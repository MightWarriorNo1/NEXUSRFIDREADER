"""
Network interface management utilities.
Provides functions to check internet connectivity and manage routing priorities.
"""

import subprocess
import socket
import psutil
import platform
import time
from utils.logger import logger


def get_interface_type(interface_name):
    """
    Determine interface type based on name.
    Returns: 'ethernet', 'wifi', 'cellular', or 'unknown'
    """
    iface_lower = interface_name.lower()
    
    if iface_lower.startswith('eth') or iface_lower.startswith('en'):
        return 'ethernet'
    elif iface_lower.startswith('wlan') or iface_lower.startswith('wl'):
        return 'wifi'
    elif iface_lower.startswith('usb') or iface_lower.startswith('wwan') or iface_lower.startswith('cdc'):
        return 'cellular'
    else:
        return 'unknown'


def get_active_interfaces():
    """
    Get all active network interfaces with IPv4 addresses.
    Returns list of dicts with 'name', 'ip', 'type', 'status'
    """
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
                'type': interface_type,
                'status': 'UP' if net_if_stats[iface].isup else 'DOWN'
            })
    
    return interfaces


def test_interface_internet(interface_name, interface_ip, timeout=3):
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
                timeout=timeout,
                text=True
            )
            return result.returncode == 0
        elif platform.system() == "Windows":
            # Windows: Use ping with -S flag to specify source IP
            result = subprocess.run(
                ['ping', '-n', '2', '-w', '2000', '-S', interface_ip, '8.8.8.8'],
                capture_output=True,
                timeout=timeout,
                text=True
            )
            return result.returncode == 0
        else:
            # For other systems, try generic ping
            result = subprocess.run(
                ['ping', '-c', '2', '8.8.8.8'],
                capture_output=True,
                timeout=timeout,
                text=True
            )
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception as e:
        logger.debug(f"Error testing {interface_name}: {e}")
        return False


