"""
Network utilities for interface management and priority reordering.
"""

import subprocess
import socket
import psutil
import platform
import re
import time
from utils.logger import logger

# Global variable to store current active interface (set during app startup)
CURRENT_INTERFACE = None


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
                        match = re.search(r'default via (\S+) dev (\w+)', line)
                        if match:
                            gateway = match.group(1)
                            interface = match.group(2)
                            
                            # Extract metric (can appear anywhere in the line after dev)
                            metric_match = re.search(r'\bmetric (\d+)\b', line)
                            metric_value = int(metric_match.group(1)) if metric_match else 0
                            
                            # Extract src IP if present
                            src_match = re.search(r'\bsrc (\S+)\b', line)
                            src_ip = src_match.group(1) if src_match else None
                            
                            routes.append({
                                'interface': interface,
                                'gateway': gateway,
                                'metric': metric_value,
                                'src': src_ip,
                                'raw': line.strip()
                            })
    except Exception as e:
        logger.error(f"Error getting default routes: {e}")
    return routes


def get_active_interfaces():
    """Get all active network interfaces with IPv4 addresses."""
    interfaces = []
    try:
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
    except Exception as e:
        logger.error(f"Error getting active interfaces: {e}")
    
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
            result = subprocess.run(
                ['ping', '-I', interface_name, '-c', '2', '-W', '2', '8.8.8.8'],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        elif platform.system() == "Windows":
            result = subprocess.run(
                ['ping', '-n', '2', '-w', '2000', '-S', interface_ip, '8.8.8.8'],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        else:
            result = subprocess.run(
                ['ping', '-c', '2', '8.8.8.8'],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def get_current_active_interface():
    """Get the currently active default network interface (lowest metric)."""
    routes = get_default_routes()
    if not routes:
        return None
    
    # Sort by metric (lower = higher priority)
    sorted_routes = sorted(routes, key=lambda x: x['metric'])
    if sorted_routes:
        active_route = sorted_routes[0]
        return {
            'interface': active_route['interface'],
            'type': get_interface_type(active_route['interface']),
            'gateway': active_route['gateway'],
            'metric': active_route['metric']
        }
    return None


def reorder_interface_priorities():
    """
    Reorder network interface priorities: Ethernet (100) -> WiFi (200) -> Cellular (300).
    Returns tuple: (success, previous_priorities, updated_priorities, current_interface)
    """
    if platform.system() != "Linux":
        logger.warning("Interface reordering only supported on Linux")
        return False, [], [], None
    
    try:
        # Get initial routes
        initial_routes = get_default_routes()
        previous_priorities = sorted(initial_routes, key=lambda x: x['metric'])
        
        # Get active interfaces
        active_interfaces = get_active_interfaces()
        
        if not active_interfaces:
            logger.warning("No active interfaces found")
            return False, previous_priorities, [], None
        
        # Verify interfaces have connectivity
        logger.info("Verifying internet interfaces...")
        for iface in active_interfaces:
            has_internet = test_interface_connectivity(iface['name'], iface['ip'])
            status = "CONNECTED" if has_internet else "NO CONNECTION"
            logger.info(f"  {iface['name']} ({iface['type']}) - {iface['ip']}: {status}")
        
        if not initial_routes:
            logger.warning("No default routes found to reorder")
            return False, [], [], None
        
        # Create interface -> gateway map
        interface_gateways = {}
        interfaces_to_reorder = []
        
        for route in initial_routes:
            iface = route['interface']
            gateway = route['gateway']
            
            if gateway and iface not in interface_gateways:
                interface_gateways[iface] = gateway
                interfaces_to_reorder.append({
                    'interface': iface,
                    'gateway': gateway
                })
        
        if not interfaces_to_reorder:
            logger.warning("No valid interfaces with gateways found")
            return False, previous_priorities, [], None
        
        # Delete all existing default routes
        logger.info("Deleting existing default routes...")
        interfaces_seen = set()
        for route in initial_routes:
            iface = route['interface']
            if iface not in interfaces_seen:
                interfaces_seen.add(iface)
                try:
                    delete_cmd = ['sudo', '-n', 'ip', 'route', 'del', 'default', 'dev', iface]
                    subprocess.run(delete_cmd, capture_output=True, timeout=5, text=True)
                    if route.get('gateway'):
                        delete_cmd2 = ['sudo', '-n', 'ip', 'route', 'del', 'default',
                                      'via', route['gateway'], 'dev', iface]
                        subprocess.run(delete_cmd2, capture_output=True, timeout=5, text=True)
                except Exception:
                    pass
        
        # Additional cleanup passes
        for cleanup_pass in range(3):
            try:
                cleanup_result = subprocess.run(
                    ['ip', 'route', 'show', 'default'],
                    capture_output=True,
                    timeout=5,
                    text=True
                )
                if cleanup_result.returncode == 0 and cleanup_result.stdout.strip():
                    interfaces_to_clean = set()
                    for cleanup_line in cleanup_result.stdout.strip().split('\n'):
                        if cleanup_line.strip():
                            match = re.search(r'dev (\w+)', cleanup_line)
                            if match:
                                interfaces_to_clean.add(match.group(1))
                    
                    for cleanup_iface in interfaces_to_clean:
                        try:
                            cleanup_cmd = ['sudo', '-n', 'ip', 'route', 'del', 'default', 'dev', cleanup_iface]
                            subprocess.run(cleanup_cmd, capture_output=True, timeout=5, text=True)
                        except Exception:
                            pass
                    
                    if cleanup_pass < 2:
                        time.sleep(0.3)
                else:
                    break
            except Exception:
                break
        
        # Add routes back with proper metrics
        logger.info("Adding routes with proper priorities...")
        sorted_interfaces = sorted(
            interfaces_to_reorder,
            key=lambda x: get_interface_metric(x['interface'])
        )
        
        for route_info in sorted_interfaces:
            ifname = route_info['interface']
            gateway = route_info['gateway']
            metric = get_interface_metric(ifname)
            
            try:
                replace_cmd = [
                    'sudo', '-n', 'ip', 'route', 'replace', 'default',
                    'via', gateway,
                    'dev', ifname,
                    'metric', str(metric)
                ]
                
                result = subprocess.run(replace_cmd, capture_output=True, timeout=5, text=True)
                
                if result.returncode != 0:
                    add_cmd = [
                        'sudo', '-n', 'ip', 'route', 'add', 'default',
                        'via', gateway,
                        'dev', ifname,
                        'metric', str(metric)
                    ]
                    subprocess.run(add_cmd, capture_output=True, timeout=5, text=True)
            except Exception as e:
                logger.warning(f"Error adding route for {ifname}: {e}")
        
        # Wait and verify routes
        time.sleep(0.5)
        try:
            verify_result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True,
                timeout=5,
                text=True
            )
            if verify_result.returncode == 0:
                for verify_line in verify_result.stdout.strip().split('\n'):
                    if verify_line.strip():
                        match = re.search(r'dev (\w+)', verify_line)
                        if match:
                            verify_iface = match.group(1)
                            expected_metric = get_interface_metric(verify_iface)
                            
                            metric_match = re.search(r'\bmetric (\d+)\b', verify_line)
                            actual_metric = int(metric_match.group(1)) if metric_match else 0
                            
                            if (verify_iface in interface_gateways and 
                                actual_metric != expected_metric and 
                                expected_metric < 400):
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
        
        # Get final routes
        final_routes = get_default_routes()
        updated_priorities = sorted(final_routes, key=lambda x: x['metric'])
        
        # Get current active interface
        current_interface = get_current_active_interface()
        
        # Log results
        logger.info("=" * 60)
        logger.info("Network Interface Priority Reordering Complete")
        logger.info("=" * 60)
        logger.info("PREVIOUS PRIORITIES:")
        for i, route in enumerate(previous_priorities, 1):
            metric_str = f"metric {route['metric']}" if route['metric'] > 0 else "metric 0 (default)"
            logger.info(f"  {i}. {route['interface']} ({get_interface_type(route['interface'])}) - {metric_str}")
        
        logger.info("UPDATED PRIORITIES:")
        for i, route in enumerate(updated_priorities, 1):
            metric_str = f"metric {route['metric']}" if route['metric'] > 0 else "metric 0 (default)"
            logger.info(f"  {i}. {route['interface']} ({get_interface_type(route['interface'])}) - {metric_str}")
        
        if current_interface:
            logger.info(f"Current active interface: {current_interface['interface']} ({current_interface['type']})")
        logger.info("=" * 60)
        
        return True, previous_priorities, updated_priorities, current_interface
        
    except Exception as e:
        logger.error(f"Error reordering interface priorities: {e}")
        return False, [], [], None
