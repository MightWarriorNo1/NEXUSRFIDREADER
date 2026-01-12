#!/usr/bin/env python3
"""
LED Status Control Test for reComputer R1100

This script tests LED status control based on device status:
- Green LED: All items nominal (RFID Connected, GPS Connected, Internet Connected)
- Yellow LED: An item is not nominal (one or more disconnected but not hardware failure)
- Red LED: Hardware failure

The USER LED on reComputer R1100 has separate red, green, and blue LEDs that can be controlled
via /sys/class/leds/led-red, /sys/class/leds/led-green, and /sys/class/leds/led-blue

Run: python3 utils_Test/led_status_test.py
     python3 utils_Test/led_status_test.py --interval 5
     python3 utils_Test/led_status_test.py --once
"""

import argparse
import logging
import os
import platform
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ping3 import ping
except ImportError:
    print("Warning: ping3 not available, internet check will be limited", file=sys.stderr)
    ping = None

try:
    import serial
    import serial.tools.list_ports
    import pynmea2
except ImportError:
    print("Warning: pyserial/pynmea2 not available, GPS check will be limited", file=sys.stderr)
    serial = None
    pynmea2 = None

try:
    from sllurp.llrp import LLRPReaderClient, LLRPReaderConfig
except ImportError:
    print("Warning: sllurp not available, RFID check will be limited", file=sys.stderr)
    LLRPReaderClient = None


# Configure logging
def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup a logger with console and optional file output"""
    logger = logging.getLogger("LED_STATUS_TEST")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)-8s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    
    return logger


class LEDController:
    """Controller for USER LED on reComputer R1100"""
    
    LED_PATHS = {
        'red': '/sys/class/leds/led-red/brightness',
        'green': '/sys/class/leds/led-green/brightness',
        'blue': '/sys/class/leds/led-blue/brightness'
    }
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.is_available = self._check_availability()
        
    def _check_availability(self) -> bool:
        """Check if LED control is available (Linux only)"""
        if platform.system() != "Linux":
            self.logger.warning("LED control is only available on Linux systems")
            return False
        
        # Check if LED paths exist
        for color, path in self.LED_PATHS.items():
            if not os.path.exists(path):
                self.logger.warning(f"LED path not found: {path}")
                return False
        
        self.logger.info("LED control paths found")
        return True
    
    def _write_led(self, color: str, value: int) -> bool:
        """Write value to LED brightness file"""
        if not self.is_available:
            return False
        
        if color not in self.LED_PATHS:
            self.logger.error(f"Invalid LED color: {color}")
            return False
        
        try:
            path = self.LED_PATHS[color]
            with open(path, 'w') as f:
                f.write(str(value))
            return True
        except PermissionError:
            self.logger.error(f"Permission denied: Need sudo to control LED. Try: sudo python3 {sys.argv[0]}")
            return False
        except Exception as e:
            self.logger.error(f"Failed to write LED {color}: {e}")
            return False
    
    def set_red(self, on: bool = True):
        """Set red LED on/off"""
        return self._write_led('red', 1 if on else 0)
    
    def set_green(self, on: bool = True):
        """Set green LED on/off"""
        return self._write_led('green', 1 if on else 0)
    
    def set_blue(self, on: bool = True):
        """Set blue LED on/off"""
        return self._write_led('blue', 1 if on else 0)
    
    def set_status(self, status: str):
        """
        Set LED status:
        - 'green': All nominal (green LED on)
        - 'yellow': Warning (green + red LEDs on)
        - 'red': Hardware failure (red LED on)
        - 'off': All LEDs off
        """
        if not self.is_available:
            self.logger.debug(f"LED status would be: {status} (LED control not available)")
            return False
        
        # Turn off all LEDs first
        self.set_red(False)
        self.set_green(False)
        self.set_blue(False)
        
        if status == 'green':
            self.set_green(True)
            self.logger.info("LED set to GREEN (all nominal)")
        elif status == 'yellow':
            self.set_green(True)
            self.set_red(True)
            self.logger.info("LED set to YELLOW (warning - item not nominal)")
        elif status == 'red':
            self.set_red(True)
            self.logger.info("LED set to RED (hardware failure)")
        elif status == 'off':
            self.logger.info("LED set to OFF")
        else:
            self.logger.warning(f"Unknown status: {status}")
            return False
        
        return True


class StatusChecker:
    """Check status of RFID, GPS, and Internet"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.rfid_host = None
        self.gps_port = None
        self.gps_baud = None
        
    def check_internet(self) -> Tuple[bool, str]:
        """Check internet connectivity"""
        if ping is None:
            return False, "ping3 not available"
        
        try:
            response_time = ping("8.8.8.8", timeout=3)
            if response_time is not None:
                return True, f"Connected ({response_time*1000:.0f}ms)"
            else:
                return False, "Disconnected"
        except Exception as e:
            self.logger.debug(f"Internet check error: {e}")
            return False, f"Error: {str(e)}"
    
    def check_gps(self) -> Tuple[bool, str]:
        """Check GPS connectivity"""
        if serial is None or pynmea2 is None:
            return False, "pyserial/pynmea2 not available"
        
        # Try to find GPS port if not already known
        if not self.gps_port:
            self.gps_port, self.gps_baud = self._find_gps_port()
        
        if not self.gps_port:
            return False, "GPS port not found"
        
        try:
            with serial.Serial(self.gps_port, baudrate=self.gps_baud or 115200, 
                             timeout=1, rtscts=True, dsrdtr=True) as ser:
                # Try to read a GPS sentence
                buffer = ser.in_waiting
                if buffer < 80:
                    time.sleep(0.2)
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith('$G'):
                    return True, f"Connected ({self.gps_port})"
                else:
                    return False, f"No GPS data ({self.gps_port})"
        except serial.SerialException as e:
            return False, f"Serial error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def _find_gps_port(self) -> Tuple[Optional[str], Optional[int]]:
        """Find GPS port by scanning serial ports"""
        if serial is None:
            return None, None
        
        ports = serial.tools.list_ports.comports()
        baud_rates = [115200, 9600, 4800, 38400]
        
        for port in ports:
            for baud in baud_rates:
                try:
                    with serial.Serial(port.device, baudrate=baud, timeout=1, 
                                     rtscts=True, dsrdtr=True) as ser:
                        for _ in range(3):  # Try 3 times
                            buffer = ser.in_waiting
                            if buffer < 80:
                                time.sleep(0.2)
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if line.startswith('$G'):
                                return port.device, baud
                except:
                    continue
        
        return None, None
    
    def check_rfid(self) -> Tuple[bool, str]:
        """Check RFID reader connectivity"""
        if LLRPReaderClient is None:
            return False, "sllurp not available"
        
        try:
            # Try to import settings
            from settings import RFID_CONFIG
            
            host = RFID_CONFIG.get('host', '127.0.0.1')
            port = RFID_CONFIG.get('port', 5084)
            
            config = LLRPReaderConfig()
            config.antennas = [1]
            config.tx_power = 0
            
            client = LLRPReaderClient(host, port, config)
            # Try to connect (this may take a moment)
            client.connect()
            
            if client.is_connected():
                client.disconnect()
                return True, f"Connected ({host}:{port})"
            else:
                return False, "Not connected"
        except ConnectionError as e:
            return False, f"Connection error: {str(e)}"
        except Exception as e:
            self.logger.debug(f"RFID check error: {e}")
            # Extract meaningful error message
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                return False, "Connection timeout"
            elif "refused" in error_msg.lower() or "unreachable" in error_msg.lower():
                return False, "Host unreachable"
            else:
                return False, f"Error: {error_msg[:50]}"
    
    def check_all_status(self) -> Dict[str, Tuple[bool, str]]:
        """Check all device statuses"""
        status = {
            'rfid': self.check_rfid(),
            'gps': self.check_gps(),
            'internet': self.check_internet()
        }
        return status


