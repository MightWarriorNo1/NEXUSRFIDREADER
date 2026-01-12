#!/usr/bin/env python3
"""
Script to test internet connectivity through each network interface.
Tests each interface by pinging 8.8.8.8 through that specific interface.
After testing, reorders interface priorities: Ethernet > WiFi > Cellular
"""

import subprocess
import socket
import psutil
import platform
import sys
import re


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


def get_interface_priority_type(interface_name):
    """Get priority type for interface ordering (1=Ethernet, 2=WiFi, 3=Cellular)."""
    iface_lower = interface_name.lower()
    
    if iface_lower.startswith('eth') or iface_lower.startswith('en'):
        return 1  # Ethernet - highest priority
    elif iface_lower.startswith('wlan') or iface_lower.startswith('wl'):
        return 2  # WiFi - medium priority
    elif iface_lower.startswith('usb') or iface_lower.startswith('wwan') or iface_lower.startswith('cdc'):
        return 3  # Cellular - lowest priority
    else:
        return 99  # Unknown - lowest priority


def get_current_default_interface():
    """Get the current default network interface."""
    try:
        if platform.system() == "Linux":
            # Get default route interface
            result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode == 0 and result.stdout:
                # Parse output: default via 192.168.1.1 dev eth0 proto dhcp metric 100
                match = re.search(r'dev\s+(\w+)', result.stdout)
                if match:
                    return match.group(1)
        elif platform.system() == "Windows":
            # Use PowerShell to get default interface
            ps_cmd = 'Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Select-Object -First 1 | Get-NetAdapter | Select-Object -ExpandProperty Name'
            result = subprocess.run(
                ['powershell', '-Command', ps_cmd],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
    except Exception as e:
        print(f"Warning: Could not determine current default interface: {e}", file=sys.stderr)
    return None


def reorder_interface_priorities(working_interfaces):
    """
    Reorder network interface priorities without reboot.
    Priority: Ethernet (1) > WiFi (2) > Cellular (3)
    Returns True if successful, False otherwise.
    """
    if not working_interfaces:
        return False
    
    # Sort interfaces by priority type
    sorted_interfaces = sorted(working_interfaces, key=lambda x: get_interface_priority_type(x['name']))
    
    try:
        if platform.system() == "Linux":
            return reorder_linux_priorities(sorted_interfaces)
        elif platform.system() == "Windows":
            return reorder_windows_priorities(sorted_interfaces)
        else:
            print("Warning: Interface priority reordering not supported on this platform", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error reordering interface priorities: {e}", file=sys.stderr)
        return False


def reorder_linux_priorities(sorted_interfaces):
    """Reorder interface priorities on Linux using ip route metrics."""
    try:
        # Assign metrics: lower metric = higher priority
        # Ethernet: 100, WiFi: 200, Cellular: 300
        metric_map = {1: 100, 2: 200, 3: 300, 99: 400}
        
        success_count = 0
        
        for iface in sorted_interfaces:
            priority = get_interface_priority_type(iface['name'])
            metric = metric_map.get(priority, 400)
            
            # Get default route for this interface
            result = subprocess.run(
                ['ip', 'route', 'show', 'default', 'dev', iface['name']],
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if result.returncode == 0 and result.stdout:
                # Delete existing default route for this interface
                del_result = subprocess.run(
                    ['sudo', 'ip', 'route', 'del', 'default', 'dev', iface['name']],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                
                # Add default route with new metric
                # Extract gateway from original route
                match = re.search(r'via\s+([\d.]+)', result.stdout)
                if match:
                    gateway = match.group(1)
                    add_result = subprocess.run(
                        ['sudo', 'ip', 'route', 'add', 'default', 'via', gateway, 'dev', iface['name'], 'metric', str(metric)],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if add_result.returncode == 0:
                        print(f"  Set {iface['name']} ({iface['type']}) metric to {metric}")
                        success_count += 1
                    else:
                        print(f"  Warning: Failed to set metric for {iface['name']}: {add_result.stderr}", file=sys.stderr)
                else:
                    # Try without gateway (direct connection)
                    add_result = subprocess.run(
                        ['sudo', 'ip', 'route', 'add', 'default', 'dev', iface['name'], 'metric', str(metric)],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if add_result.returncode == 0:
                        print(f"  Set {iface['name']} ({iface['type']}) metric to {metric}")
                        success_count += 1
                    else:
                        print(f"  Warning: Failed to set metric for {iface['name']}: {add_result.stderr}", file=sys.stderr)
            else:
                # No default route exists for this interface, try to add one
                # First, try to get gateway from interface's network
                gateway_result = subprocess.run(
                    ['ip', 'route', 'show', 'dev', iface['name']],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                if gateway_result.returncode == 0 and gateway_result.stdout:
                    # Try to find a gateway in the routes
                    gateway_match = re.search(r'via\s+([\d.]+)', gateway_result.stdout)
                    if gateway_match:
                        gateway = gateway_match.group(1)
                        add_result = subprocess.run(
                            ['sudo', 'ip', 'route', 'add', 'default', 'via', gateway, 'dev', iface['name'], 'metric', str(metric)],
                            capture_output=True,
                            timeout=5,
                            text=True
                        )
                        if add_result.returncode == 0:
                            print(f"  Added default route for {iface['name']} ({iface['type']}) with metric {metric}")
                            success_count += 1
        
        return success_count > 0
    except Exception as e:
        print(f"Error in Linux priority reordering: {e}", file=sys.stderr)
        return False


def reorder_windows_priorities(sorted_interfaces):
    """Reorder interface priorities on Windows using interface metrics."""
    try:
        # Assign metrics: lower metric = higher priority
        # Ethernet: 10, WiFi: 20, Cellular: 30
        metric_map = {1: 10, 2: 20, 3: 30, 99: 40}
        
        for iface in sorted_interfaces:
            priority = get_interface_priority_type(iface['name'])
            metric = metric_map.get(priority, 40)
            
            # Set interface metric using netsh
            result = subprocess.run(
                ['netsh', 'interface', 'ip', 'set', 'interface', iface['name'], 'metric=' + str(metric)],
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if result.returncode == 0:
                print(f"  Set {iface['name']} ({iface['type']}) metric to {metric}")
            else:
                print(f"  Warning: Failed to set metric for {iface['name']}: {result.stderr}", file=sys.stderr)
        
        return True
    except Exception as e:
        print(f"Error in Windows priority reordering: {e}", file=sys.stderr)
        return False


def main():
    """Main function to test all interfaces and report results."""
    print("=" * 60)
    print("Network Interface Internet Connectivity Test")
    print("=" * 60)
    print()
    
    # Get current default interface before any changes
    current_default = get_current_default_interface()
    
    # Get all active interfaces
    interfaces = get_active_interfaces()
    
    if not interfaces:
        print("No active network interfaces found with IPv4 addresses.")
        return
    
    print(f"Found {len(interfaces)} active interface(s):")
    for iface in interfaces:
        print(f"  - {iface['name']}: {iface['ip']} ({iface['status']})")
    print()
    
    if current_default:
        print(f"Current default interface: {current_default}")
    else:
        print("Current default interface: Unable to determine")
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
    
    # Reorder interface priorities if we have working interfaces
    if working_interfaces:
        print()
        print("Reordering interface priorities (Ethernet > WiFi > Cellular)...")
        print()
        
        if reorder_interface_priorities(working_interfaces):
            print("✓ Interface priorities updated successfully")
        else:
            print("✗ Failed to update interface priorities (may require admin/sudo privileges)")
        
        # Get updated default interface
        updated_default = get_current_default_interface()
        
        print()
        print("=" * 60)
        print("INTERFACE PRIORITY UPDATE")
        print("=" * 60)
        print()
        print(f"Previous default interface: {current_default if current_default else 'Unable to determine'}")
        print(f"Updated default interface: {updated_default if updated_default else 'Unable to determine'}")
        
        if current_default != updated_default:
            print("✓ Default interface changed")
        else:
            print("ℹ Default interface unchanged (may already be optimal)")
    
    print()
    print("=" * 60)
    
    # Return exit code: 0 if at least one interface works, 1 otherwise
    sys.exit(0 if working_interfaces else 1)


if __name__ == "__main__":
    main()

