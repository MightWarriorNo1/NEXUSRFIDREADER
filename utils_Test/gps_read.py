"""
Simple GPS port finder and data reader.
This script only finds GPS port and reads data - no GPS enabling or pre-configuration.

Run: python3 utils_Test/gps_read.py --auto-detect
     python3 utils_Test/gps_read.py --port COM3 --baud 115200
     python3 utils_Test/gps_read.py --port /dev/ttyUSB0 --baud 9600
"""

import argparse
import logging
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

import serial
import serial.tools.list_ports
import pynmea2


# Configure detailed logging
def setup_logger(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup a detailed logger with console and optional file output"""
    logger = logging.getLogger("GPS_READ")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()
    
    # Create formatter with detailed information
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)-8s] [%(name)s] %(message)s [%(filename)s:%(lineno)d]',
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
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    
    return logger


def list_serial_ports(logger: logging.Logger) -> list:
    """List all available serial ports"""
    ports = serial.tools.list_ports.comports()
    port_list = []
    logger.info("=" * 60)
    logger.info("Available Serial Ports:")
    logger.info("=" * 60)
    for port in ports:
        port_info = {
            'device': port.device,
            'description': port.description,
            'manufacturer': port.manufacturer,
            'hwid': port.hwid
        }
        port_list.append(port_info)
        logger.info(f"  Port: {port.device}")
        logger.info(f"    Description: {port.description}")
        logger.info(f"    Manufacturer: {port.manufacturer or 'N/A'}")
        logger.info(f"    HWID: {port.hwid}")
        logger.info("")
    return port_list


def find_gps_port(baud_rate: int, logger: logging.Logger) -> Optional[str]:
    """
    Find GPS port by scanning all ports at given baud rate.
    Tries 5 attempts per port to catch GPS data.
    """
    serial_ports = [port.device for port in serial.tools.list_ports.comports()]
    logger.debug(f"Scanning ports at {baud_rate} baud: {serial_ports}")
    
    # Try each port multiple times to ensure we catch GPS data
    for port in serial_ports:
        logger.info(f"Testing port: {port}")
        try:
            with serial.Serial(port, baudrate=baud_rate, timeout=1, rtscts=True, dsrdtr=True) as ser:
                # Try multiple reads to catch GPS data (5 attempts)
                for attempt in range(5):
                    buffer = ser.in_waiting
                    if buffer < 80:
                        time.sleep(0.2)  # Wait a bit longer for data
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        logger.debug(f"  Attempt {attempt + 1}: {line[:60]}...")
                        if line.startswith('$G'):
                            logger.info(f"✓ GPS found on port: {port}")
                            return port
                logger.debug(f"  No GPS data found on {port} after 5 attempts")
        except (OSError, serial.SerialException) as e:
            logger.debug(f"  Port {port} error: {e}")
            pass
    
    logger.warning("No GPS port found")
    return None


def auto_detect_gps_port(baud_rates: list, logger: logging.Logger) -> Optional[Tuple[str, int]]:
    """
    Auto-detect GPS port by trying different baud rates.
    No GPS enabling or pre-configuration - just scan and find.
    """
    logger.info("=" * 60)
    logger.info("Auto-detecting GPS port (scanning only, no enabling)...")
    logger.info("=" * 60)
    
    # Try each baud rate
    for baud_rate in baud_rates:
        logger.info(f"Trying baud rate: {baud_rate}")
        port = find_gps_port(baud_rate, logger)
        if port:
            logger.info(f"✓ GPS found on {port} at {baud_rate} baud")
            return port, baud_rate
    
    logger.warning("No GPS device detected on any port at any baud rate")
    return None


def connect_gps(port: str, baud_rate: int, logger: logging.Logger) -> Optional[serial.Serial]:
    """Connect to GPS device"""
    logger.info("=" * 60)
    logger.info(f"Connecting to GPS on {port} at {baud_rate} baud...")
    logger.info("=" * 60)
    
    try:
        ser = serial.Serial(
            port=port,
            baudrate=baud_rate,
            timeout=1,
            write_timeout=1,
            rtscts=True,
            dsrdtr=True
        )
        logger.info(f"✓ Successfully connected to {port}")
        logger.info(f"  Port settings: {ser.get_settings()}")
        return ser
    except serial.SerialException as e:
        logger.error(f"✗ Failed to connect: {e}")
        return None
    except Exception as e:
        logger.error(f"✗ Unexpected error during connection: {e}")
        return None


def parse_nmea_sentence(line: str, logger: logging.Logger) -> Optional[Dict]:
    """Parse NMEA sentence and return structured data"""
    if not line.startswith('$'):
        return None
    
    try:
        msg = pynmea2.parse(line)
        data = {
            'sentence_type': msg.sentence_type,
            'raw': line
        }
        
        # Extract all fields
        for field in msg.fields:
            label, attr = field[:2]
            try:
                value = getattr(msg, attr)
                data[attr] = value
            except AttributeError:
                pass
        
        return data
    except pynmea2.ParseError as e:
        logger.debug(f"Parse error for '{line[:50]}...': {e}")
        return None
    except Exception as e:
        logger.debug(f"Unexpected error parsing '{line[:50]}...': {e}")
        return None


def format_gps_data(data: Dict, logger: logging.Logger) -> str:
    """Format GPS data for display"""
    if not data:
        return "No data"
    
    sentence_type = data.get('sentence_type', 'UNKNOWN')
    output = [f"\n[{sentence_type}]"]
    
    # Format based on sentence type
    if sentence_type == 'RMC':
        # Recommended Minimum Course
        lat = data.get('lat', 'N/A')
        lat_dir = data.get('lat_dir', '')
        lon = data.get('lon', 'N/A')
        lon_dir = data.get('lon_dir', '')
        speed = data.get('spd_over_grnd', 'N/A')
        course = data.get('true_course', 'N/A')
        timestamp = data.get('timestamp', 'N/A')
        datestamp = data.get('datestamp', 'N/A')
        status = data.get('status', 'N/A')
        
        output.append(f"  Status: {status}")
        output.append(f"  Position: {lat}° {lat_dir}, {lon}° {lon_dir}")
        output.append(f"  Speed: {speed} knots ({speed * 1.15078 if isinstance(speed, (int, float)) else 'N/A'} mph)")
        output.append(f"  Course: {course}°")
        output.append(f"  Time: {timestamp} | Date: {datestamp}")
        
    elif sentence_type == 'GGA':
        # Global Positioning System Fix Data
        lat = data.get('lat', 'N/A')
        lat_dir = data.get('lat_dir', '')
        lon = data.get('lon', 'N/A')
        lon_dir = data.get('lon_dir', '')
        altitude = data.get('altitude', 'N/A')
        num_sats = data.get('num_sats', 'N/A')
        hdop = data.get('horizontal_dil', 'N/A')
        fix_quality = data.get('gps_qual', 'N/A')
        
        output.append(f"  Position: {lat}° {lat_dir}, {lon}° {lon_dir}")
        output.append(f"  Altitude: {altitude} {data.get('altitude_units', 'm')}")
        output.append(f"  Satellites: {num_sats}")
        output.append(f"  HDOP: {hdop}")
        output.append(f"  Fix Quality: {fix_quality}")
        
    elif sentence_type == 'GSV':
        # Satellites in view
        num_sentences = data.get('num_sentences', 'N/A')
        sentence_num = data.get('sentence_num', 'N/A')
        num_sats_in_view = data.get('num_sv_in_view', 'N/A')
        output.append(f"  Sentences: {sentence_num}/{num_sentences}")
        output.append(f"  Satellites in view: {num_sats_in_view}")
        
    elif sentence_type == 'GSA':
        # GPS DOP and active satellites
        mode = data.get('mode', 'N/A')
        fix_type = data.get('mode_fix_type', 'N/A')
        pdop = data.get('pdop', 'N/A')
        hdop = data.get('hdop', 'N/A')
        vdop = data.get('vdop', 'N/A')
        output.append(f"  Mode: {mode} | Fix Type: {fix_type}")
        output.append(f"  PDOP: {pdop} | HDOP: {hdop} | VDOP: {vdop}")
        
    else:
        # Generic output for other sentence types
        for key, value in data.items():
            if key not in ['sentence_type', 'raw']:
                output.append(f"  {key}: {value}")
    
    return "\n".join(output)


def read_gps_data(ser: serial.Serial, logger: logging.Logger, 
                  show_raw: bool = False, show_all_sentences: bool = False,
                  stats: Dict = None) -> None:
    """Read and process GPS data continuously"""
    logger.info("=" * 60)
    logger.info("Reading GPS data... (Press Ctrl+C to stop)")
    logger.info("=" * 60)
    
    last_position_time = None
    position_count = 0
    
    try:
        while True:
            try:
                # Wait for data
                buffer = ser.in_waiting
                if buffer < 80:
                    time.sleep(0.2)
                
                # Read line
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if not line:
                    continue
                
                # Log raw sentence if requested
                if show_raw:
                    logger.debug(f"RAW: {line}")
                
                # Parse NMEA sentence
                data = parse_nmea_sentence(line, logger)
                
                if data:
                    sentence_type = data.get('sentence_type', 'UNKNOWN')
                    
                    # Track statistics
                    if stats is not None:
                        stats['total_sentences'] = stats.get('total_sentences', 0) + 1
                        stats[sentence_type] = stats.get(sentence_type, 0) + 1
                    
                    # Show all sentences or only important ones
                    if show_all_sentences or sentence_type in ['RMC', 'GGA', 'GSA']:
                        formatted = format_gps_data(data, logger)
                        logger.info(formatted)
                        
                        # Track position updates
                        if sentence_type in ['RMC', 'GGA']:
                            position_count += 1
                            current_time = time.time()
                            if last_position_time:
                                time_diff = current_time - last_position_time
                                logger.debug(f"Position update #{position_count} (interval: {time_diff:.2f}s)")
                            last_position_time = current_time
                    else:
                        logger.debug(f"Received {sentence_type} sentence (not displayed)")
                
            except serial.SerialException as e:
                logger.error(f"Serial error: {e}")
                logger.warning("Attempting to reconnect...")
                time.sleep(1)
                break
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error(f"Unexpected error: {e}", exc_info=True)
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("Stopping GPS reader...")
        logger.info("=" * 60)


def print_statistics(stats: Dict, logger: logging.Logger):
    """Print reading statistics"""
    if not stats:
        return
    
    logger.info("=" * 60)
    logger.info("Reading Statistics:")
    logger.info("=" * 60)
    logger.info(f"Total sentences received: {stats.get('total_sentences', 0)}")
    
    sentence_types = {k: v for k, v in stats.items() if k != 'total_sentences'}
    if sentence_types:
        logger.info("Sentence types:")
        for stype, count in sorted(sentence_types.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {stype}: {count}")
    logger.info("=" * 60)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Simple GPS Port Finder and Data Reader (No GPS Enabling)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect GPS port
  python gps_read.py --auto-detect
  
  # Connect to specific port
  python gps_read.py --port COM3 --baud 115200
  
  # Linux port with custom baud rate
  python gps_read.py --port /dev/ttyUSB0 --baud 9600
  
  # Show all NMEA sentences and raw data
  python gps_read.py --port COM3 --show-all --show-raw
  
  # Save logs to file
  python gps_read.py --port COM3 --log-file gps_read.log
        """
    )
    
    parser.add_argument(
        '--port', '-p',
        type=str,
        help='Serial port (e.g., COM3, /dev/ttyUSB0)'
    )
    parser.add_argument(
        '--baud', '-b',
        type=int,
        default=115200,
        help='Baud rate (default: 115200)'
    )
    parser.add_argument(
        '--auto-detect', '-a',
        action='store_true',
        help='Auto-detect GPS port and baud rate (scanning only, no enabling)'
    )
    parser.add_argument(
        '--list-ports', '-l',
        action='store_true',
        help='List all available serial ports and exit'
    )
    parser.add_argument(
        '--show-raw',
        action='store_true',
        help='Show raw NMEA sentences'
    )
    parser.add_argument(
        '--show-all',
        action='store_true',
        help='Show all NMEA sentence types (not just RMC/GGA/GSA)'
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
    parser.add_argument(
        '--baud-rates',
        nargs='+',
        type=int,
        default=[115200, 9600, 4800, 38400],
        help='Baud rates to try for auto-detection (default: 115200 9600 4800 38400)'
    )
    
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()
    
    # Setup logger
    logger = setup_logger(args.log_level, args.log_file)
    
    logger.info("=" * 60)
    logger.info("GPS Port Finder and Data Reader")
    logger.info("(No GPS enabling - scanning and reading only)")
    logger.info("=" * 60)
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # List ports if requested
    if args.list_ports:
        list_serial_ports(logger)
        return
    
    # Determine port and baud rate
    port = None
    baud_rate = args.baud
    
    if args.auto_detect:
        result = auto_detect_gps_port(args.baud_rates, logger)
        if result:
            port, baud_rate = result
        else:
            logger.error("Failed to auto-detect GPS. Use --list-ports to see available ports.")
            sys.exit(1)
    elif args.port:
        port = args.port
    else:
        logger.error("Either --port or --auto-detect must be specified. Use --list-ports to see available ports.")
        sys.exit(1)
    
    # Connect to GPS
    ser = connect_gps(port, baud_rate, logger)
    if not ser:
        logger.error("Failed to connect to GPS device")
        sys.exit(1)
    
    # Statistics tracking
    stats = {}
    
    # Setup signal handler for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\nReceived interrupt signal, shutting down...")
        if ser and ser.is_open:
            ser.close()
        print_statistics(stats, logger)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Read GPS data
        read_gps_data(
            ser,
            logger,
            show_raw=args.show_raw,
            show_all_sentences=args.show_all,
            stats=stats
        )
    finally:
        # Cleanup
        if ser and ser.is_open:
            logger.info("Closing serial connection...")
            ser.close()
        
        # Print statistics
        print_statistics(stats, logger)
        
        logger.info(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)


if __name__ == "__main__":
    main()

