from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtWidgets import QTableWidgetItem, QLabel

from screens.base import BaseScreen
from ui.screens.ui_overview import Ui_OverviewScreen
from utils.logger import logger
from utils.rfid import RFID
from utils.gps import GPS
from utils.common import extract_from_gps, get_date_from_utc, pre_config_gps, find_gps_port, get_processor_id, enable_gps_at_command
from utils.data_storage import DataStorage
from utils.api_client import ApiClient
from utils.network import CURRENT_INTERFACE, get_current_active_interface
from widgets.waiting_spinner import QtWaitingSpinner
import settings
from settings import API_CONFIG, FILTER_CONFIG, DATABASE_CONFIG, reload_config
import time
import subprocess
import platform
import sqlite3
from ping3 import ping


class GPSScannerThread(QThread):
    """Background thread for scanning GPS ports without blocking the main UI"""
    gps_found = Signal(str, int)  # port, baud_rate
    gps_not_found = Signal()
    
    def __init__(self):
        super().__init__()
        self._stop_requested = False
        
    def run(self):
        """Scan for GPS ports in background"""
        baud = pre_config_gps()
        port = find_gps_port(baud)
        if port is not None and not self._stop_requested:
            self.gps_found.emit(port, baud)
        elif not self._stop_requested:
            self.gps_not_found.emit()
    
    def stop(self):
        """Request thread to stop"""
        self._stop_requested = True
        self.wait()


