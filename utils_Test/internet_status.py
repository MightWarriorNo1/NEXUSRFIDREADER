import psutil
import socket
import platform
import subprocess

# Map interface prefixes to tunnel types
INTERFACE_MAP = {
    "eth": "Ethernet",
    "en": "Ethernet",
    "wlan": "Wifi",
    "wl": "Wifi",
    "wwan": "Cellular",
    "usb": "Cellular",
    "cdc": "Cellular",
}

def get_tunnel_type(interface):
    for prefix, tunnel in INTERFACE_MAP.items():
        if interface.lower().startswith(prefix):
            return tunnel
    # Windows-specific: check interface name directly
    iface_lower = interface.lower()
    if "ethernet" in iface_lower:
        return "Ethernet"
    elif "wi-fi" in iface_lower or "wireless" in iface_lower or "wlan" in iface_lower:
        return "Wifi"
    elif "mobile" in iface_lower or "cellular" in iface_lower or "wwan" in iface_lower:
        return "Cellular"
    return None

def has_internet(interface):
    """Check if interface has internet connectivity by pinging 8.8.8.8 through the specific interface"""
    try:
        # Get interface IP first
        interfaces = psutil.net_if_addrs()
        if interface not in interfaces:
            return False
        
        # Find IPv4 address for this interface
        ipv4_addr = None
        for addr in interfaces[interface]:
            if addr.family == socket.AF_INET:
                ipv4_addr = addr.address
                break
        
        if not ipv4_addr:
            return False
        
        if platform.system() == "Windows":
            # Windows: Use ping with -S flag to specify source IP
            result = subprocess.run(
                ["ping", "-n", "2", "-w", "2000", "-S", ipv4_addr, "8.8.8.8"],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
        else:
            # Linux: Use ping with -I flag to bind to specific interface
            result = subprocess.run(
                ["ping", "-I", interface, "-c", "2", "-W", "2", "8.8.8.8"],
                capture_output=True,
                timeout=5,
                text=True
            )
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def detect_active_tunnels():
    active_tunnels = set()

    interfaces = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for iface, addrs in interfaces.items():
        # Skip loopback interface
        if iface == 'lo':
            continue
            
        if iface not in stats or not stats[iface].isup:
            continue

        # Check if interface has an IPv4 address
        if not any(addr.family == socket.AF_INET for addr in addrs):
            continue

        if has_internet(iface):
            tunnel = get_tunnel_type(iface)
            if tunnel:
                active_tunnels.add(tunnel)

    return active_tunnels

if __name__ == "__main__":
    tunnels = detect_active_tunnels()

    if not tunnels:
        print("Nothing")
    else:
        print(" and ".join(sorted(tunnels)))