def get_interface_gateway(interface_name):
    """
    Get the gateway IP for a specific interface.
    Returns gateway IP string or None if not found.
    """
    try:
        if platform.system() == "Linux":
            # Method 1: Try to get gateway from route to 8.8.8.8 via this interface
            result = subprocess.run(
                ['ip', 'route', 'get', '8.8.8.8', 'oif', interface_name],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'via' in line:
                        # Extract gateway IP
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'via' and i + 1 < len(parts):
                                gateway = parts[i + 1]
                                # Validate it's an IP address
                                if '.' in gateway and gateway.split('.')[0].isdigit():
                                    return gateway
            
            # Method 2: Get default route for this interface
            result = subprocess.run(
                ['ip', 'route', 'show', 'dev', interface_name],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'default via' in line:
                        # Extract gateway IP
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'via' and i + 1 < len(parts):
                                gateway = parts[i + 1]
                                # Validate it's an IP address
                                if '.' in gateway and gateway.split('.')[0].isdigit():
                                    return gateway
            
            # Method 3: Check all default routes and find one for this interface
            result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if interface_name in line and 'via' in line:
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if part == 'via' and i + 1 < len(parts):
                                gateway = parts[i + 1]
                                # Validate it's an IP address
                                if '.' in gateway and gateway.split('.')[0].isdigit():
                                    return gateway
        elif platform.system() == "Windows":
            # Windows: Use route print
            result = subprocess.run(
                ['route', 'print', '-4'],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode == 0:
                # Parse route table (simplified)
                lines = result.stdout.split('\n')
                for line in lines:
                    if interface_name in line and '0.0.0.0' in line:
                        parts = line.split()
                        if len(parts) >= 3:
                            return parts[2]
    except Exception as e:
        logger.debug(f"Error getting gateway for {interface_name}: {e}")
    
    return None


def set_route_priority(interface_name, gateway, metric):
    """
    Set routing priority for an interface by adding/updating default route with specific metric.
    Lower metric = higher priority.
    """
    try:
        if platform.system() == "Linux":
            # First, remove all existing default routes for this interface
            # This ensures we don't have duplicates
            # Try multiple times to catch all variations
            removal_commands = [
                ['sudo', '-n', 'ip', 'route', 'del', 'default', 'dev', interface_name],
                ['sudo', '-n', 'ip', 'route', 'del', 'default', 'via', gateway, 'dev', interface_name],
            ]
            
            for cmd in removal_commands:
                # Run removal command (ignore errors - route might not exist)
                subprocess.run(cmd, capture_output=True, timeout=5, text=True)
            
            # Also try to remove routes with any metric by parsing the route table
            result = subprocess.run(
                ['ip', 'route', 'show', 'default', 'dev', interface_name],
                capture_output=True,
                timeout=5,
                text=True
            )
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and 'default' in line and interface_name in line:
                        # Parse the route line and reconstruct delete command
                        # Format: "default via GATEWAY dev INTERFACE [metric METRIC] [proto PROTO] [src SRC]"
                        parts = line.split()
                        try:
                            # Find 'via' and 'dev' to extract gateway and interface
                            via_idx = parts.index('via') if 'via' in parts else -1
                            dev_idx = parts.index('dev') if 'dev' in parts else -1
                            
                            if via_idx >= 0 and dev_idx >= 0 and via_idx + 1 < len(parts) and dev_idx + 1 < len(parts):
                                gateway = parts[via_idx + 1]
                                # Build delete command
                                del_cmd = ['sudo', '-n', 'ip', 'route', 'del', 'default', 'via', gateway, 'dev', interface_name]
                                subprocess.run(del_cmd, capture_output=True, timeout=5, text=True)
                        except (ValueError, IndexError):
                            # If parsing fails, try simpler deletion
                            pass
            
            # Add new default route with specified metric
            result = subprocess.run(
                ['sudo', '-n', 'ip', 'route', 'add', 'default', 'via', gateway, 'dev', interface_name, 'metric', str(metric)],
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"Set route priority for {interface_name}: metric {metric} (gateway: {gateway})")
                return True
            else:
                logger.warning(f"Failed to set route priority for {interface_name}: {result.stderr}")
                return False
        else:
            logger.warning(f"Route priority management not implemented for {platform.system()}")
            return False
    except Exception as e:
        logger.error(f"Error setting route priority for {interface_name}: {e}")
        return False


def configure_network_priorities():
    """
    Check internet connectivity for all interfaces and configure routing priorities.
    Priority order: Ethernet > WiFi > Cellular
    
    Returns dict with results:
    {
        'success': bool,
        'configured': list of interface names that were configured,
        'working': list of interfaces with internet,
        'failed': list of interfaces without internet
    }
    """
    if platform.system() != "Linux":
        logger.info("Network priority management only supported on Linux")
        return {
            'success': False,
            'configured': [],
            'working': [],
            'failed': []
        }
    
    logger.info("Configuring network interface priorities...")
    
    # Get all active interfaces
    interfaces = get_active_interfaces()
    
    if not interfaces:
        logger.warning("No active network interfaces found")
        return {
            'success': False,
            'configured': [],
            'working': [],
            'failed': []
        }
    
    logger.info(f"Found {len(interfaces)} active interface(s)")
    
    # Test internet connectivity for each interface
    working_interfaces = []
    failed_interfaces = []
    
    for iface in interfaces:
        interface_name = iface['name']
        interface_ip = iface['ip']
        interface_type = iface['type']
        
        logger.info(f"Testing {interface_name} ({interface_type}) - {interface_ip}...")
        
        if test_interface_internet(interface_name, interface_ip):
            logger.info(f"  ✓ {interface_name} has internet connectivity")
            working_interfaces.append(iface)
        else:
            logger.info(f"  ✗ {interface_name} has no internet connectivity")
            failed_interfaces.append(iface)
    
    if not working_interfaces:
        logger.warning("No interfaces with internet connectivity found")
        return {
            'success': False,
            'configured': [],
            'working': [],
            'failed': [iface['name'] for iface in failed_interfaces]
        }
    
    # Sort working interfaces by priority: Ethernet > WiFi > Cellular
    priority_order = {'ethernet': 1, 'wifi': 2, 'cellular': 3}
    
    def get_priority(iface):
        return priority_order.get(iface['type'], 99)
    
    working_interfaces.sort(key=get_priority)
    
    # Assign metrics (lower = higher priority)
    # Ethernet: 100, WiFi: 300, Cellular: 500
    metric_map = {'ethernet': 100, 'wifi': 300, 'cellular': 500}
    
    configured = []
    
    # Track count of interfaces by type for proper metric assignment
    type_counters = {'ethernet': 0, 'wifi': 0, 'cellular': 0}
    
    # Set priorities for each working interface
    for iface in working_interfaces:
        interface_name = iface['name']
        interface_type = iface['type']
        
        # Get gateway for this interface
        gateway = get_interface_gateway(interface_name)
        
        if not gateway:
            logger.warning(f"Could not determine gateway for {interface_name}, skipping")
            continue
        
        # Calculate metric based on type and position within same type
        base_metric = metric_map.get(interface_type, 1000)
        # Add small offset for multiple interfaces of same type
        type_counters[interface_type] = type_counters.get(interface_type, 0) + 1
        metric = base_metric + ((type_counters[interface_type] - 1) * 10)
        
        if set_route_priority(interface_name, gateway, metric):
            configured.append(interface_name)
            logger.info(f"Configured {interface_name} ({interface_type}) with metric {metric}")
        else:
            logger.warning(f"Failed to configure {interface_name}")
    
    # Wait a moment for routes to settle
    time.sleep(1)
    
    logger.info(f"Network priority configuration complete. {len(configured)} interface(s) configured.")
    
    return {
        'success': len(configured) > 0,
        'configured': configured,
        'working': [iface['name'] for iface in working_interfaces],
        'failed': [iface['name'] for iface in failed_interfaces]
    }

