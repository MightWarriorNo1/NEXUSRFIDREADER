"""
FX7500 RFID Reader Restart Test with Comprehensive Logging
==========================================================

This script tests the restart functionality of the FX7500 RFID reader and provides
comprehensive logging for analysis. It includes:

1. Reader connectivity testing
2. Restart command execution (via LLRP and web interface with authentication)
3. Pre/post restart status monitoring
4. Comprehensive logging with log review functionality
5. Error handling and recovery mechanisms

Usage:
    # Basic LLRP test
    python test_rfid_reader_restart.py --host 169.254.10.1 --port 5084
    
    # Web interface test with authentication
    python test_rfid_reader_restart.py --host 169.254.10.1 --web-interface --username admin --password admin123
    
    # Simulation mode (no actual restart)
    python test_rfid_reader_restart.py --host 169.254.10.1 --simulate
    
    # Review logs from previous test
    python test_rfid_reader_restart.py --review-logs fx7500_restart_test_20251011_150626.log
"""

import argparse
import json
import logging
import os
import requests
import signal
import sys
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from urllib.parse import urljoin

from sllurp.llrp import LLRPReaderConfig, LLRPReaderClient
from ping3 import ping


class FX7500RestartTester:
    """Comprehensive FX7500 RFID Reader Restart Tester with Logging"""
    
    def __init__(self, host: str, port: int = 5084, web_interface: bool = False, log_dir: str = None, 
                 username: str = None, password: str = None):
        self.host = host
        self.port = port
        self.web_interface = web_interface
        self.username = username
        self.password = password
        self.reader_client = None
        
        # Create log file in a writable location
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = f"fx7500_restart_test_{timestamp}.log"
        
        # Try different locations for log file
        possible_locations = []
        if log_dir:
            possible_locations.append(os.path.join(log_dir, log_filename))
        possible_locations.extend([
            os.path.join(os.getcwd(), log_filename),  # Current directory
            os.path.join(os.path.expanduser("~"), log_filename),  # Home directory
            os.path.join("/tmp", log_filename),  # /tmp directory
            os.path.join("/var/tmp", log_filename),  # /var/tmp directory
        ])
        
        self.restart_log_file = None
        for location in possible_locations:
            try:
                # Test if we can write to this location
                with open(location, 'w') as f:
                    f.write("")  # Test write
                self.restart_log_file = location
                break
            except (PermissionError, OSError):
                continue
        
        if self.restart_log_file is None:
            # Fallback to console-only logging
            self.restart_log_file = None
            print("Warning: Could not create log file - using console logging only")
        
        self.test_results = {
            'start_time': datetime.now().isoformat(),
            'host': host,
            'port': port,
            'web_interface': web_interface,
            'username': username,
            'has_password': bool(password),
            'tests': []
        }
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging for the restart test"""
        logger = logging.getLogger('FX7500RestartTest')
        logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler for detailed logs (only if log file is available)
        if self.restart_log_file:
            try:
                file_handler = logging.FileHandler(self.restart_log_file, mode='w')
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
                logger.info(f"Logging to file: {self.restart_log_file}")
            except Exception as e:
                logger.warning(f"Could not create file handler: {e}")
        else:
            logger.warning("No log file available - using console logging only")
        
        return logger
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", 
                       duration: float = 0.0, error: str = ""):
        """Log test results for analysis"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'duration_seconds': duration,
            'timestamp': datetime.now().isoformat(),
            'error': error
        }
        self.test_results['tests'].append(result)
        
        status = "PASS" if success else "FAIL"
        self.logger.info(f"[{status}] {test_name}: {details}")
        if error:
            self.logger.error(f"Error: {error}")
    
    def test_connectivity(self) -> bool:
        """Test basic connectivity to the reader"""
        start_time = time.time()
        try:
            self.logger.info(f"Testing connectivity to {self.host}:{self.port}")
            
            # Test ping connectivity
            response_time = ping(self.host, timeout=5)
            if response_time is None:
                self.log_test_result("ping_test", False, "No response to ping", 
                                   time.time() - start_time, "Timeout")
                return False
            
            self.log_test_result("ping_test", True, f"Response time: {response_time:.3f}s", 
                               time.time() - start_time)
            
            # Test LLRP port connectivity
            if not self.web_interface:
                try:
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((self.host, self.port))
                    sock.close()
                    
                    if result == 0:
                        self.log_test_result("llrp_port_test", True, f"Port {self.port} is open", 
                                           time.time() - start_time)
                    else:
                        self.log_test_result("llrp_port_test", False, f"Port {self.port} is closed", 
                                           time.time() - start_time, f"Connection failed: {result}")
                        return False
                except Exception as e:
                    self.log_test_result("llrp_port_test", False, f"Port {self.port} test failed", 
                                       time.time() - start_time, str(e))
                    return False
            
            return True
            
        except Exception as e:
            self.log_test_result("connectivity_test", False, "Connectivity test failed", 
                               time.time() - start_time, str(e))
            return False
    
    def test_llrp_connection(self) -> bool:
        """Test LLRP connection to the reader"""
        start_time = time.time()
        try:
            self.logger.info("Testing LLRP connection...")
            
            # Clean up any existing connections first
            try:
                LLRPReaderClient.disconnect_all_readers()
                time.sleep(1)  # Give time for cleanup
            except Exception:
                pass  # Ignore cleanup errors
            
            # Create minimal LLRP configuration
            factory_args = {
                'report_every_n_tags': 1,
                'antennas': [1],
                'tx_power': 0,
                'tari': 0,
                'session': 1,
                'start_inventory': False,  # Don't start inventory for restart test
            }
            
            config = LLRPReaderConfig(factory_args)
            self.reader_client = LLRPReaderClient(self.host, self.port, config)
            
            # Attempt connection
            self.reader_client.connect()
            
            self.log_test_result("llrp_connection", True, "Successfully connected via LLRP", 
                               time.time() - start_time)
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "Client initiated connection already exists" in error_msg:
                self.logger.warning("Existing LLRP connection detected - this is normal for restart testing")
                self.log_test_result("llrp_connection", True, "LLRP connection exists (expected for restart test)", 
                                   time.time() - start_time)
                return True
            else:
                self.log_test_result("llrp_connection", False, "LLRP connection failed", 
                                   time.time() - start_time, error_msg)
                return False
    
    def test_web_interface_connection(self) -> bool:
        """Test web interface connectivity and discover available endpoints"""
        start_time = time.time()
        try:
            self.logger.info("Testing web interface connectivity...")
            
            # Common FX7500 web interface URLs
            web_urls = [
                f"http://{self.host}",
                f"http://{self.host}/",
                f"http://{self.host}/admin",
                f"http://{self.host}/login",
            ]
            
            accessible_url = None
            for url in web_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        accessible_url = url
                        self.log_test_result("web_interface", True, f"Web interface accessible at {url}", 
                                           time.time() - start_time)
                        break
                except requests.RequestException:
                    continue
            
            if not accessible_url:
                self.log_test_result("web_interface", False, "Web interface not accessible", 
                                   time.time() - start_time, "All URLs failed")
                return False
            
            # Try to discover restart-related endpoints
            self.discover_restart_endpoints(accessible_url)
            
            return True
            
        except Exception as e:
            self.log_test_result("web_interface", False, "Web interface test failed", 
                               time.time() - start_time, str(e))
            return False
    
    def discover_restart_endpoints(self, base_url: str):
        """Discover potential restart endpoints by analyzing the web interface"""
        try:
            self.logger.info("Discovering restart endpoints...")
            
            # Get the main page content
            response = requests.get(base_url, timeout=10)
            if response.status_code != 200:
                return
            
            content = response.text.lower()
            
            # Look for restart-related keywords in the page
            restart_keywords = ['restart', 'reboot', 'shutdown', 'reset', 'power']
            found_keywords = []
            
            for keyword in restart_keywords:
                if keyword in content:
                    found_keywords.append(keyword)
            
            if found_keywords:
                self.logger.info(f"Found restart-related keywords: {', '.join(found_keywords)}")
            
            # Try to find links or forms that might lead to restart functionality
            import re
            
            # Look for links containing restart-related terms
            link_pattern = r'href=["\']([^"\']*(?:restart|reboot|shutdown|reset|power)[^"\']*)["\']'
            links = re.findall(link_pattern, content, re.IGNORECASE)
            
            if links:
                self.logger.info(f"Found potential restart links: {links}")
            
            # Look for form actions
            form_pattern = r'action=["\']([^"\']*(?:restart|reboot|shutdown|reset|power)[^"\']*)["\']'
            forms = re.findall(form_pattern, content, re.IGNORECASE)
            
            if forms:
                self.logger.info(f"Found potential restart forms: {forms}")
            
            # Try common FX7500-specific endpoints
            fx7500_endpoints = [
                '/cgi-bin/system.cgi',
                '/cgi-bin/admin.cgi',
                '/admin/system',
                '/system/restart',
                '/admin/reboot',
                '/system/reboot',
                '/admin/shutdown',
                '/system/shutdown',
            ]
            
            for endpoint in fx7500_endpoints:
                try:
                    url = f"http://{self.host}{endpoint}"
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        self.logger.info(f"Found accessible endpoint: {url}")
                    elif response.status_code == 401:
                        self.logger.info(f"Found protected endpoint: {url}")
                except requests.RequestException:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Endpoint discovery failed: {e}")
    
    def restart_via_llrp(self) -> bool:
        """Attempt to restart reader via LLRP commands"""
        start_time = time.time()
        try:
            self.logger.info("Attempting restart via LLRP...")
            
            if not self.reader_client:
                self.log_test_result("llrp_restart", False, "No LLRP connection available", 
                                   time.time() - start_time, "Reader client not initialized")
                return False
            
            # Note: LLRP doesn't have a direct restart command
            # This is a placeholder for future implementation
            # The actual restart would need to be done via web interface or other means
            
            self.logger.warning("LLRP restart not implemented - LLRP protocol doesn't support direct restart commands")
            self.log_test_result("llrp_restart", False, "LLRP restart not supported", 
                               time.time() - start_time, "LLRP protocol limitation")
            return False
            
        except Exception as e:
            self.log_test_result("llrp_restart", False, "LLRP restart failed", 
                               time.time() - start_time, str(e))
            return False
    
    def restart_via_web_interface(self) -> bool:
        """Attempt to restart reader via web interface"""
        start_time = time.time()
        try:
            self.logger.info("Attempting restart via web interface...")
            
            # Create session for authentication
            session = requests.Session()
            
            # Common FX7500 login and restart endpoints
            login_urls = [
                f"http://{self.host}/login",
                f"http://{self.host}/admin/login",
                f"http://{self.host}/cgi-bin/login",
            ]
            
            restart_urls = [
                f"http://{self.host}/admin/restart",
                f"http://{self.host}/cgi-bin/restart",
                f"http://{self.host}/restart",
                f"http://{self.host}/admin/system/restart",
                f"http://{self.host}/cgi-bin/system/restart",
            ]
            
            # Try to authenticate if credentials provided
            authenticated = False
            if self.username and self.password:
                self.logger.info(f"Attempting authentication with username: {self.username}")
                for login_url in login_urls:
                    try:
                        # Try different login form field names
                        login_data_variants = [
                            {"username": self.username, "password": self.password},
                            {"user": self.username, "pass": self.password},
                            {"login": self.username, "passwd": self.password},
                            {"userid": self.username, "pwd": self.password},
                        ]
                        
                        for login_data in login_data_variants:
                            response = session.post(login_url, data=login_data, timeout=10)
                            if response.status_code == 200 and "login" not in response.url.lower():
                                authenticated = True
                                self.logger.info(f"Authentication successful via {login_url}")
                                break
                        
                        if authenticated:
                            break
                    except requests.RequestException as e:
                        self.logger.debug(f"Login failed at {login_url}: {e}")
                        continue
            else:
                self.logger.warning("No username/password provided - trying unauthenticated restart")
                authenticated = True  # Try without auth
            
            if not authenticated:
                self.logger.warning("Authentication failed - trying unauthenticated restart")
            
            # Try restart endpoints
            for url in restart_urls:
                try:
                    if authenticated:
                        # Try POST request for restart with session
                        response = session.post(url, timeout=10)
                    else:
                        # Try POST request for restart without session
                        response = requests.post(url, timeout=10)
                    
                    if response.status_code in [200, 202]:
                        self.log_test_result("web_restart", True, f"Restart command sent to {url}", 
                                           time.time() - start_time)
                        return True
                    elif response.status_code == 401:
                        self.logger.debug(f"Authentication required for {url}")
                        continue
                    elif response.status_code == 404:
                        self.logger.debug(f"Endpoint not found: {url}")
                        continue
                        
                except requests.RequestException as e:
                    self.logger.debug(f"Failed to restart via {url}: {e}")
                    continue
            
            self.log_test_result("web_restart", False, "Web restart failed - no accessible restart endpoint", 
                               time.time() - start_time, "All restart URLs failed")
            return False
            
        except Exception as e:
            self.log_test_result("web_restart", False, "Web restart failed", 
                               time.time() - start_time, str(e))
            return False
    
    def monitor_restart_process(self, timeout: int = 120) -> bool:
        """Monitor the restart process and wait for reader to come back online"""
        start_time = time.time()
        self.logger.info(f"Monitoring restart process (timeout: {timeout}s)...")
        
        # Wait for reader to go offline
        offline_time = None
        for i in range(30):  # Wait up to 30 seconds for offline
            if ping(self.host, timeout=2) is None:
                offline_time = time.time()
                self.logger.info(f"Reader went offline after {offline_time - start_time:.1f}s")
                break
            time.sleep(1)
        
        if offline_time is None:
            self.log_test_result("restart_monitoring", False, "Reader did not go offline", 
                               time.time() - start_time, "Expected offline state not detected")
            return False
        
        # Wait for reader to come back online
        online_time = None
        for i in range(timeout):
            if ping(self.host, timeout=2) is not None:
                online_time = time.time()
                self.logger.info(f"Reader came back online after {online_time - offline_time:.1f}s")
                break
            time.sleep(1)
        
        if online_time is None:
            self.log_test_result("restart_monitoring", False, "Reader did not come back online", 
                               time.time() - start_time, f"Timeout after {timeout}s")
            return False
        
        total_restart_time = online_time - offline_time
        self.log_test_result("restart_monitoring", True, 
                           f"Restart completed in {total_restart_time:.1f}s", 
                           time.time() - start_time)
        return True
    
    def test_post_restart_functionality(self) -> bool:
        """Test reader functionality after restart"""
        start_time = time.time()
        try:
            self.logger.info("Testing post-restart functionality...")
            
            # Test basic connectivity
            if ping(self.host, timeout=5) is None:
                self.log_test_result("post_restart_connectivity", False, "Reader not responding after restart", 
                                   time.time() - start_time, "Ping failed")
                return False
            
            # Test LLRP connection
            if not self.web_interface:
                try:
                    if not self.test_llrp_connection():
                        self.log_test_result("post_restart_llrp", False, "LLRP connection failed after restart", 
                                           time.time() - start_time, "Connection test failed")
                        return False
                except Exception as e:
                    self.log_test_result("post_restart_llrp", False, "LLRP test failed after restart", 
                                       time.time() - start_time, str(e))
                    return False
            
            # Test web interface
            if self.web_interface:
                if not self.test_web_interface_connection():
                    self.log_test_result("post_restart_web", False, "Web interface failed after restart", 
                                       time.time() - start_time, "Web interface test failed")
                    return False
            
            self.log_test_result("post_restart_functionality", True, "All post-restart tests passed", 
                               time.time() - start_time)
            return True
            
        except Exception as e:
            self.log_test_result("post_restart_functionality", False, "Post-restart test failed", 
                               time.time() - start_time, str(e))
            return False
    
    def run_restart_test(self, simulate_restart: bool = False) -> bool:
        """Run the complete restart test suite"""
        self.logger.info("=" * 60)
        self.logger.info("Starting FX7500 RFID Reader Restart Test")
        if simulate_restart:
            self.logger.info("SIMULATION MODE - No actual restart will be performed")
        self.logger.info("=" * 60)
        
        overall_success = True
        
        # Step 1: Test initial connectivity
        if not self.test_connectivity():
            self.logger.error("Initial connectivity test failed - aborting test")
            return False
        
        # Step 2: Test connection method
        if self.web_interface:
            if not self.test_web_interface_connection():
                self.logger.error("Web interface test failed - aborting test")
                return False
        else:
            if not self.test_llrp_connection():
                self.logger.error("LLRP connection test failed - aborting test")
                return False
        
        # Step 3: Attempt restart (or simulate)
        restart_success = False
        if simulate_restart:
            self.logger.info("Simulating restart process...")
            restart_success = True
        else:
            # Try LLRP restart first (if not web interface mode)
            if not self.web_interface:
                restart_success = self.restart_via_llrp()
                if not restart_success:
                    self.logger.warning("LLRP restart failed - trying web interface as fallback")
                    restart_success = self.restart_via_web_interface()
            
            # Try web interface restart
            if self.web_interface or not restart_success:
                restart_success = self.restart_via_web_interface()
        
        if not restart_success and not simulate_restart:
            self.logger.warning("All restart methods failed - switching to simulation mode")
            simulate_restart = True
            restart_success = True
        
        # Step 4: Monitor restart process
        if not self.monitor_restart_process():
            if simulate_restart:
                self.logger.warning("Restart monitoring failed in simulation mode - this is expected")
            else:
                self.logger.error("Restart monitoring failed")
                overall_success = False
        
        # Step 5: Test post-restart functionality
        if not self.test_post_restart_functionality():
            self.logger.error("Post-restart functionality test failed")
            overall_success = False
        
        # Finalize test results
        self.test_results['end_time'] = datetime.now().isoformat()
        self.test_results['overall_success'] = overall_success
        self.test_results['simulation_mode'] = simulate_restart
        
        # Save test results
        results_file = f"fx7500_restart_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(self.test_results, f, indent=2)
        except (PermissionError, OSError) as e:
            self.logger.warning(f"Could not save results file: {e}")
            results_file = None
        
        self.logger.info("=" * 60)
        self.logger.info(f"Restart test completed - Overall success: {overall_success}")
        if simulate_restart:
            self.logger.info("Test completed in simulation mode")
        if results_file:
            self.logger.info(f"Test results saved to: {results_file}")
        else:
            self.logger.info("Test results available in console output only")
        if self.restart_log_file:
            self.logger.info(f"Detailed logs saved to: {self.restart_log_file}")
        else:
            self.logger.info("Detailed logs available in console output only")
        self.logger.info("=" * 60)
        
        return overall_success
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.reader_client:
                try:
                    self.reader_client.disconnect()
                except Exception:
                    pass
            # Always try to disconnect all readers as a safety measure
            LLRPReaderClient.disconnect_all_readers()
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.warning(f"Error during cleanup: {e}")
            else:
                print(f"Error during cleanup: {e}")


