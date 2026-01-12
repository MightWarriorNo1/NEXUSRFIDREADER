"""
Standalone real-time RFID reader demo (no unittest, no project imports).
Run: python3 utils/test_rfid_reader_tag.py --host 169.254.x.x --port 5084

This script directly uses sllurp LLRP to connect and print tags in real-time.
It does NOT require importing project-specific modules like settings.py.
"""

import argparse
import json
import os
import signal
import sys
import threading
import time
from typing import Dict, Any, Optional, Tuple, List

from sllurp.llrp import LLRPReaderConfig, LLRPReaderClient


# Minimal stdout logger
def _log(msg: str) -> None:
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"{ts} - {msg}")


def parse_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RFID Reader Real-time Tag Demo (Standalone)")
    parser.add_argument("--host", required=True, help="RFID reader IP address (LLRP)")
    parser.add_argument("--port", default=5084, type=int, help="RFID reader LLRP port")
    parser.add_argument("--antennas", default="1", help="Comma-separated list of antennas to enable (e.g., 1,2)")
    parser.add_argument("--tx-power", default=0, type=int, help="Transmit power (0=max)")
    parser.add_argument("--tari", default=0, type=int, help="Tari value (0=auto)")
    parser.add_argument("--session", default=1, type=int, help="Gen2 session")
    parser.add_argument("--tag-population", default=4, type=int, help="Tag population")
    parser.add_argument("--report-every-n-tags", default=1, type=int, dest="every_n", help="Issue TagReport every N tags")
    # Impinj options are disabled by default; enable explicitly if your reader supports them
    parser.add_argument("--enable-impinj", action="store_true", help="Enable Impinj vendor extensions")
    parser.add_argument("--impinj-search-mode", choices=["1", "2"], default=None, help="Impinj search mode (1=single,2=dual)")
    parser.add_argument("--print-json", action="store_true", help="Print full tag JSON objects instead of summary")
    return parser.parse_args()


def extract_tag_summary(tag: Dict[str, Any]) -> Tuple[str, Optional[int], Optional[int]]:
    """
    Extract common fields from a tag dict in a resilient way across readers:
    - EPC (or TagID)
    - Antenna ID
    - RSSI (PeakRSSI)
    Returns (epc_str, antenna_id, rssi)
    """
    epc_keys = [
        "EPC", "EPC-96", "epc", "tag", "TagID", "id",
    ]
    antenna_keys = ["AntennaID", "antenna", "antenna_id"]
    rssi_keys = ["PeakRSSI", "RSSI", "rssi", "peak_rssi"]

    epc_val = None
    for k in epc_keys:
        if k in tag:
            epc_val = tag.get(k)
            break
    if epc_val is None:
        # Try to find any key that contains 'epc'
        for k, v in tag.items():
            if isinstance(k, str) and "epc" in k.lower():
                epc_val = v
                break

    antenna_val = None
    for k in antenna_keys:
        if k in tag:
            antenna_val = tag.get(k)
            break

    rssi_val = None
    for k in rssi_keys:
        if k in tag:
            rssi_val = tag.get(k)
            break

    try:
        epc_str = str(epc_val) if epc_val is not None else json.dumps(tag)
    except Exception:
        epc_str = str(epc_val) if epc_val is not None else str(tag)

    try:
        antenna_id = int(antenna_val) if antenna_val is not None else None
    except Exception:
        antenna_id = None

    try:
        rssi = int(rssi_val) if rssi_val is not None else None
    except Exception:
        # Some readers report RSSI as negative dBm float or string
        try:
            rssi = int(float(rssi_val)) if rssi_val is not None else None
        except Exception:
            rssi = None

    return epc_str, antenna_id, rssi


def print_header(host: str, port: int) -> None:
    print("\n" + "=" * 60)
    print("RFID READER TAG STREAM")
    print("=" * 60)
    print(f"Reader: {host}:{port}")
    print("Press Ctrl+C to stop.\n")


def main() -> None:
    args = parse_cli_args()

    host = args.host
    port = int(args.port)
    print_header(host, port)

    # Build LLRP configuration
    try:
        enabled_antennas: List[int] = [int(x.strip()) for x in str(args.antennas).split(',') if x.strip()]
    except Exception:
        enabled_antennas = [1]

    factory_args = dict(
        report_every_n_tags=args.every_n,
        antennas=enabled_antennas,
        tx_power=args.tx_power,
        tari=args.tari,
        session=args.session,
        mode_identifier=None,
        tag_population=args.tag_population,
        start_inventory=True,
        tag_content_selector={
            "EnableROSpecID": True,
            "EnableSpecIndex": True,
            "EnableInventoryParameterSpecID": True,
            "EnableAntennaID": True,
            "EnableChannelIndex": True,
            "EnablePeakRSSI": True,
            "EnableFirstSeenTimestamp": True,
            "EnableLastSeenTimestamp": True,
            "EnableTagSeenCount": True,
            "EnableAccessSpecID": True,
            "C1G2EPCMemorySelector": {"EnableCRC": True, "EnablePCBits": True},
        },
    )

    # Only include Impinj fields if explicitly enabled
    if getattr(args, "enable_impinj", False):
        if getattr(args, "impinj_search_mode", None) is not None:
            factory_args["impinj_search_mode"] = args.impinj_search_mode
        factory_args["impinj_tag_content_selector"] = None

    config = LLRPReaderConfig(factory_args)
    client = LLRPReaderClient(host, port, config)

    # Shared state
    stop_event = threading.Event()
    last_print_time = 0.0
    printed_intro = False

    def on_tags(reader, tags):
        nonlocal last_print_time, printed_intro
        try:
            if not tags:
                return
            for tag in tags:
                if args.print_json:
                    try:
                        print("[TAG] " + json.dumps(tag, ensure_ascii=False))
                    except Exception:
                        print(f"[TAG] {tag}")
                else:
                    epc, antenna_id, rssi = extract_tag_summary(tag)
                    details = []
                    if antenna_id is not None:
                        details.append(f"ant={antenna_id}")
                    if rssi is not None:
                        details.append(f"rssi={rssi}")
                    suffix = (" (" + ", ".join(details) + ")") if details else ""
                    print(f"[TAG] {epc}{suffix}")
            last_print_time = time.time()
            printed_intro = True
        except Exception as e:
            _log(f"Tag callback error: {e}")

    client.add_tag_report_callback(on_tags)

    def handle_sigint(signum, frame):
        stop_event.set()

    signal.signal(signal.SIGINT, handle_sigint)
    if hasattr(signal, "SIGTERM"):
        try:
            signal.signal(signal.SIGTERM, handle_sigint)
        except Exception:
            pass

    try:
        _log("Connecting to reader...")
        client.connect()
        print("[STATUS] Connected to RFID reader.")

        while not stop_event.is_set():
            now = time.time()
            if not printed_intro or (now - last_print_time) > 5:
                print("[WAIT] Listening for tags...")
                printed_intro = True
                last_print_time = now
            time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    except Exception as e:
        _log(f"Reader error: {e}")
    finally:
        print("\nStopping reader...")
        try:
            LLRPReaderClient.disconnect_all_readers()
        except Exception:
            pass
        print("Done.")


if __name__ == "__main__":
    main()


