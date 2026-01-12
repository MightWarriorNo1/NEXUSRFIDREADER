import threading
import time

from PySide6.QtCore import QThread, Signal
from sllurp.llrp import LLRP_DEFAULT_PORT, LLRPReaderConfig, LLRPReaderClient
from ping3 import ping

from settings import RFID_CONFIG, DEFAULT_RFID_HOSTS, update_rfid_host, reload_config
from utils.logger import logger
from utils.rfid_discovery import discover_rfid_readers
from utils.common import extract_from_gps


def _parse_args_from_settings(rfid_cfg):
    cfg = {
        'every_n': rfid_cfg.get('report_every_n_tags', 1),
        'antennas': rfid_cfg.get('antennas', '1'),
        'tx_power': rfid_cfg.get('tx_power', 0),
        'tari': rfid_cfg.get('tari', 0),
        'session': rfid_cfg.get('session', 1),
        'mode_identifier': rfid_cfg.get('mode_identifier', None),
        'tag_population': rfid_cfg.get('tag_population', 4),
        'impinj_search_mode': rfid_cfg.get('impinj_search_mode', None),
        'impinj_reports': rfid_cfg.get('impinj_reports', False),
        'port': rfid_cfg.get('port', LLRP_DEFAULT_PORT),
        'host': rfid_cfg.get('host', '127.0.0.1')
    }
    return cfg


def _convert_to_unicode(obj):
    if isinstance(obj, dict):
        return { _convert_to_unicode(k): _convert_to_unicode(v) for k, v in obj.items() }
    elif isinstance(obj, list):
        return [_convert_to_unicode(e) for e in obj]
    elif isinstance(obj, bytes):
        return obj.decode('utf-8')
    else:
        return obj