def determine_led_status(status: Dict[str, Tuple[bool, str]], logger: logging.Logger) -> str:
    """
    Determine LED status based on device status:
    - 'green': All items nominal (all connected)
    - 'yellow': An item is not nominal (one or more disconnected but not hardware failure)
    - 'red': Hardware failure
    """
    rfid_ok, rfid_msg = status['rfid']
    gps_ok, gps_msg = status['gps']
    internet_ok, internet_msg = status['internet']
    
    logger.info(f"Status check - RFID: {rfid_msg}, GPS: {gps_msg}, Internet: {internet_msg}")
    
    # Check for hardware failure (all disconnected might indicate hardware issue)
    # For now, we'll consider it a warning (yellow) if items are disconnected
    # Red would be for actual hardware failures detected
    
    all_connected = rfid_ok and gps_ok and internet_ok
    
    if all_connected:
        return 'green'
    else:
        # One or more items not nominal - use yellow
        # TODO: Add hardware failure detection logic here
        # For example: if RFID reader hardware error detected, use 'red'
        return 'yellow'


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="LED Status Control Test for reComputer R1100",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once and exit
  sudo python3 led_status_test.py --once
  
  # Run continuously with 5 second interval
  sudo python3 led_status_test.py --interval 5
  
  # Run with verbose logging
  sudo python3 led_status_test.py --interval 5 --log-level DEBUG
        """
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=float,
        default=10.0,
        help='Check interval in seconds (default: 10.0)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (default: run continuously)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        help='Save logs to file'
    )
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger(args.log_level, args.log_file)
    
    logger.info("=" * 60)
    logger.info("LED Status Control Test for reComputer R1100")
    logger.info("=" * 60)
    
    # Initialize LED controller and status checker
    led_controller = LEDController(logger)
    status_checker = StatusChecker(logger)
    
    if not led_controller.is_available:
        logger.warning("LED control not available. Continuing with status checks only...")
    
    # Setup signal handler for graceful shutdown
    running = True
    
    def signal_handler(sig, frame):
        nonlocal running
        logger.info("\nReceived interrupt signal, shutting down...")
        running = False
        if led_controller.is_available:
            led_controller.set_status('off')
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        while running:
            # Check all statuses
            status = status_checker.check_all_status()
            
            # Determine LED status
            led_status = determine_led_status(status, logger)
            
            # Set LED
            if led_controller.is_available:
                led_controller.set_status(led_status)
            else:
                logger.info(f"LED status would be: {led_status.upper()}")
            
            # Print summary
            rfid_ok, rfid_msg = status['rfid']
            gps_ok, gps_msg = status['gps']
            internet_ok, internet_msg = status['internet']
            
            logger.info("=" * 60)
            logger.info("Status Summary:")
            logger.info(f"  RFID:    {'✓' if rfid_ok else '✗'} {rfid_msg}")
            logger.info(f"  GPS:     {'✓' if gps_ok else '✗'} {gps_msg}")
            logger.info(f"  Internet: {'✓' if internet_ok else '✗'} {internet_msg}")
            logger.info(f"  LED Status: {led_status.upper()}")
            logger.info("=" * 60)
            
            if args.once:
                break
            
            # Wait for next check
            time.sleep(args.interval)
    
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
    finally:
        if led_controller.is_available:
            logger.info("Turning off LED...")
            led_controller.set_status('off')
        logger.info("Test completed")


if __name__ == "__main__":
    main()
