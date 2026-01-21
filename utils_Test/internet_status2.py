#!/usr/bin/env python3
"""
Script to test internet connectivity through each network interface.
Tests each interface by pinging 8.8.8.8 through that specific interface.
"""

import subprocess
import socket
import psutil
import platform
import sys


def get_active_interfaces():
    """Get all active network interfaces with IPv4 addresses."""
    interfaces = []
    net_if_addrs = psutil.net_if_addrs()
    net_if_stats = psutil.net_if_stats()
    
    for iface, addrs in net_if_addrs.items():
        # Skip loopback interface
        if iface == 'lo':
            continue
            
        # Check if interface is up
        if iface not in net_if_stats or not net_if_stats[iface].isup:
            continue
        
        # Check if interface has IPv4 address
        ipv4_addr = None
        for addr in addrs:
            if addr.family == socket.AF_INET:
                ipv4_addr = addr.address
                break
        
        if ipv4_addr:
            interfaces.append({
                'name': iface,
                'ip': ipv4_addr,
                'status': 'UP' if net_if_stats[iface].isup else 'DOWN'
            })
    
    return interfaces


def test_interface_ping(interface_name, interface_ip):
    """
    Test internet connectivity through a specific interface by pinging 8.8.8.8.
    Returns True if ping succeeds, False otherwise.
    """
    try:
        if platform.system() == "Linux":
            # Linux: Use ping with -I flag to bind to specific interface
            result = subprocess.run(
                ['ping', '-I', interface_name, '-c', '2', '-W', '2', '8.8.8.8'],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        elif platform.system() == "Windows":
            # Windows: Use ping with -S flag to specify source IP
            result = subprocess.run(
                ['ping', '-n', '2', '-w', '2000', '-S', interface_ip, '8.8.8.8'],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        else:
            # For other systems, try generic ping
            result = subprocess.run(
                ['ping', '-c', '2', '8.8.8.8'],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        print(f"Error testing {interface_name}: {e}", file=sys.stderr)
        return False


def get_tunnel_type(interface_name):
    """Determine tunnel/connection type based on interface name."""
    iface_lower = interface_name.lower()
    
    if iface_lower.startswith('eth') or iface_lower.startswith('en'):
        return "Ethernet"
    elif iface_lower.startswith('wlan') or iface_lower.startswith('wl'):
        return "WiFi"
    elif iface_lower.startswith('usb'):
        return "USB/Cellular"
    elif iface_lower.startswith('wwan') or iface_lower.startswith('cdc'):
        return "Cellular"
    elif iface_lower.startswith('tun') or iface_lower.startswith('tap'):
        return "VPN/Tunnel"
    else:
        return "Unknown"


def main():
    """Main function to test all interfaces and report results."""
    print("=" * 60)
    print("Network Interface Internet Connectivity Test")
    print("=" * 60)
    print()
    
    # Get all active interfaces
    interfaces = get_active_interfaces()
    
    if not interfaces:
        print("No active network interfaces found with IPv4 addresses.")
        return
    
    print(f"Found {len(interfaces)} active interface(s):")
    for iface in interfaces:
        print(f"  - {iface['name']}: {iface['ip']} ({iface['status']})")
    print()
    print("Testing internet connectivity (pinging 8.8.8.8) through each interface...")
    print()
    
    working_interfaces = []
    failed_interfaces = []
    
    # Test each interface
    for iface in interfaces:
        interface_name = iface['name']
        interface_ip = iface['ip']
        tunnel_type = get_tunnel_type(interface_name)
        
        print(f"Testing {interface_name} ({tunnel_type}) - {interface_ip}...", end=' ', flush=True)
        
        if test_interface_ping(interface_name, interface_ip):
            print("✓ CONNECTED")
            working_interfaces.append({
                'name': interface_name,
                'ip': interface_ip,
                'type': tunnel_type
            })
        else:
            print("✗ NO CONNECTION")
            failed_interfaces.append({
                'name': interface_name,
                'ip': interface_ip,
                'type': tunnel_type
            })
    
    print()
    print("=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print()
    
    if working_interfaces:
        print(f"✓ {len(working_interfaces)} interface(s) with internet connectivity:")
        for iface in working_interfaces:
            print(f"  • {iface['name']} ({iface['type']}) - {iface['ip']}")
    else:
        print("✗ No interfaces with internet connectivity found.")
    
    print()
    
    if failed_interfaces:
        print(f"✗ {len(failed_interfaces)} interface(s) without internet connectivity:")
        for iface in failed_interfaces:
            print(f"  • {iface['name']} ({iface['type']}) - {iface['ip']}")
    
    print()
    print("=" * 60)
    
    # Return exit code: 0 if at least one interface works, 1 otherwise
    sys.exit(0 if working_interfaces else 1)


if __name__ == "__main__":
    main()