class RFID(QThread):

    sig_msg = Signal(int)
    sig_arp_scan_status = Signal(bool)  # True = started, False = stopped

    def __init__(self, gps=None, gps_getter=None):
        super().__init__()
        self._b_stop = threading.Event()
        self.tag_data = None
        self.connectivity = None
        self.reader = None
        self._cfg = _parse_args_from_settings(RFID_CONFIG if isinstance(RFID_CONFIG, dict) else {})
        self.host = self._cfg['host']
        self._set_reader(self.host, False)
        self._discovery_in_progress = False
        self.gps = gps
        self.gps_getter = gps_getter  # Function to get current GPS instance

    def set_reader(self, host, status):
        self._set_reader(host, status)

    def _set_reader(self, host, status):
        self.connectivity = status
        self.host = host
        args = _parse_args_from_settings(RFID_CONFIG if isinstance(RFID_CONFIG, dict) else {})
        enabled_antennas = [int(x.strip()) for x in str(args['antennas']).split(',')]
        factory_args = dict(
            report_every_n_tags=args['every_n'],
            antennas=enabled_antennas,
            tx_power=args['tx_power'],
            tari=args['tari'],
            session=args['session'],
            mode_identifier=args['mode_identifier'],
            tag_population=args['tag_population'],
            start_inventory=True,
            tag_content_selector={
                'EnableROSpecID': True,
                'EnableSpecIndex': True,
                'EnableInventoryParameterSpecID': True,
                'EnableAntennaID': True,
                'EnableChannelIndex': True,
                'EnablePeakRSSI': True,
                'EnableFirstSeenTimestamp': True,
                'EnableLastSeenTimestamp': True,
                'EnableTagSeenCount': True,
                'EnableAccessSpecID': True,
                'C1G2EPCMemorySelector': {
                    'EnableCRC': True,
                    'EnablePCBits': True,
                }
            },
            impinj_search_mode=args['impinj_search_mode'],
            impinj_tag_content_selector=None,
        )

        port = args['port']
        config = LLRPReaderConfig(factory_args)
        self.reader = LLRPReaderClient(host, port, config)
        self.reader.add_tag_report_callback(self.tag_seen_callback)
        logger.debug("RFID initialized.")

    def tag_seen_callback(self, reader, tags):
        if tags:
            # logger.debug(f"RFID tags detected: {len(tags)} tags")
            converted_tags = _convert_to_unicode(tags)
            # Get GPS data if available - use getter function if available, otherwise use direct reference
            lat, lon, speed, bearing = 0, 0, 0, 0
            gps_instance = self.gps_getter() if self.gps_getter else self.gps
            if gps_instance and hasattr(gps_instance, 'isRunning') and gps_instance.isRunning():
                try:
                    lat, lon = extract_from_gps(gps_instance.get_data())
                    speed, bearing = gps_instance.get_sdata()
                except Exception as e:
                    logger.debug(f"Error reading GPS data: {e}")
                    lat, lon, speed, bearing = 0, 0, 0, 0
            # Round to 7 decimals for consistency
            lat = round(lat, 7)
            lon = round(lon, 7)
            # Structure: [tag_dict, lat, lon, speed, bearing]
            # For multiple tags, use the first one
            if isinstance(converted_tags, list) and len(converted_tags) > 0:
                tag_dict = converted_tags[0]
            elif isinstance(converted_tags, dict):
                tag_dict = converted_tags
            else:
                tag_dict = converted_tags
            self.tag_data = [tag_dict, lat, lon, speed, bearing]
            # logger.debug(f"Tag data: {self.tag_data}")
            self.sig_msg.emit(3)
        else:
            logger.debug("RFID callback called but no tags found")

    def run(self):
        logger.debug(f"RFID thread starting, attempting to connect to {self.host}:{self._cfg['port']}")
        # Emit initial "Disconnected" status if connectivity is False or None
        if self.connectivity is not True:
            self.connectivity = False
            self.sig_msg.emit(2)
        
        # Initial connection attempts with limited retries before triggering discovery
        connection_attempts = 0
        max_initial_attempts = 10  # Try 10 times before switching to discovery mode
        
        while not self._b_stop.is_set() and connection_attempts < max_initial_attempts:
            try:
                logger.debug("Attempting RFID reader connection...")
                self.reader.connect()
                logger.info("RFID reader connected successfully")
                self.connectivity = True
                self.sig_msg.emit(1)
                break
            except Exception as e:
                logger.debug(f"RFID connection attempt failed: {e}")
                connection_attempts += 1
                if self.connectivity is True:
                    self.connectivity = False
                    self.sig_msg.emit(2)
                elif self.connectivity is not False:
                    # Handle None case - ensure it's set to False and emit Disconnected
                    self.connectivity = False
                    self.sig_msg.emit(2)
            time.sleep(.1)
        
        # If initial connection failed, check ping and trigger discovery
        if self.connectivity is False and not self._b_stop.is_set():
            logger.info("Initial connection attempts failed, checking network connectivity and starting discovery")
            # Check if host is reachable via ping
            try:
                response_time = ping(self.host, timeout=3)
                if response_time is None:
                    logger.info("Host is not reachable, starting RFID discovery")
                    if not self._discovery_in_progress:
                        self._attempt_discovery()
            except Exception:
                logger.info("Ping failed, starting RFID discovery")
                if not self._discovery_in_progress:
                    self._attempt_discovery()

        while not self._b_stop.is_set():
            try:
                response_time = ping(self.host, timeout=3)
                if response_time is not None:
                    if self.connectivity is False:
                        LLRPReaderClient.disconnect_all_readers()
                        self.reader = None
                        self._set_reader(self.host, True)
                        self.reader.connect()
                        self.sig_msg.emit(1)
                        # Reset discovery tracking when connection is restored
                        self._discovery_in_progress = False
                else:
                    if self.connectivity is True:
                        self.connectivity = False
                        self.sig_msg.emit(2)
                    # Check if we should trigger discovery: disconnected and ping failed
                    elif self.connectivity is False:
                        # Continuously attempt discovery if not already in progress
                        if not self._discovery_in_progress:
                            self._attempt_discovery()
            except Exception:
                if self.connectivity is True:
                    self.connectivity = False
                    self.sig_msg.emit(2)
                # Also check for discovery on ping exceptions
                elif self.connectivity is False:
                    # Continuously attempt discovery if not already in progress
                    if not self._discovery_in_progress:
                        self._attempt_discovery()
            time.sleep(.1)

    def _attempt_discovery(self):
        """Attempt to discover a new RFID reader when disconnected. Runs continuously until a reader is found."""
        if self._discovery_in_progress:
            return
        
        self._discovery_in_progress = True
        logger.info("======= RFID DISCOVERY PROCESS STARTED =======")
        logger.info("RFID disconnected and ping failed - starting continuous discovery for RFID reader")
        logger.info("Discovery will run continuously until a reader is found (like 'gpt_find.py')")
        
        # Keep trying until we find a reader or connection is restored
        while not self._b_stop.is_set() and self.connectivity is False:
            try:
                new_host = None
                
                # First, try default RFID hosts by attempting actual connection
                logger.info(f"Trying default RFID hosts: {DEFAULT_RFID_HOSTS}")
                for default_host in DEFAULT_RFID_HOSTS:
                    if self._b_stop.is_set():
                        break
                    
                    logger.info(f"Attempting to connect to default host: {default_host}")
                    try:
                        # Create a temporary reader to test connection
                        test_config = LLRPReaderConfig({
                            'report_every_n_tags': 1,
                            'antennas': [1],
                            'start_inventory': False  # Don't start inventory for testing
                        })
                        test_reader = LLRPReaderClient(default_host, self._cfg['port'], test_config)
                        
                        # Try to connect with a short timeout
                        test_reader.connect()
                        logger.info(f"Successfully connected to default host {default_host} - this is an RFID reader!")
                        
                        # Disconnect the test reader
                        try:
                            test_reader.disconnect()
                        except Exception:
                            pass
                        
                        new_host = default_host
                        break
                    except Exception as e:
                        logger.debug(f"Default host {default_host} connection failed: {e}")
                
                # If no default host connected, try arp-scan discovery
                if not new_host:
                    logger.info("All default hosts failed to connect, running arp-scan discovery")
                    self.sig_arp_scan_status.emit(True)  # Signal that arp-scan is starting
                    try:
                        new_host = discover_rfid_readers(interface="eth0", subnet="169.254.0.0/16")
                    finally:
                        self.sig_arp_scan_status.emit(False)  # Signal that arp-scan is complete
                
                if new_host:
                    if new_host != self.host:
                        logger.info(f"Found new RFID reader at {new_host}, updating settings and reconnecting")
                        
                        # Update settings with the new host
                        if update_rfid_host(new_host):
                            # Reload config to get updated host
                            reload_config()
                            # Update local config
                            self._cfg = _parse_args_from_settings(RFID_CONFIG if isinstance(RFID_CONFIG, dict) else {})
                            
                            # Disconnect current reader and set up new one
                            try:
                                LLRPReaderClient.disconnect_all_readers()
                            except Exception:
                                pass
                            
                            self.reader = None
                            self.host = new_host
                            self._set_reader(self.host, False)
                            
                            # Attempt to connect to the new reader
                            try:
                                logger.info(f"Attempting to connect to newly discovered reader at {self.host}")
                                self.reader.connect()
                                self.connectivity = True
                                self.sig_msg.emit(1)
                                logger.info(f"Successfully connected to newly discovered RFID reader at {self.host}")
                                break  # Exit discovery loop on successful connection
                            except Exception as e:
                                logger.warning(f"Failed to connect to newly discovered reader at {self.host}: {e}")
                                self.connectivity = False
                                self.sig_msg.emit(2)
                                # Continue discovery loop to retry
                        else:
                            logger.error("Failed to update RFID host in settings")
                            # Continue discovery loop to retry
                    else:
                        # Same host discovered - try to reconnect (network issue may be resolved)
                        logger.info(f"Discovered reader is the same as current host: {self.host}, attempting to reconnect")
                        try:
                            LLRPReaderClient.disconnect_all_readers()
                        except Exception:
                            pass
                        
                        self.reader = None
                        self._set_reader(self.host, False)
                        
                        try:
                            logger.info(f"Attempting to reconnect to reader at {self.host}")
                            self.reader.connect()
                            self.connectivity = True
                            self.sig_msg.emit(1)
                            logger.info(f"Successfully reconnected to RFID reader at {self.host}")
                            break  # Exit discovery loop on successful connection
                        except Exception as e:
                            logger.warning(f"Failed to reconnect to reader at {self.host}: {e}")
                            self.connectivity = False
                            self.sig_msg.emit(2)
                            # Continue discovery loop to retry
                else:
                    logger.debug("No RFID reader found during discovery, retrying...")
                    # Small delay before retry to avoid tight loop (but still continuous)
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error during RFID discovery: {e}")
                # Small delay before retry on error
                time.sleep(1)
        
        self._discovery_in_progress = False
        if self.connectivity is True:
            logger.info("RFID discovery completed - reader connected")
        else:
            logger.debug("RFID discovery stopped (thread stopping or connection restored)")

    def stop(self):
        self._b_stop.set()
        self.wait()
        LLRPReaderClient.disconnect_all_readers()