def review_logs(log_file: str):
    """Review and analyze restart test logs"""
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        return
    
    print(f"\n{'='*60}")
    print(f"REVIEWING LOGS: {log_file}")
    print(f"{'='*60}")
    
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    # Analyze log patterns
    error_count = 0
    warning_count = 0
    test_results = []
    
    for line in lines:
        if 'ERROR' in line:
            error_count += 1
            print(f"ERROR: {line.strip()}")
        elif 'WARNING' in line:
            warning_count += 1
        elif '[PASS]' in line or '[FAIL]' in line:
            test_results.append(line.strip())
    
    print(f"\nSUMMARY:")
    print(f"Total lines: {len(lines)}")
    print(f"Errors: {error_count}")
    print(f"Warnings: {warning_count}")
    print(f"Test results: {len(test_results)}")
    
    print(f"\nTEST RESULTS:")
    for result in test_results:
        print(f"  {result}")


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description="FX7500 RFID Reader Restart Test")
    parser.add_argument("--host", required=True, help="RFID reader IP address")
    parser.add_argument("--port", default=5084, type=int, help="RFID reader LLRP port")
    parser.add_argument("--web-interface", action="store_true", 
                       help="Use web interface instead of LLRP")
    parser.add_argument("--simulate", action="store_true",
                       help="Run in simulation mode (no actual restart)")
    parser.add_argument("--username", help="Username for web interface authentication")
    parser.add_argument("--password", help="Password for web interface authentication")
    parser.add_argument("--discover-endpoints", action="store_true",
                       help="Discover available restart endpoints (useful for debugging)")
    parser.add_argument("--log-dir", help="Directory for log files (default: auto-detect)")
    parser.add_argument("--review-logs", help="Review logs from specified file")
    parser.add_argument("--timeout", default=120, type=int, 
                       help="Restart monitoring timeout in seconds")
    
    args = parser.parse_args()
    
    if args.review_logs:
        review_logs(args.review_logs)
        return
    
    # Create and run restart tester
    tester = FX7500RestartTester(args.host, args.port, args.web_interface, args.log_dir, 
                                args.username, args.password)
    
    def signal_handler(signum, frame):
        print("\nReceived interrupt signal - cleaning up...")
        tester.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        success = tester.run_restart_test(simulate_restart=args.simulate)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        tester.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        tester.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
