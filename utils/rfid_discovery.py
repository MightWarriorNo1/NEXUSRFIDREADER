"""
RFID Reader Discovery Utility

This module provides functionality to discover RFID readers on the network
using arp-scan to find devices with Impinj or Zebra vendors.
"""

import re
import shutil
import subprocess
import platform
from typing import List, Dict, Optional

from utils.logger import logger

ARP_LINE_RE = re.compile(
    r"^\s*(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\s+(?P<mac>(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2})\s*(?P<vendor>.*)$"
)


def check_arp_scan_available() -> bool:
    """Check if arp-scan is available on the system"""
    return shutil.which("arp-scan") is not None


def run_arp_scan(interface: str, subnet: str, use_sudo: bool = True) -> str:
    """
    Runs arp-scan and returns stdout as text.
    
    Args:
        interface: Network interface to use (e.g., 'eth0')
        subnet: Subnet to scan in CIDR notation (e.g., '169.254.0.0/16')
        use_sudo: Whether to run with sudo (required on Linux)
    
    Returns:
        stdout output from arp-scan
    
    Raises:
        RuntimeError: If arp-scan is not found or fails
    """
    cmd = []
    if use_sudo and platform.system() == "Linux":
        cmd.append("sudo")
    cmd.extend(["arp-scan", "--interface", interface, subnet])
    
    try:
        res = subprocess.run(
            cmd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
            # No timeout - let arp-scan run as long as needed, just like the gpt_find.py script
        )
        return res.stdout
    except FileNotFoundError:
        raise RuntimeError("arp-scan not found. Please install arp-scan (e.g. `sudo apt install arp-scan`).")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"arp-scan failed (rc={e.returncode}). stderr:\n{e.stderr.strip()}")


def parse_arp_scan_output(output: str) -> List[Dict[str, str]]:
    """
    Parse arp-scan output lines.
    
    Args:
        output: Raw output from arp-scan
    
    Returns:
        List of dicts with 'ip', 'mac', and 'vendor' keys
    """
    results = []
    seen_ips = set()  # Track unique IPs to avoid duplicates
    
    for line in output.splitlines():
        m = ARP_LINE_RE.match(line)
        if not m:
            continue
        
        ip = m.group("ip")
        # Skip duplicates (arp-scan can show the same IP multiple times)
        if ip in seen_ips:
            continue
        seen_ips.add(ip)
        
        mac = m.group("mac").lower()
        vendor = m.group("vendor").strip() or "Unknown"
        results.append({"ip": ip, "mac": mac, "vendor": vendor})
    
    return results


def discover_rfid_readers(interface: str = "eth0", subnet: str = "169.254.0.0/16") -> Optional[str]:
    """
    Discover RFID readers on the network by scanning for Impinj or Zebra devices.
    
    Args:
        interface: Network interface to use (default: 'eth0')
        subnet: Subnet to scan in CIDR notation (default: '169.254.0.0/16')
    
    Returns:
        IP address of first found RFID reader, or None if none found
    """
    # Only run on Linux systems (arp-scan typically requires sudo)
    if platform.system() != "Linux":
        logger.debug("RFID discovery only supported on Linux systems")
        return None
    
    if not check_arp_scan_available():
        logger.warning("arp-scan not available - cannot discover RFID readers")
        return None
    
    try:
        logger.info(f"======= RFID DISCOVERY STARTED =======")
        logger.info(f"Scanning for RFID readers on {interface}, subnet {subnet}")
        raw_output = run_arp_scan(interface, subnet)
        results = parse_arp_scan_output(raw_output)
        
        logger.debug(f"Found {len(results)} devices during scan")
        
        # Look for Impinj or Zebra devices
        valid_vendors = ["Impinj", "Zebra"]
        for device in results:
            vendor = device.get("vendor", "")
            ip = device.get("ip", "")
            
            # Check if vendor contains any of our target vendors
            if any(target_vendor.lower() in vendor.lower() for target_vendor in valid_vendors):
                logger.info(f"Found RFID reader: {ip} ({vendor})")
                return ip
        
        logger.debug("No RFID readers (Impinj/Zebra) found during scan")
        return None
        
    except RuntimeError as e:
        logger.warning(f"RFID discovery failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during RFID discovery: {e}")
        return None

