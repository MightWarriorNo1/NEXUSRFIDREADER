#!/usr/bin/env python3
"""
find_rfid_ip_2.py

Run `arp-scan` via sudo, parse output and optionally save as CSV or JSON.

Usage examples:
  # run like your original command
  sudo python3 find_rfid_ip_2.py --iface eth0 --subnet 169.254.0.0/16

  # run from a non-root shell (script will call sudo internally and ask for password)
  python3 find_rfid_ip_2.py --iface eth0 --subnet 169.254.0.0/16

  # dump to json
  sudo python3 find_rfid_ip_2.py -i eth0 -s 169.254.0.0/16 --json out.json

  # dump to csv
  sudo python3 find_rfid_ip_2.py -i eth0 -s 169.254.0.0/16 --csv out.csv

Notes:
 - Requires `arp-scan` installed on the machine.
 - The script calls `sudo arp-scan ...` (so sudo password prompt may appear).
 - If you want to avoid password prompts, configure sudoers appropriately (careful!).
"""

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from typing import List, Dict, Optional


ARP_LINE_RE = re.compile(
    r"^\s*(?P<ip>(?:\d{1,3}\.){3}\d{1,3})\s+(?P<mac>(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2})\s*(?P<vendor>.*)$"
)


def check_program_exists(prog: str) -> bool:
    return shutil.which(prog) is not None


def run_arp_scan(interface: str, subnet: str, extra_args: Optional[List[str]] = None, use_sudo: bool = True) -> str:
    """
    Runs arp-scan and returns stdout as text (raises subprocess.CalledProcessError on non-zero return).
    """
    cmd = []
    if use_sudo:
        cmd.append("sudo")
    cmd.extend(["arp-scan", "--interface", interface, subnet])
    if extra_args:
        cmd.extend(extra_args)
    try:
        # Use run to stream stderr through; text=True returns str
        res = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.stdout
    except FileNotFoundError:
        raise RuntimeError("arp-scan not found. Please install arp-scan (e.g. `sudo apt install arp-scan`).")
    except subprocess.CalledProcessError as e:
        # include stderr to help debugging
        raise RuntimeError(f"arp-scan failed (rc={e.returncode}). stderr:\n{e.stderr.strip()}")


def parse_arp_scan_output(output: str) -> List[Dict[str, str]]:
    """
    Parse arp-scan output lines like:
    169.254.10.1    c4:7d:cc:68:d8:93       Zebra Technologies Inc
    Returns list of dicts: {'ip':..., 'mac':..., 'vendor':...}
    """
    results = []
    for line in output.splitlines():
        m = ARP_LINE_RE.match(line)
        if not m:
            continue
        ip = m.group("ip")
        mac = m.group("mac").lower()
        vendor = m.group("vendor").strip() or "Unknown"
        results.append({"ip": ip, "mac": mac, "vendor": vendor})
    return results


def print_table(rows: List[Dict[str, str]]) -> None:
    if not rows:
        print("No hosts found.")
        return
    col_ip = "IP"
    col_mac = "MAC"
    col_vendor = "Vendor"
    print(f"{col_ip:16} {col_mac:20} {col_vendor}")
    print("-" * 60)
    for r in rows:
        print(f"{r['ip']:16} {r['mac']:20} {r['vendor']}")


def save_json(rows: List[Dict[str, str]], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)


def save_csv(rows: List[Dict[str, str]], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["ip", "mac", "vendor"])
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    p = argparse.ArgumentParser(description="Wrapper to run `arp-scan` from Python and parse results.")
    p.add_argument("--iface", "-i", required=True, help="interface to use (e.g. eth0)")
    p.add_argument("--subnet", "-s", required=True, help="CIDR/subnet to scan (e.g. 169.254.0.0/16)")
    p.add_argument("--no-sudo", action="store_true", help="do not run with sudo (assume you already have privileges)")
    p.add_argument("--extra", "-e", nargs="*", help="extra args to append to arp-scan (e.g. --localnet)")
    p.add_argument("--json", help="save results to this JSON file")
    p.add_argument("--csv", help="save results to this CSV file")
    args = p.parse_args()

    if not check_program_exists("arp-scan"):
        print("ERROR: `arp-scan` not found on PATH. Please install it (e.g. `sudo apt install arp-scan`).", file=sys.stderr)
        sys.exit(2)

    try:
        raw = run_arp_scan(interface=args.iface, subnet=args.subnet, extra_args=args.extra, use_sudo=not args.no_sudo)
    except RuntimeError as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(3)

    rows = parse_arp_scan_output(raw)
    print_table(rows)

    if args.json:
        try:
            save_json(rows, args.json)
            print(f"Saved JSON -> {args.json}")
        except Exception as e:
            print("Failed to save JSON:", e, file=sys.stderr)

    if args.csv:
        try:
            save_csv(rows, args.csv)
            print(f"Saved CSV -> {args.csv}")
        except Exception as e:
            print("Failed to save CSV:", e, file=sys.stderr)


if __name__ == "__main__":
    main()