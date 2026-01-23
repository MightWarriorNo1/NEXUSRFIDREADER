"""
Demo script for testing the network status checker.
This script shows how to use the NetworkStatusChecker class.
"""

import sys
import os

# Add the utils directory to the path so we can import our module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from test_network_status import NetworkStatusChecker
    
    def demo_network_status():
        """Demonstrate the network status checker functionality."""
        print("Network Status Checker Demo")
        print("=" * 40)
        
        # Create checker instance
        checker = NetworkStatusChecker()
        
        # Print detailed status
        checker.print_status()
        
        # Get status as dictionary for programmatic use
        status = checker.get_network_status()
        
        print("\nProgrammatic Usage Example:")
        print(f"WiFi Connected: {status['summary']['wifi_connected']}")
        print(f"Cellular Connected: {status['summary']['cellular_connected']}")
        print(f"Internet Available: {status['summary']['internet_available']}")
        
        # Show individual interface details
        if status['wifi_interfaces']:
            print(f"\nWiFi Interfaces Found: {len(status['wifi_interfaces'])}")
            for interface in status['wifi_interfaces']:
                print(f"  - {interface['interface']}: {'Connected' if interface.get('is_up') else 'Disconnected'}")
        
        if status['cellular_interfaces']:
            print(f"\nCellular Interfaces Found: {len(status['cellular_interfaces'])}")
            for interface in status['cellular_interfaces']:
                print(f"  - {interface['interface']}: {'Connected' if interface.get('is_up') else 'Disconnected'}")

    if __name__ == "__main__":
        demo_network_status()
        
except ImportError as e:
    print(f"Import Error: {e}")
    print("Please install required dependencies:")
    print("pip install psutil requests")
except Exception as e:
    print(f"Error: {e}")