class OverviewScreen(BaseScreen):

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.ui = Ui_OverviewScreen()
        self.ui.setupUi(self)

        # Prepare table cells (non-editable)
        for row in range(self.ui.tableWidget.rowCount()):
            for column in range(self.ui.tableWidget.columnCount()):
                item = QTableWidgetItem("")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEditable & ~Qt.ItemFlag.ItemIsEnabled)
                self.ui.tableWidget.setItem(row, column, item)

        # Set custom column widths
        # Columns: Time, Tag, Antenna, Position, Speed, Heading
        self.ui.tableWidget.setColumnWidth(0, 140)  # Time
        self.ui.tableWidget.setColumnWidth(1, 195)  # Tag
        self.ui.tableWidget.setColumnWidth(2, 75)   # Antenna
        self.ui.tableWidget.setColumnWidth(3, 50)  # RSSI
        self.ui.tableWidget.setColumnWidth(4, 190)  # Position
        self.ui.tableWidget.setColumnWidth(5, 60)   # Speed
        self.ui.tableWidget.setColumnWidth(6, 75)   # Heading

        # Init helpers and modules
        self.api = ApiClient()
        self.storage = DataStorage(
            use_db=DATABASE_CONFIG.get('use_db', False),
            max_records=DATABASE_CONFIG.get('max_records', 100)
        )
        
        # Set device ID using processor ID
        device_id = get_processor_id()
        self.ui.device_id.setText(device_id)
        self.ui.truck_number.setText(device_id)
        
        # Set site ID from API_CONFIG
        site_id = API_CONFIG.get('site_id', 'N/A')
        self.ui.site_id.setText(site_id)

        # GPS init
        self.last_lat = None
        self.last_lon = None
        self.last_utctime = None
        
        # Track last stored values for duplicate prevention
        self.last_stored_rfid = None
        self.last_stored_lat = None
        self.last_stored_lon = None

        self.gps = None
        self.gps_scanner = None
        self.external_retry_timer = QTimer(self)
        self.external_retry_timer.timeout.connect(self._start_gps_scan)
        self.external_retry_timer.setInterval(30000)

        # GPS connection timeout tracking
        self.gps_connection_start_time = None
        self.gps_timeout_seconds = 300  # 5 minutes timeout
        self.gps_timeout_timer = QTimer(self)
        self.gps_timeout_timer.timeout.connect(self._check_gps_timeout)
        self.gps_timeout_timer.setInterval(10000)  # Check every 10 seconds

        # Enable GPS on startup
        logger.info("Attempting to enable GPS on startup...")
        enable_gps_at_command()

        # Always attempt external; retry every 30s if not connected
        self._start_gps_scan()

        # RFID init
        # Initialize RFID connection status to "Disconnected" instead of "N/A"
        self.ui.rfid_connection_status.setStyleSheet("""color: #ff0000;""")
        self.ui.rfid_connection_status.setText("Disconnected")
        
        # Initialize RFID with GPS getter function to always access current GPS instance
        self.rfid = RFID(gps=None, gps_getter=lambda: self.gps)
        self.rfid.sig_msg.connect(self._on_rfid_status)
        self.rfid.sig_arp_scan_status.connect(self._on_arp_scan_status)
        self.rfid.start()
        
        # Initialize spinner for arp-scan
        self.arp_scan_spinner = QtWaitingSpinner(self.ui.tableWidget, center_on_parent=True, disable_parent_when_spinning=False)
        
        # Initialize label for waiting message
        self.waiting_label = QLabel("Waiting for RFID Reader to connect...", self.ui.tableWidget)
        self.waiting_label.setStyleSheet("color: #00ff00; font-size: 14px; font-weight: bold; background-color: transparent;")
        self.waiting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.waiting_label.hide()

        # Schedulers
        self.health_timer = QTimer(self)
        self.health_timer.timeout.connect(self._upload_health)
        self.health_timer.start(int(API_CONFIG.get('health_interval_ms', 15000)))

        self.upload_timer = QTimer(self)
        self.upload_timer.timeout.connect(self._upload_records)
        self.upload_timer.start(int(API_CONFIG.get('record_interval_ms', 7000)))

        # GPS display update timer
        self.gps_display_timer = QTimer(self)
        self.gps_display_timer.timeout.connect(self._update_gps_display)
        self.gps_display_timer.start(2000)  # Update every 2 seconds

        # Internet status check timer
        self.internet_timer = QTimer(self)
        self.internet_timer.timeout.connect(self._check_internet_status)
        self.internet_timer.start(5000)  # Check every 5 seconds
        self._check_internet_status()  # Initial check
        
        # Initialize internet tunnel status
        self._update_internet_tunnel_display()
        
        # Internet disconnection tracking
        self.internet_disconnected_start = None
        self.internet_limit_seconds = settings.INTERNET_LIMIT_TIME * 60  # Convert minutes to seconds
        
        # Config reload timer - reload config every internet_limit_time * 3 seconds
        self.config_reload_timer = QTimer(self)
        self.config_reload_timer.timeout.connect(self._reload_config_and_update)
        self._start_config_reload_timer()
        
        # Flag to track if screen is being destroyed/left
        self._is_leaving = False

    def on_leave(self):
        logger.info("Leaving overview screen - stopping all threads and timers immediately")
        
        # Set flag to prevent any new storage operations
        self._is_leaving = True
        
        # Disconnect all signal connections first to prevent callbacks from firing
        try:
            if hasattr(self, 'rfid') and self.rfid:
                self.rfid.sig_msg.disconnect()
                self.rfid.sig_arp_scan_status.disconnect()
        except Exception as e:
            logger.debug(f"Error disconnecting RFID signals: {e}")
        
        try:
            if hasattr(self, 'gps') and self.gps:
                self.gps.sig_msg.disconnect()
        except Exception as e:
            logger.debug(f"Error disconnecting GPS signals: {e}")
        
        try:
            if hasattr(self, 'gps_scanner') and self.gps_scanner:
                self.gps_scanner.gps_found.disconnect()
                self.gps_scanner.gps_not_found.disconnect()
        except Exception as e:
            logger.debug(f"Error disconnecting GPS scanner signals: {e}")
        
        # Stop all timers unconditionally (stop even if not active to ensure clean state)
        timers_to_stop = [
            'health_timer', 'upload_timer', 'gps_display_timer', 
            'internet_timer', 'gps_timeout_timer', 'external_retry_timer', 
            'config_reload_timer'
        ]
        for timer_name in timers_to_stop:
            if hasattr(self, timer_name):
                timer = getattr(self, timer_name)
                if timer and timer.isActive():
                    timer.stop()
                    logger.debug(f"Stopped {timer_name}")
        
        # Stop all threads immediately
        if hasattr(self, 'rfid') and self.rfid:
            if self.rfid.isRunning():
                logger.info("Stopping RFID thread immediately")
                self.rfid.stop()
            else:
                # Even if not running, ensure stop flag is set
                try:
                    self.rfid._b_stop.set()
                except Exception:
                    pass
        
        if hasattr(self, 'gps') and self.gps:
            if self.gps.isRunning():
                logger.info("Stopping GPS thread immediately")
                self.gps.stop()
            else:
                # Even if not running, ensure stop flag is set
                try:
                    self.gps._b_stop.set()
                except Exception:
                    pass
        
        if hasattr(self, 'gps_scanner') and self.gps_scanner:
            if self.gps_scanner.isRunning():
                logger.info("Stopping GPS scanner thread immediately")
                self.gps_scanner.stop()
            else:
                # Even if not running, ensure stop flag is set
                try:
                    self.gps_scanner._stop_requested = True
                except Exception:
                    pass
        
        # Stop UI elements
        if hasattr(self, 'arp_scan_spinner'):
            try:
                self.arp_scan_spinner.stop()
            except Exception:
                pass
        if hasattr(self, 'waiting_label'):
            try:
                self.waiting_label.hide()
            except Exception:
                pass
        
        # Close storage
        if hasattr(self, 'storage'):
            try:
                self.storage.close()
            except Exception as e:
                logger.debug(f"Error closing storage: {e}")
        
        logger.info("All threads and timers stopped successfully")

    def _set_gps_status(self, text, ok):
        self.ui.gps_connection_status.setStyleSheet("""color: #00ff00;""" if ok else """color: #ff0000;""")
        self.ui.gps_connection_status.setText(text)

    def _set_internet_status(self, text, ok):
        self.ui.internet_status.setStyleSheet("""color: #00ff00;""" if ok else """color: #ff0000;""")
        self.ui.internet_status.setText(text)
    

    def _on_gps_status(self, status):
        # Called by external GPS worker
        if status:
            self._set_gps_status("External GPS Connected", True)
            # Reset timeout tracking when GPS connects
            self.gps_connection_start_time = None
            self.gps_timeout_timer.stop()
            # RFID accesses GPS through gps_getter function, so no manual update needed
        else:
            # External disconnected: update status and start GPS scan
            self._set_gps_status("Disconnected", False)
            # Start timeout tracking when GPS disconnects
            self.gps_connection_start_time = time.time()
            self.gps_timeout_timer.start()
            self._start_gps_scan()

    def _on_arp_scan_status(self, is_scanning):
        """Handle arp-scan status changes - show/hide spinner"""
        if is_scanning:
            self.arp_scan_spinner.start()
            self._update_waiting_label_position()
            self.waiting_label.show()
            logger.debug("ARP-scan started - showing spinner")
        else:
            self.arp_scan_spinner.stop()
            self.waiting_label.hide()
            logger.debug("ARP-scan completed - hiding spinner")
    
    def _update_waiting_label_position(self):
        """Update the position of the waiting label to be below the spinner"""
        if self.ui.tableWidget:
            # Get table widget center in local coordinates
            table_rect = self.ui.tableWidget.rect()
            center_x = table_rect.center().x()
            center_y = table_rect.center().y()
            
            # Spinner size is approximately 60x60 (innerRadius + lineLength) * 2
            spinner_size = 60
            # Position label below the spinner, centered horizontally
            label_width = 300
            label_height = 30
            label_x = center_x - label_width // 2
            label_y = center_y + spinner_size // 2 + 20  # Below spinner with spacing
            self.waiting_label.move(label_x, label_y)
            self.waiting_label.resize(label_width, label_height)

    def _on_rfid_status(self, status):
        # Check if we're leaving - if so, ignore all RFID signals
        if self._is_leaving:
            return
        
        # logger.debug(f"RFID status received: {status}")
        if status == 1:
            self.ui.rfid_connection_status.setStyleSheet("""color: #00ff00;""")
            self.ui.rfid_connection_status.setText("Connected")
            logger.info("RFID reader connected")
        elif status == 2:
            self.ui.rfid_connection_status.setStyleSheet("""color: #ff0000;""")
            self.ui.rfid_connection_status.setText("Disconnected")
            logger.warning("RFID reader disconnected")
        elif status == 3:
            # logger.debug("RFID tag detected, processing...")
            if not self.rfid.tag_data or len(self.rfid.tag_data) < 5:
                logger.warning("RFID tag detected but no tag data available")
                return
            tag = self.rfid.tag_data[0]
            lat = self.rfid.tag_data[1]
            lon = self.rfid.tag_data[2]
            speed = self.rfid.tag_data[3]
            bearing = self.rfid.tag_data[4]
            # logger.debug(f"Processing tag: EPC={tag.get('EPC-96', 'N/A')}, Antenna={tag.get('AntennaID', 'N/A')}, RSSI={tag.get('PeakRSSI', 'N/A')}")
            if lat != 0 and lon != 0:
                self.last_lat = lat
                self.last_lon = lon
                self.last_utctime = int(time.time() * 1_000_000)

            storage_flag = True
            
            # Filter records for storage based on GPS data and filter settings
            if lat == 0 and lon == 0:
                storage_flag = False
                # logger.debug(f"Tag detected but no GPS data: TAG {tag['EPC-96']} ant={tag['AntennaID']} rssi={tag['PeakRSSI']} (lat=0, lon=0)")
            
            # Apply filters from settings for storage
            if storage_flag:
                sp = FILTER_CONFIG.get('speed', {})
                if sp.get('enabled'):
                    min_s = sp.get('min')
                    max_s = sp.get('max')
                    if min_s is not None and max_s is not None and (speed < min_s or speed > max_s):
                        # logger.debug(f"Skipping storage: speed {speed} is not in range {min_s} to {max_s}")
                        storage_flag = False

            if storage_flag:
                rs = FILTER_CONFIG.get('rssi', {})
                if rs.get('enabled'):
                    min_r = rs.get('min')
                    max_r = rs.get('max')
                    if min_r is not None and max_r is not None and (tag['PeakRSSI'] < min_r or tag['PeakRSSI'] > max_r):
                        # logger.debug(f"Skipping storage: RSSI {tag['PeakRSSI']} is not in range {min_r} to {max_r}")
                        storage_flag = False

            if storage_flag:
                tr = FILTER_CONFIG.get('tag_range', {})
                if tr.get('enabled'):
                    min_t = tr.get('min')
                    max_t = tr.get('max')
                    try:
                        epc = int(tag['EPC-96'])
                        if min_t is not None and max_t is not None and (epc < min_t or epc > max_t):
                            # logger.debug(f"Skipping storage: EPC {epc} is not in range {min_t} to {max_t}")
                            storage_flag = False
                    except Exception:
                        logger.debug(f"Skipping storage: EPC {tag['EPC-96']} is not an integer")
                        storage_flag = False

            # Skip storage if storage_flag is False
            if not storage_flag:
                # Don't store records that don't pass filters, but still update UI
                # logger.info(f"Skipping storage: filters failed for tag {tag['EPC-96']}")
                pass
            else:
                # Store tag data locally if it passes all filters
                # Check if current values are different from last stored values
                current_rfid = tag['EPC-96']
                current_lat = lat
                current_lon = lon
                
                # Skip storage if all values match the last stored values
                # if (self.last_stored_rfid == current_rfid or ( self.last_stored_lat == current_lat and self.last_stored_lon == current_lon)):
                if (self.last_stored_lat == current_lat and self.last_stored_lon == current_lon):
                    # Values haven't changed, skip storage but still update UI
                    # logger.debug(f"Skipping storage: same values as last stored (RFID: {current_rfid}, lat: {current_lat}, lon: {current_lon})")
                    pass
                else:
                    # Values are different, proceed with storage
                    # Check if storage is still valid before using it
                    if self._is_leaving or not self.storage:
                        return
                    
                    if self.storage.use_db:
                        # Check if database connection is still valid
                        if not self.storage.db_connection or not self.storage.db_cursor:
                            logger.debug("Database connection closed, skipping storage")
                            return
                        
                        # Prevent duplicates within configured time window
                        duplicate_window_seconds = DATABASE_CONFIG.get('duplicate_detection_seconds', 3)
                        duplicate_window_microseconds = duplicate_window_seconds * 1_000_000
                        try:
                            self.storage.db_cursor.execute('''
                                SELECT * FROM records
                                WHERE rfidTag = ?
                                AND (
                                    ABS(timestamp - ?) < ?
                                    OR (latitude = ? AND longitude = ?)
                                )
                            ''', (tag['EPC-96'], tag['LastSeenTimestampUTC'], duplicate_window_microseconds, lat, lon))
                            rows = self.storage.db_cursor.fetchall()
                            if not rows:
                                # Prepare record list with explicit id
                                self.storage.db_cursor.execute('SELECT id FROM records ORDER BY id ASC')
                                used_ids = self.storage.db_cursor.fetchall()
                                rec = [
                                    calculate_next_id(used_ids), tag['EPC-96'], f"{tag['AntennaID']}", f"{tag['PeakRSSI']}",
                                    lat, lon, speed, bearing, "-", self.api.user_name, tag['LastSeenTimestampUTC'],
                                    "", "", "", "", "", "", "", ""
                                ]
                                self.storage.add_record(rec)
                                # Update last stored values after successful storage
                                self.last_stored_rfid = current_rfid
                                self.last_stored_lat = current_lat
                                self.last_stored_lon = current_lon
                        except (sqlite3.ProgrammingError, AttributeError) as e:
                            logger.debug(f"Database operation failed (possibly closed): {e}")
                            return
                    else:
                        new_data = [True, tag['EPC-96'], f"{tag['AntennaID']}", f"{tag['PeakRSSI']}",
                                    lat, lon, speed, bearing, "-", self.api.user_name, tag['LastSeenTimestampUTC'],
                                    "", "", "", "", "", "", "", ""]
                        self.storage.add_record(new_data)
                        # Update last stored values after successful storage
                        self.last_stored_rfid = current_rfid
                        self.last_stored_lat = current_lat
                        self.last_stored_lon = current_lon

            # one-line debug for real-time processing
            # logger.debug(f"TAG {tag['EPC-96']} ant={tag['AntennaID']} rssi={tag['PeakRSSI']} pos=({lat:.7f},{lon:.7f}) speed={speed} heading={bearing}")

            # UI updates
            table_data = [get_date_from_utc(tag['LastSeenTimestampUTC']), tag['EPC-96'], f"{tag['AntennaID']}", f"{tag['PeakRSSI']}",
                         f"{lat:.7f}".rstrip('0').rstrip('.') + ", " + f"{lon:.7f}".rstrip('0').rstrip('.'),
                         f"{speed:.4f}".rstrip('0').rstrip('.'), f"{bearing}"]
            # logger.debug(f"Updating table with data: {table_data}")
            self._refresh_table(table_data)
            self.ui.last_rfid_read.setText(tag['EPC-96'])
            self.ui.last_rfid_time.setText(get_date_from_utc(tag['LastSeenTimestampUTC']))
            self.ui.last_gps_read.setText(f"{lat:.7f}, {lon:.7f}")
            # Use actual GPS timestamp when available; otherwise use RFID timestamp
            if self.gps and self.gps.isRunning():
                gps_timestamp = self.gps.get_data_timestamp()
                if gps_timestamp:
                    self.ui.last_gps_time.setText(get_date_from_utc(gps_timestamp))
                else:
                    self.ui.last_gps_time.setText(get_date_from_utc(tag['LastSeenTimestampUTC']))
            else:
                self.ui.last_gps_time.setText(get_date_from_utc(tag['LastSeenTimestampUTC']))
            # logger.info(f"Tag processed and displayed: {tag['EPC-96']} at {get_date_from_utc(tag['LastSeenTimestampUTC'])}")

    def _refresh_table(self, new_data):
        for row in range(self.ui.tableWidget.rowCount() - 2, -1, -1):
            for column in range(self.ui.tableWidget.columnCount()):
                item = self.ui.tableWidget.item(row, column).text()
                self.ui.tableWidget.setItem(row + 1, column, QTableWidgetItem(item))
        for column in range(self.ui.tableWidget.columnCount()):
            self.ui.tableWidget.setItem(0, column, QTableWidgetItem(new_data[column]))

    def _check_gps_timeout(self):
        """Check if GPS has been disconnected for too long and enable GPS if needed"""
        if self.gps_connection_start_time is None:
            return  # No timeout tracking active
        
        current_time = time.time()
        disconnection_duration = current_time - self.gps_connection_start_time
        
        if disconnection_duration >= self.gps_timeout_seconds:
            logger.warning(f"GPS disconnected for {disconnection_duration:.0f} seconds (timeout: {self.gps_timeout_seconds} seconds). Attempting to enable GPS...")
            enable_gps_at_command()
            # Reset timeout tracking after attempting to enable GPS
            self.gps_connection_start_time = None
            self.gps_timeout_timer.stop()
        else:
            remaining_time = self.gps_timeout_seconds - disconnection_duration
            logger.debug(f"GPS still disconnected. {remaining_time:.0f} seconds remaining before GPS enable attempt")

    def _start_gps_scan(self):
        """Start GPS port scanning in background thread"""
        if self.gps_scanner and self.gps_scanner.isRunning():
            return  # Already scanning
        
        # Start timeout tracking when scanning for GPS
        if self.gps_connection_start_time is None:
            self.gps_connection_start_time = time.time()
            self.gps_timeout_timer.start()
        
        self.gps_scanner = GPSScannerThread()
        self.gps_scanner.gps_found.connect(self._on_gps_found)
        self.gps_scanner.gps_not_found.connect(self._on_gps_not_found)
        self.gps_scanner.start()
        logger.debug("Started GPS port scan in background")

    def _on_gps_found(self, port, baud):
        """Called when GPS port is found in background thread"""
        self._start_external_gps(port, baud)
        self.external_retry_timer.stop()
        logger.info(f"GPS found on port {port}, starting connection")

    def _on_gps_not_found(self):
        """Called when no GPS port is found in background thread"""
        self._set_gps_status("Disconnected", False)
        # Start timeout tracking when GPS is not found
        if self.gps_connection_start_time is None:
            self.gps_connection_start_time = time.time()
            self.gps_timeout_timer.start()
        if not self.external_retry_timer.isActive():
            self.external_retry_timer.start()
        logger.debug("No GPS port found, will retry in 30 seconds")

    def _start_external_gps(self, port, baud):
        if self.gps and self.gps.isRunning():
            self.gps.stop()
        self.gps = GPS(port=port, baud_rate=baud)
        self.gps.sig_msg.connect(self._on_gps_status)
        self.gps.start()
        # RFID will access GPS through gps_getter function, so no need to update reference
        self._set_gps_status("External GPS Connected", True)

    def _upload_health(self):
        lat, lon = (0, 0)
        if self.gps:
            lat, lon = extract_from_gps(self.gps.get_data())
        gps_text = self.ui.gps_connection_status.text()
        self.api.upload_health(bool(self.rfid.connectivity), gps_text, lat, lon)

    def _update_gps_display(self):
        """Update GPS display fields with current GPS data"""
        if self.gps and self.gps.isRunning():
            # External GPS
            lat, lon = extract_from_gps(self.gps.get_data())
            if lat != 0 and lon != 0:
                speed, bearing = self.gps.get_sdata()
                # Use actual GPS data timestamp instead of current time
                gps_timestamp = self.gps.get_data_timestamp()
                if gps_timestamp:
                    self.ui.last_gps_read.setText(f"{lat:.7f}, {lon:.7f}")
                    self.ui.last_gps_time.setText(get_date_from_utc(gps_timestamp))

    def _update_internet_tunnel_display(self):
        """Update the internet tunnel display with current active interface."""
        try:
            # First try to get from global variable set during startup
            current_interface = CURRENT_INTERFACE
            
            # If not available, try to get current interface
            if not current_interface:
                current_interface = get_current_active_interface()
            
            if current_interface:
                interface_name = current_interface['interface']
                interface_type = current_interface['type']
                self.ui.internet_tunnel.setText(f"{interface_name} ({interface_type})")
            else:
                self.ui.internet_tunnel.setText("N/A")
        except Exception as e:
            logger.debug(f"Error updating internet tunnel display: {e}")
            self.ui.internet_tunnel.setText("N/A")

    def _check_internet_status(self):
        """Check internet connectivity by pinging Google DNS"""
        try:
            response_time = ping("8.8.8.8", timeout=3)
            if response_time is not None:
                self._set_internet_status("Connected", True)
                # logger.debug(f"Internet ping successful: {response_time:.2f}ms")
                # Reset disconnection timer when connected
                self.internet_disconnected_start = None
            else:
                self._set_internet_status("Disconnected", False)
                logger.debug("Internet ping failed: no response")
                self._handle_internet_disconnection()
        except Exception as e:
            self._set_internet_status("Disconnected", False)
            logger.debug(f"Internet ping error: {e}")
            self._handle_internet_disconnection()

    def _handle_internet_disconnection(self):
        """Handle internet disconnection and check if restart is needed"""
        current_time = time.time()
        
        # Start tracking disconnection time if not already started
        if self.internet_disconnected_start is None:
            self.internet_disconnected_start = current_time
            logger.warning("Internet disconnected, starting disconnection timer")
            return
        
        # Check if disconnection time exceeds the limit
        disconnection_duration = current_time - self.internet_disconnected_start
        if disconnection_duration >= self.internet_limit_seconds:
            logger.critical(f"Internet disconnected for {disconnection_duration:.0f} seconds (limit: {self.internet_limit_seconds} seconds). Restarting device...")
            self._restart_device()
        else:
            remaining_time = self.internet_limit_seconds - disconnection_duration
            logger.warning(f"Internet still disconnected. {remaining_time:.0f} seconds remaining before restart")

    def _restart_device(self):
        """Restart the device based on the operating system"""
        logger.critical("Initiating device restart...")
        try:
            if platform.system() == "Linux":
                # For Linux/Raspberry Pi
                subprocess.run(["sudo", "reboot"], check=True)
            elif platform.system() == "Windows":
                # For Windows
                subprocess.run(["shutdown", "/r", "/t", "10"], check=True)
            else:
                logger.error(f"Unsupported operating system for restart: {platform.system()}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart device: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during restart: {e}")

    def _start_config_reload_timer(self):
        """Start or restart the config reload timer with current internet_limit_time * 3"""
        reload_interval_ms = settings.INTERNET_LIMIT_TIME * 3 * 1000  # Convert to milliseconds
        if self.config_reload_timer.isActive():
            self.config_reload_timer.stop()
        self.config_reload_timer.start(reload_interval_ms)
        # logger.debug(f"Config reload timer started with interval: {reload_interval_ms}ms ({settings.INTERNET_LIMIT_TIME * 3} seconds)")

    def _reload_config_and_update(self):
        """Reload configuration file and update all config values that depend on it"""
        # logger.info("Reloading configuration from config.json...")
        if reload_config():
            # Access updated values from settings module
            # Note: Dictionary configs (API_CONFIG, FILTER_CONFIG, etc.) are updated in-place
            # so existing references automatically reflect changes. Only primitives need re-access.
            
            # Update internet limit seconds (access via settings module to get updated value)
            self.internet_limit_seconds = settings.INTERNET_LIMIT_TIME * 60
            
            # Update site_id display if it changed (API_CONFIG is updated in-place)
            new_site_id = settings.API_CONFIG.get('site_id', 'N/A')
            current_site_id = self.ui.site_id.text()
            if new_site_id != current_site_id:
                self.ui.site_id.setText(new_site_id)
                logger.debug(f"Site ID updated to: {new_site_id}")
            
            # Update health timer interval if it changed
            new_health_interval = int(settings.API_CONFIG.get('health_interval_ms', 15000))
            if self.health_timer.interval() != new_health_interval:
                self.health_timer.setInterval(new_health_interval)
                logger.debug(f"Health timer interval updated to: {new_health_interval}ms")
            
            # Update upload timer interval if it changed
            new_upload_interval = int(settings.API_CONFIG.get('record_interval_ms', 7000))
            if self.upload_timer.interval() != new_upload_interval:
                self.upload_timer.setInterval(new_upload_interval)
                logger.debug(f"Upload timer interval updated to: {new_upload_interval}ms")
            
            # Update API client cached values
            self.api.update_config()
            
            # Restart config reload timer with new interval (in case internet_limit_time changed)
            self._start_config_reload_timer()
            
            logger.info("The whole config is updated")
        else:
            logger.error("Failed to reload configuration, using existing values")

    def _upload_records(self):
        # Check if we're leaving or storage is invalid
        if self._is_leaving or not self.storage:
            return
        
        # Check if database connection is still valid (if using database)
        if self.storage.use_db:
            if not self.storage.db_connection or not self.storage.db_cursor:
                return
        
        try:
            data = self.storage.fetch_all_records()
        except (sqlite3.ProgrammingError, AttributeError) as e:
            logger.debug(f"Failed to fetch records (possibly closed): {e}")
            return
        
        if not data:
            return
        
        # Get max_upload_records from API_CONFIG
        max_upload_records = API_CONFIG.get('max_upload_records', 10)
        device_id = get_processor_id()
        # Get site_id from API_CONFIG in settings (loaded from config.json)
        site_id = API_CONFIG.get('site_id', '')
        
        # Filter out records with no GPS data first
        valid_records = []
        for row in data:
            # Skip records with no GPS data (lat=0, lon=0, speed=0)
            latitude = row[4] if row[4] else 0
            longitude = row[5] if row[5] else 0  
            speed = int(row[6]) if row[6] else 0
            
            if latitude == 0 and longitude == 0:
                continue  # Skip this record
            
            valid_records.append(row)
        
        if not valid_records:
            return
        
        # Process records in batches of max_upload_records
        # Records are already sorted oldest first (timestamp ASC)
        total_records = len(valid_records)
        batch_number = 0
        
        while batch_number * max_upload_records < total_records:
            # Get the current batch (oldest records first)
            start_idx = batch_number * max_upload_records
            end_idx = min(start_idx + max_upload_records, total_records)
            batch_records = valid_records[start_idx:end_idx]
            
            # Build payload for this batch
            payload = []
            uploaded_record_ids = []  # Track IDs of records to be uploaded in this batch
            
            for row in batch_records:
                latitude = row[4] if row[4] else 0
                longitude = row[5] if row[5] else 0  
                speed = int(row[6]) if row[6] else 0
                heading = row[7] if row[7] else 0  # heading (bearing) from GPS
                
                # adapt to new API format
                record = {
                    "siteId": site_id,  # siteId from settings
                    "tagName": row[1],  # tagName (was rfidTag)
                    "latitude": latitude,  # latitude
                    "longitude": longitude,  # longitude
                    "speed": speed,  # speed as integer
                    "deviceId": device_id,  # deviceId from get_processor_id()
                    "antenna": int(row[2]) if row[2] else 1,  # antenna number
                    "barrier": heading,  # heading (bearing) from GPS
                    "isProcess": True  # isProcess (was isProcessed)
                }
                payload.append(record)
                uploaded_record_ids.append(row[0])  # Track the record ID (first column)
            
            # Upload this batch
            if payload and self.api.upload_records(payload):
                # Delete the successfully uploaded records
                try:
                    if not self._is_leaving and self.storage:
                        self.storage.delete_uploaded_records(uploaded_record_ids)
                    logger.debug(f"Successfully uploaded batch {batch_number + 1} with {len(uploaded_record_ids)} record(s)")
                    batch_number += 1
                except (sqlite3.ProgrammingError, AttributeError) as e:
                    logger.debug(f"Failed to delete uploaded records (possibly closed): {e}")
                    break
            else:
                # Upload failed, stop processing remaining batches
                logger.warning(f"Failed to upload batch {batch_number + 1}, stopping batch processing")
                break
        
        # Also do best-effort pruning for any old records
        if not self._is_leaving and self.storage:
            try:
                self.storage.prune_old()
            except (sqlite3.ProgrammingError, AttributeError) as e:
                logger.debug(f"Failed to prune old records (possibly closed): {e}")


def calculate_next_id(used_ids):
    smallest_available_id = 1
    for record in used_ids:
        current_id = record[0]
        if current_id == smallest_available_id:
            smallest_available_id += 1
        else:
            break
    return smallest_available_id


