#!/usr/bin/env python3
"""
Script to activate cellular interface (usb0) and reorder network interface priorities.
Sets priority order: Ethernet -> WiFi -> Cellular (usb0)
Outputs previous and updated priorities and saves to internet_output.txt
"""

import subprocess
import socket
import psutil
import platform
import sys
import re
import os
import time
from datetime import datetime


def get_default_routes():
    """Get current default routes with their metrics."""
    routes = []
    try:
        if platform.system() == "Linux":
            result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        # Parse various formats:
                        # default via 192.168.0.1 dev eth1 metric 100
                        # default via 192.168.0.1 dev eth1 proto dhcp src 192.168.0.202 metric 100
                        # default via 192.168.225.1 dev usb0 (no metric)
                        # default via 192.168.0.1 dev wlan0 metric 200
                        # Extract gateway, interface, and metric (which can appear anywhere)
                        match = re.search(r'default via (\S+) dev (\w+)', line)
                        if match:
                            gateway = match.group(1)
                            interface = match.group(2)
                            
                            # Extract metric (can appear anywhere in the line after dev)
                            metric_match = re.search(r'\bmetric (\d+)\b', line)
                            metric_value = int(metric_match.group(1)) if metric_match else 0
                            
                            # Extract src IP if present (for deletion purposes)
                            src_match = re.search(r'\bsrc (\S+)\b', line)
                            src_ip = src_match.group(1) if src_match else None
                            
                            routes.append({
                                'interface': interface,
                                'gateway': gateway,
                                'metric': metric_value,
                                'src': src_ip,
                                'raw': line.strip()
                            })
        elif platform.system() == "Windows":
            # Windows implementation would use netsh or PowerShell
            ps_cmd = 'Get-NetRoute -DestinationPrefix "0.0.0.0/0" | Select-Object InterfaceAlias, NextHop, RouteMetric'
            result = subprocess.run(
                ['powershell', '-Command', ps_cmd],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode == 0 and result.stdout:
                # Parse PowerShell output
                lines = result.stdout.strip().split('\n')
                for line in lines[2:]:  # Skip header lines
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            routes.append({
                                'interface': parts[0],
                                'gateway': parts[1],
                                'metric': int(parts[2]) if parts[2].isdigit() else 0,
                                'raw': line.strip()
                            })
    except Exception as e:
        print(f"Error getting default routes: {e}", file=sys.stderr)
    return routes


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
            interface_type = get_interface_type(iface)
            interfaces.append({
                'name': iface,
                'ip': ipv4_addr,
                'status': 'UP' if net_if_stats[iface].isup else 'DOWN',
                'type': interface_type
            })
    
    return interfaces


def get_interface_type(interface_name):
    """Determine interface type based on name."""
    iface_lower = interface_name.lower()
    
    if iface_lower.startswith('eth') or iface_lower.startswith('en'):
        return "Ethernet"
    elif iface_lower.startswith('wlan') or iface_lower.startswith('wl'):
        return "WiFi"
    elif iface_lower.startswith('usb') or iface_lower.startswith('wwan') or iface_lower.startswith('cdc'):
        return "Cellular"
    else:
        return "Unknown"


def get_interface_metric(interface_name):
    """Get the desired metric based on interface type."""
    interface_type = get_interface_type(interface_name)
    
    if interface_type == "Ethernet":
        return 100
    elif interface_type == "WiFi":
        return 200
    elif interface_type == "Cellular":
        return 300
    else:
        return 400  # Unknown interfaces get lowest priority


def test_interface_connectivity(interface_name, interface_ip):
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
        return False


def run_dhclient(interface):
    """Run dhclient on the specified interface."""
    try:
        if platform.system() == "Linux":
            result = subprocess.run(
                ['sudo', '-n', 'dhclient', interface],
                capture_output=True,
                timeout=30,
                text=True
            )
            return result.returncode == 0, result.stdout, result.stderr
        else:
            return False, "", "dhclient only available on Linux"
    except subprocess.TimeoutExpired:
        return False, "", "dhclient timed out"
    except Exception as e:
        return False, "", str(e)


def reorder_routes(routes, active_interfaces):
    """Reorder routes by setting proper metrics."""
    success = True
    errors = []
    
    if platform.system() != "Linux":
        return False, ["Route reordering only supported on Linux"]
    
    if not routes:
        return False, ["No default routes found to reorder"]
    
    try:
        # Create a map of interface -> gateway from existing routes
        # Handle duplicates by keeping the first occurrence (typically the one without metric)
        interface_gateways = {}
        interfaces_to_reorder = []
        
        for route in routes:
            iface = route['interface']
            gateway = route['gateway']
            
            # Only process if we have a gateway and haven't seen this interface yet
            if gateway and iface not in interface_gateways:
                interface_gateways[iface] = gateway
                interfaces_to_reorder.append({
                    'interface': iface,
                    'gateway': gateway
                })
        
        if not interfaces_to_reorder:
            return False, ["No valid interfaces with gateways found in routes"]
        
        # First, delete ALL existing default routes completely
        # Delete by interface to ensure we get all variations (with/without src, proto, etc.)
        interfaces_seen = set()
        for route in routes:
            iface = route['interface']
            if iface not in interfaces_seen:
                interfaces_seen.add(iface)
                try:
                    # Delete all default routes for this interface (handles all variations)
                    # This will delete routes regardless of metric, src, proto, etc.
                    delete_cmd = ['sudo', '-n', 'ip', 'route', 'del', 'default', 'dev', iface]
                    result = subprocess.run(delete_cmd, capture_output=True, timeout=5, text=True)
                    # Continue even if deletion fails - might need multiple attempts
                    # Also try deleting specific routes
                    if route.get('gateway'):
                        delete_cmd2 = ['sudo', '-n', 'ip', 'route', 'del', 'default',
                                      'via', route['gateway'], 'dev', iface]
                        subprocess.run(delete_cmd2, capture_output=True, timeout=5, text=True)
                except Exception:
                    pass
        
        # Additional cleanup: Make multiple passes to ensure all routes are deleted
        # DHCP clients may recreate routes, so we need to be thorough
        for cleanup_pass in range(3):  # Try up to 3 times
            try:
                cleanup_result = subprocess.run(
                    ['ip', 'route', 'show', 'default'],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                if cleanup_result.returncode == 0 and cleanup_result.stdout.strip():
                    # Delete any remaining default routes by interface
                    interfaces_to_clean = set()
                    for cleanup_line in cleanup_result.stdout.strip().split('\n'):
                        if cleanup_line.strip():
                            match = re.search(r'dev (\w+)', cleanup_line)
                            if match:
                                interfaces_to_clean.add(match.group(1))
                    
                    for cleanup_iface in interfaces_to_clean:
                        try:
                            # Delete all default routes for this interface
                            cleanup_cmd = ['sudo', '-n', 'ip', 'route', 'del', 'default', 'dev', cleanup_iface]
                            subprocess.run(cleanup_cmd, capture_output=True, timeout=5, text=True)
                        except Exception:
                            pass
                    
                    if cleanup_pass < 2:  # Don't sleep on last pass
                        time.sleep(0.3)  # Brief pause between passes
                else:
                    break  # No more routes to clean
            except Exception:
                break
        
        # Add routes back with proper metrics, in priority order
        # Sort interfaces by priority: Ethernet (100), WiFi (200), Cellular (300)
        sorted_interfaces = sorted(
            interfaces_to_reorder,
            key=lambda x: get_interface_metric(x['interface'])
        )
        
        for route_info in sorted_interfaces:
            ifname = route_info['interface']
            gateway = route_info['gateway']
            metric = get_interface_metric(ifname)
            
            try:
                # Try replace first (will update existing route or add if not exists)
                # If replace fails, fall back to add
                replace_cmd = [
                    'sudo', '-n', 'ip', 'route', 'replace', 'default',
                    'via', gateway,
                    'dev', ifname,
                    'metric', str(metric)
                ]
                
                result = subprocess.run(
                    replace_cmd,
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                
                if result.returncode != 0:
                    # If replace fails, try add
                    add_cmd = [
                        'sudo', '-n', 'ip', 'route', 'add', 'default',
                        'via', gateway,
                        'dev', ifname,
                        'metric', str(metric)
                    ]
                    
                    result = subprocess.run(
                        add_cmd,
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    
                    if result.returncode != 0:
                        # Check if it's just a "File exists" error (route already exists)
                        if "File exists" not in result.stderr and "already exists" not in result.stderr.lower():
                            errors.append(f"Failed to add/replace route for {ifname}: {result.stderr}")
                            success = False
            except Exception as e:
                errors.append(f"Error adding route for {ifname}: {str(e)}")
                success = False
        
        # Wait a moment for routes to settle, then verify and fix any routes that dhcp might have changed
        time.sleep(0.5)
        try:
            verify_result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True,
                timeout=5,
                text=True
            )
            if verify_result.returncode == 0:
                # Check if any routes have wrong metrics and fix them
                for verify_line in verify_result.stdout.strip().split('\n'):
                    if verify_line.strip():
                        match = re.search(r'dev (\w+)', verify_line)
                        if match:
                            verify_iface = match.group(1)
                            expected_metric = get_interface_metric(verify_iface)
                            
                            # Extract actual metric from route
                            metric_match = re.search(r'\bmetric (\d+)\b', verify_line)
                            actual_metric = int(metric_match.group(1)) if metric_match else 0
                            
                            # Only fix if metric is wrong (and it's one of our interfaces)
                            if (verify_iface in interface_gateways and 
                                actual_metric != expected_metric and 
                                expected_metric < 400):  # Skip unknown interfaces
                                # Delete wrong route and re-add with correct metric
                                try:
                                    del_cmd = ['sudo', '-n', 'ip', 'route', 'del', 'default', 'dev', verify_iface]
                                    subprocess.run(del_cmd, capture_output=True, timeout=5, text=True)
                                    
                                    replace_cmd = [
                                        'sudo', '-n', 'ip', 'route', 'replace', 'default',
                                        'via', interface_gateways[verify_iface],
                                        'dev', verify_iface,
                                        'metric', str(expected_metric)
                                    ]
                                    subprocess.run(replace_cmd, capture_output=True, timeout=5, text=True)
                                except Exception:
                                    pass
        except Exception:
            pass
        
    except Exception as e:
        errors.append(f"Error reordering routes: {str(e)}")
        success = False
    
    return success, errors


def format_routes_output(routes, title="Default Routes"):
    """Format routes for output."""
    output = [f"{title}:"]
    if not routes:
        output.append("  No default routes found")
    else:
        # Sort by metric (lower = higher priority)
        sorted_routes = sorted(routes, key=lambda x: x['metric'])
        for i, route in enumerate(sorted_routes, 1):
            metric_str = f"metric {route['metric']}" if route['metric'] > 0 else "metric 0 (highest priority)"
            output.append(f"  {i}. {route['interface']} ({get_interface_type(route['interface'])}) - "
                         f"Gateway: {route['gateway']}, {metric_str}")
            output.append(f"     Raw: {route['raw']}")
    return '\n'.join(output)


def main():
    """Main function to reorder network interfaces."""
    output_lines = []
    output_lines.append("=" * 70)
    output_lines.append("Network Interface Priority Reordering")
    output_lines.append("=" * 70)
    output_lines.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append("")
    
    # Step 1: Get initial default routes
    output_lines.append("STEP 1: Getting initial default routes...")
    initial_routes = get_default_routes()
    output_lines.append(format_routes_output(initial_routes, "Initial Default Routes"))
    output_lines.append("")
    
    # Step 2: Get and verify active interfaces
    output_lines.append("STEP 2: Getting and verifying active network interfaces...")
    active_interfaces = get_active_interfaces()
    if active_interfaces:
        output_lines.append(f"Found {len(active_interfaces)} active interface(s):")
        for iface in active_interfaces:
            # Test connectivity
            has_internet = test_interface_connectivity(iface['name'], iface['ip'])
            status_icon = "✓" if has_internet else "✗"
            connectivity = "CONNECTED" if has_internet else "NO CONNECTION"
            output_lines.append(f"  - {iface['name']}: {iface['ip']} ({iface['status']}) [{iface['type']}] {status_icon} {connectivity}")
            iface['has_internet'] = has_internet
    else:
        output_lines.append("  No active interfaces found")
    output_lines.append("")
    
    # Step 3: Run dhclient on usb0
    output_lines.append("STEP 3: Activating cellular interface (usb0)...")
    usb0_found = any(iface['name'] == 'usb0' for iface in active_interfaces)
    if usb0_found:
        success, stdout, stderr = run_dhclient('usb0')
        if success:
            output_lines.append("  ✓ Successfully ran: sudo -n dhclient usb0")
            if stdout:
                output_lines.append(f"  Output: {stdout}")
        else:
            output_lines.append(f"  ✗ Failed to run dhclient usb0")
            if stderr:
                output_lines.append(f"  Error: {stderr}")
    else:
        output_lines.append("  ⚠ usb0 interface not found, skipping dhclient")
    output_lines.append("")
    
    # Step 4: Get routes after dhclient
    output_lines.append("STEP 4: Getting default routes after dhclient...")
    routes_after_dhclient = get_default_routes()
    output_lines.append(format_routes_output(routes_after_dhclient, "Default Routes After dhclient"))
    output_lines.append("")
    
    # Step 5: Reorder routes
    output_lines.append("STEP 5: Reordering interface priorities...")
    output_lines.append("  Target priority order:")
    output_lines.append("    1. Ethernet (metric 100)")
    output_lines.append("    2. WiFi (metric 200)")
    output_lines.append("    3. Cellular (metric 300)")
    output_lines.append("")
    
    if platform.system() == "Linux" and active_interfaces:
        success, errors = reorder_routes(routes_after_dhclient, active_interfaces)
        if success:
            output_lines.append("  ✓ Successfully reordered routes")
        else:
            output_lines.append("  ✗ Failed to reorder routes:")
            for error in errors:
                output_lines.append(f"    - {error}")
    else:
        output_lines.append("  ⚠ Route reordering skipped (not Linux or no active interfaces)")
    output_lines.append("")
    
    # Step 6: Get final routes
    output_lines.append("STEP 6: Getting final default routes...")
    final_routes = get_default_routes()
    output_lines.append(format_routes_output(final_routes, "Final Default Routes"))
    output_lines.append("")
    
    # Summary
    output_lines.append("=" * 70)
    output_lines.append("SUMMARY")
    output_lines.append("=" * 70)
    output_lines.append("")
    output_lines.append("PREVIOUS PRIORITIES (after dhclient):")
    if routes_after_dhclient:
        sorted_prev = sorted(routes_after_dhclient, key=lambda x: x['metric'])
        for i, route in enumerate(sorted_prev, 1):
            metric_str = f"metric {route['metric']}" if route['metric'] > 0 else "metric 0 (default)"
            output_lines.append(f"  {i}. {route['interface']} ({get_interface_type(route['interface'])}) - {metric_str}")
    else:
        output_lines.append("  No routes found")
    output_lines.append("")
    output_lines.append("UPDATED PRIORITIES (after reordering):")
    if final_routes:
        sorted_final = sorted(final_routes, key=lambda x: x['metric'])
        for i, route in enumerate(sorted_final, 1):
            metric_str = f"metric {route['metric']}" if route['metric'] > 0 else "metric 0 (default)"
            output_lines.append(f"  {i}. {route['interface']} ({get_interface_type(route['interface'])}) - {metric_str}")
    else:
        output_lines.append("  No routes found")
    output_lines.append("")
    output_lines.append("=" * 70)
    
    # Print to console
    output_text = '\n'.join(output_lines)
    print(output_text)
    
    # Save to file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, 'internet_output.txt')
    try:
        with open(output_file, 'w') as f:
            f.write(output_text)
        print(f"\nOutput saved to: {output_file}")
    except Exception as e:
        print(f"\nError saving output to file: {e}", file=sys.stderr)
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
