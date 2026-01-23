"""
Network Status Checker
Cross-platform network status detection for WiFi and cellular connections.
Works on both Windows and Linux without requiring sudo privileges.
"""

import platform
import subprocess
import socket
import time
import json
from typing import Dict, List, Optional, Tuple
import psutil
import requests


class NetworkStatusChecker:
    """Cross-platform network status checker for WiFi and cellular connections."""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.wifi_interfaces = []
        self.cellular_interfaces = []
        self._identify_interfaces()
    
    def _identify_interfaces(self):
        """Identify WiFi and cellular network interfaces."""
        try:
            interfaces = psutil.net_if_addrs()
            
            for interface_name, addresses in interfaces.items():
                # Skip loopback and virtual interfaces
                if any(skip in interface_name.lower() for skip in ['lo', 'loopback', 'docker', 'veth', 'br-']):
                    continue
                
                # Check if interface has an IP address
                has_ip = any(addr.family == socket.AF_INET and addr.address != '127.0.0.1' 
                           for addr in addresses)
                
                if has_ip:
                    # Try to identify interface type
                    interface_type = self._get_interface_type(interface_name)
                    
                    if interface_type == 'wifi':
                        self.wifi_interfaces.append(interface_name)
                    elif interface_type == 'cellular':
                        self.cellular_interfaces.append(interface_name)
                        
        except Exception as e:
            print(f"Error identifying interfaces: {e}")
    
    def _get_interface_type(self, interface_name: str) -> str:
        """Determine if interface is WiFi or cellular based on name patterns."""
        name_lower = interface_name.lower()
        
        # WiFi patterns
        wifi_patterns = ['wlan', 'wifi', 'wireless', 'wlp', 'wlo']
        if any(pattern in name_lower for pattern in wifi_patterns):
            return 'wifi'
        
        # Cellular patterns
        cellular_patterns = ['wwan', 'cellular', 'mobile', '3g', '4g', '5g', 'lte', 'gsm']
        if any(pattern in name_lower for pattern in cellular_patterns):
            return 'cellular'
        
        # On Windows, check using netsh for WiFi
        if self.platform == 'windows':
            try:
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'interfaces'],
                    capture_output=True, text=True, timeout=5
                )
                if interface_name in result.stdout:
                    return 'wifi'
            except:
                pass
        
        # Default to ethernet if not identified
        return 'ethernet'
    
    def get_interface_status(self, interface_name: str) -> Dict:
        """Get detailed status for a specific network interface."""
        try:
            # Get interface statistics
            stats = psutil.net_io_counters(pernic=True).get(interface_name)
            
            # Get interface addresses
            addresses = psutil.net_if_addrs().get(interface_name, [])
            
            # Find IPv4 address
            ipv4_address = None
            for addr in addresses:
                if addr.family == socket.AF_INET and addr.address != '127.0.0.1':
                    ipv4_address = addr.address
                    break
            
            # Check if interface is up
            is_up = ipv4_address is not None
            
            status = {
                'interface': interface_name,
                'is_up': is_up,
                'ip_address': ipv4_address,
                'bytes_sent': stats.bytes_sent if stats else 0,
                'bytes_received': stats.bytes_recv if stats else 0,
                'packets_sent': stats.packets_sent if stats else 0,
                'packets_received': stats.packets_recv if stats else 0,
            }
            
            # Add platform-specific information
            if self.platform == 'windows':
                status.update(self._get_windows_interface_info(interface_name))
            elif self.platform == 'linux':
                status.update(self._get_linux_interface_info(interface_name))
            
            return status
            
        except Exception as e:
            return {
                'interface': interface_name,
                'is_up': False,
                'error': str(e)
            }
    
    def _get_windows_interface_info(self, interface_name: str) -> Dict:
        """Get Windows-specific interface information."""
        info = {}
        
        try:
            # Get WiFi information using netsh
            if interface_name in self.wifi_interfaces:
                result = subprocess.run(
                    ['netsh', 'wlan', 'show', 'interfaces'],
                    capture_output=True, text=True, timeout=5
                )
                
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    for i, line in enumerate(lines):
                        if interface_name in line:
                            # Look for signal strength in nearby lines
                            for j in range(max(0, i-5), min(len(lines), i+5)):
                                if 'Signal' in lines[j]:
                                    signal_line = lines[j].strip()
                                    info['signal_strength'] = signal_line
                                    break
                            break
            
            # Get general interface information using ipconfig
            result = subprocess.run(
                ['ipconfig', '/all'],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                in_interface = False
                
                for line in lines:
                    if interface_name in line:
                        in_interface = True
                        continue
                    
                    if in_interface:
                        if 'Physical Address' in line:
                            info['mac_address'] = line.split(':')[-1].strip()
                        elif 'DHCP Enabled' in line:
                            info['dhcp_enabled'] = 'Yes' in line
                        elif line.strip() == '':
                            break
                            
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def _get_linux_interface_info(self, interface_name: str) -> Dict:
        """Get Linux-specific interface information."""
        info = {}
        
        try:
            # Get interface information using ip command
            result = subprocess.run(
                ['ip', 'addr', 'show', interface_name],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'link/ether' in line:
                        mac_address = line.split()[1]
                        info['mac_address'] = mac_address
                    elif 'state' in line:
                        state = line.split()[8] if len(line.split()) > 8 else 'unknown'
                        info['state'] = state
            
            # Try to get WiFi information using iwconfig (if available)
            if interface_name in self.wifi_interfaces:
                try:
                    result = subprocess.run(
                        ['iwconfig', interface_name],
                        capture_output=True, text=True, timeout=5
                    )
                    
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if 'Signal level' in line:
                                signal_info = line.strip()
                                info['signal_strength'] = signal_info
                                break
                except FileNotFoundError:
                    # iwconfig not available, skip WiFi-specific info
                    pass
                    
        except Exception as e:
            info['error'] = str(e)
        
        return info
    
    def test_internet_connectivity(self, timeout: int = 5) -> Dict:
        """Test internet connectivity using multiple methods."""
        connectivity = {
            'dns_resolution': False,
            'http_connectivity': False,
            'ping_test': False,
            'response_time': None
        }
        
        # Test DNS resolution
        try:
            socket.gethostbyname('google.com')
            connectivity['dns_resolution'] = True
        except:
            pass
        
        # Test HTTP connectivity
        try:
            start_time = time.time()
            response = requests.get('http://httpbin.org/get', timeout=timeout)
            end_time = time.time()
            
            if response.status_code == 200:
                connectivity['http_connectivity'] = True
                connectivity['response_time'] = round((end_time - start_time) * 1000, 2)  # ms
        except:
            pass
        
        # Test ping (platform-specific)
        try:
            if self.platform == 'windows':
                result = subprocess.run(
                    ['ping', '-n', '1', '8.8.8.8'],
                    capture_output=True, text=True, timeout=timeout
                )
            else:
                result = subprocess.run(
                    ['ping', '-c', '1', '8.8.8.8'],
                    capture_output=True, text=True, timeout=timeout
                )
            
            connectivity['ping_test'] = result.returncode == 0
        except:
            pass
        
        return connectivity
    
    def get_network_status(self) -> Dict:
        """Get comprehensive network status for all interfaces."""
        status = {
            'platform': self.platform,
            'timestamp': time.time(),
            'wifi_interfaces': [],
            'cellular_interfaces': [],
            'other_interfaces': [],
            'internet_connectivity': {},
            'summary': {
                'wifi_connected': False,
                'cellular_connected': False,
                'internet_available': False
            }
        }
        
        # Check WiFi interfaces
        for interface in self.wifi_interfaces:
            interface_status = self.get_interface_status(interface)
            status['wifi_interfaces'].append(interface_status)
            if interface_status.get('is_up', False):
                status['summary']['wifi_connected'] = True
        
        # Check cellular interfaces
        for interface in self.cellular_interfaces:
            interface_status = self.get_interface_status(interface)
            status['cellular_interfaces'].append(interface_status)
            if interface_status.get('is_up', False):
                status['summary']['cellular_connected'] = True
        
        # Check other active interfaces
        all_interfaces = psutil.net_if_addrs()
        for interface_name, addresses in all_interfaces.items():
            if (interface_name not in self.wifi_interfaces and 
                interface_name not in self.cellular_interfaces and
                not any(skip in interface_name.lower() for skip in ['lo', 'loopback', 'docker', 'veth', 'br-'])):
                
                has_ip = any(addr.family == socket.AF_INET and addr.address != '127.0.0.1' 
                           for addr in addresses)
                
                if has_ip:
                    interface_status = self.get_interface_status(interface_name)
                    status['other_interfaces'].append(interface_status)
        
        # Test internet connectivity
        status['internet_connectivity'] = self.test_internet_connectivity()
        status['summary']['internet_available'] = (
            status['internet_connectivity']['dns_resolution'] or
            status['internet_connectivity']['http_connectivity'] or
            status['internet_connectivity']['ping_test']
        )
        
        return status
    
    def print_status(self):
        """Print formatted network status."""
        status = self.get_network_status()
        
        print(f"\n{'='*60}")
        print(f"NETWORK STATUS REPORT - {platform.system()} {platform.release()}")
        print(f"{'='*60}")
        print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(status['timestamp']))}")
        
        # Summary
        print(f"\nSUMMARY:")
        print(f"  WiFi Connected: {'Yes' if status['summary']['wifi_connected'] else 'No'}")
        print(f"  Cellular Connected: {'Yes' if status['summary']['cellular_connected'] else 'No'}")
        print(f"  Internet Available: {'Yes' if status['summary']['internet_available'] else 'No'}")
        
        # WiFi Interfaces
        if status['wifi_interfaces']:
            print(f"\nWIFI INTERFACES:")
            for interface in status['wifi_interfaces']:
                self._print_interface_details(interface)
        
        # Cellular Interfaces
        if status['cellular_interfaces']:
            print(f"\nCELLULAR INTERFACES:")
            for interface in status['cellular_interfaces']:
                self._print_interface_details(interface)
        
        # Other Interfaces
        if status['other_interfaces']:
            print(f"\nOTHER INTERFACES:")
            for interface in status['other_interfaces']:
                self._print_interface_details(interface)
        
        # Internet Connectivity
        print(f"\nINTERNET CONNECTIVITY:")
        connectivity = status['internet_connectivity']
        print(f"  DNS Resolution: {'Yes' if connectivity['dns_resolution'] else 'No'}")
        print(f"  HTTP Connectivity: {'Yes' if connectivity['http_connectivity'] else 'No'}")
        print(f"  Ping Test: {'Yes' if connectivity['ping_test'] else 'No'}")
        if connectivity['response_time']:
            print(f"  Response Time: {connectivity['response_time']} ms")
        
        print(f"\n{'='*60}")


def _print_interface_details(self, interface: Dict):
    """Print detailed interface information."""
    status_icon = 'Yes' if interface.get('is_up', False) else 'No'
    print(f"  {status_icon} {interface['interface']}")
    
    if interface.get('is_up', False):
        print(f"    IP Address: {interface.get('ip_address', 'N/A')}")
        print(f"    Bytes Sent: {interface.get('bytes_sent', 0):,}")
        print(f"    Bytes Received: {interface.get('bytes_received', 0):,}")
        
        if 'mac_address' in interface:
            print(f"    MAC Address: {interface['mac_address']}")
        
        if 'signal_strength' in interface:
            print(f"    Signal: {interface['signal_strength']}")
        
        if 'state' in interface:
            print(f"    State: {interface['state']}")
    
    if 'error' in interface:
        print(f"    Error: {interface['error']}")


# Add the method to the class
NetworkStatusChecker._print_interface_details = _print_interface_details


def main():
    """Main function to demonstrate network status checking."""
    try:
        checker = NetworkStatusChecker()
        checker.print_status()
        
        # Also return JSON for programmatic use
        status = checker.get_network_status()
        print(f"\nJSON Output:")
        print(json.dumps(status, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
