"""
Simple GPS enable script - sends AT+QGPS=1 command to /dev/ttyUSB2.
This mimics the manual minicom action:
  1. sudo minicom -D /dev/ttyUSB2 -b 115200
  2. Type: AT+QGPS=1

Run: python3 utils_Test/gps_enable.py
     python3 utils_Test/gps_enable.py --port /dev/ttyUSB2 --baud 115200
     python3 utils_Test/gps_enable.py --port COM3 --baud 115200
"""

import argparse
import logging
import sys
import time
from datetime import datetime

import serial


# Configure logging
def setup_logger(log_level: str = "INFO") -> logging.Logger:
    """Setup a logger with console output"""
    logger = logging.getLogger("GPS_ENABLE")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)-8s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    class ColoredFormatter(logging.Formatter):
        """Add colors to console output"""
        COLORS = {
            'DEBUG': '\033[36m',      # Cyan
            'INFO': '\033[32m',       # Green
            'WARNING': '\033[33m',    # Yellow
            'ERROR': '\033[31m',      # Red
            'CRITICAL': '\033[35m',   # Magenta
        }
        RESET = '\033[0m'
        
        def format(self, record):
            color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            return super().format(record)
    
    console_handler.setFormatter(ColoredFormatter(
        '%(asctime)s [%(levelname)-8s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(console_handler)
    
    return logger


def send_at_command(port: str, baud_rate: int, command: str, logger: logging.Logger, 
                   read_response: bool = True, wait_time: float = 2.0) -> bool:
    """
    Send AT command to serial port and optionally read response.
    
    Args:
        port: Serial port (e.g., /dev/ttyUSB2, COM3)
        baud_rate: Baud rate (default: 115200)
        command: AT command to send (e.g., "AT+QGPS=1")
        logger: Logger instance
        read_response: Whether to read and display response
        wait_time: Time to wait after sending command (seconds)
    
    Returns:
        True if command was sent successfully, False otherwise
    """
    logger.info("=" * 60)
    logger.info(f"Sending AT command to {port} at {baud_rate} baud")
    logger.info("=" * 60)
    
    try:
        # Open serial connection
        logger.info(f"Opening serial connection to {port}...")
        ser = serial.Serial(
            port=port,
            baudrate=baud_rate,
            timeout=1,
            write_timeout=1,
            rtscts=True,
            dsrdtr=True
        )
        logger.info(f"✓ Connected to {port}")
        
        # Clear any existing data in buffer
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Prepare command (add carriage return like minicom)
        at_command = command if command.endswith('\r') else command + '\r'
        command_bytes = at_command.encode('utf-8')
        
        # Send command
        logger.info(f"Sending command: {command}")
        ser.write(command_bytes)
        logger.info(f"✓ Command sent: {command_bytes}")
        
        # Wait for response
        if wait_time > 0:
            logger.debug(f"Waiting {wait_time} seconds for GPS to initialize...")
            time.sleep(wait_time)
        
        # Read response if requested
        if read_response:
            logger.info("Reading response...")
            response_lines = []
            start_time = time.time()
            timeout = 2.0  # 2 second timeout for reading
            
            while (time.time() - start_time) < timeout:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        response_lines.append(line)
                        logger.info(f"  Response: {line}")
                else:
                    time.sleep(0.1)
            
            if response_lines:
                logger.info(f"✓ Received {len(response_lines)} response line(s)")
            else:
                logger.warning("No response received (this may be normal)")
        
        # Close connection
        ser.close()
        logger.info(f"✓ Connection closed")
        logger.info("=" * 60)
        logger.info("GPS enable command completed successfully")
        logger.info("=" * 60)
        
        return True
        
    except serial.SerialException as e:
        logger.error(f"✗ Serial error: {e}")
        logger.error("Make sure:")
        logger.error(f"  1. Port {port} exists and is accessible")
        logger.error(f"  2. You have permission to access the port (may need sudo)")
        logger.error(f"  3. No other program is using the port")
        return False
    except PermissionError as e:
        logger.error(f"✗ Permission denied: {e}")
        logger.error("Try running with sudo or add your user to the dialout group:")
        logger.error("  sudo usermod -a -G dialout $USER")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        return False


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Send AT+QGPS=1 command to enable GPS (mimics minicom action)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default: Send AT+QGPS=1 to /dev/ttyUSB2 at 115200 baud
  python gps_enable.py
  
  # Custom port and baud rate
  python gps_enable.py --port /dev/ttyUSB2 --baud 115200
  
  # Windows port
  python gps_enable.py --port COM3 --baud 115200
  
  # Custom AT command
  python gps_enable.py --command "AT+QGPS=1"
  
  # Don't read response
  python gps_enable.py --no-response
  
  # Custom wait time
  python gps_enable.py --wait 3.0
        """
    )
    
    parser.add_argument(
        '--port', '-p',
        type=str,
        default='/dev/ttyUSB2',
        help='Serial port (default: /dev/ttyUSB2)'
    )
    parser.add_argument(
        '--baud', '-b',
        type=int,
        default=115200,
        help='Baud rate (default: 115200)'
    )
    parser.add_argument(
        '--command', '-c',
        type=str,
        default='AT+QGPS=1',
        help='AT command to send (default: AT+QGPS=1)'
    )
    parser.add_argument(
        '--no-response',
        action='store_true',
        help='Do not read response from device'
    )
    parser.add_argument(
        '--wait', '-w',
        type=float,
        default=2.0,
        help='Wait time after sending command in seconds (default: 2.0)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()
    
    # Setup logger
    logger = setup_logger(args.log_level)
    
    logger.info("=" * 60)
    logger.info("GPS Enable Script")
    logger.info("(Mimics: sudo minicom -D /dev/ttyUSB2 -b 115200)")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    logger.info(f"Port: {args.port}")
    logger.info(f"Baud Rate: {args.baud}")
    logger.info(f"Command: {args.command}")
    logger.info("")
    
    # Send AT command
    success = send_at_command(
        port=args.port,
        baud_rate=args.baud,
        command=args.command,
        logger=logger,
        read_response=not args.no_response,
        wait_time=args.wait
    )
    
    if success:
        logger.info("")
        logger.info("✓ GPS enable command sent successfully!")
        logger.info("GPS should now be enabled and ready to use.")
        sys.exit(0)
    else:
        logger.error("")
        logger.error("✗ Failed to send GPS enable command")
        logger.error("Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()

