import threading

from PySide6.QtCore import Signal, QTimer, Qt
from PySide6.QtWidgets import QLineEdit, QLabel
from screens.base import BaseScreen
from ui.screens.ui_settings import Ui_SettingsScreen
from settings import load_config, save_config, reload_config
from utils.logger import logger


class SettingsScreen(BaseScreen):

    sig_result = Signal(bool)

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.ui = Ui_SettingsScreen()
        self.ui.setupUi(self)
        
        # Initialize notification label
        self.notification_label = QLabel("", self)
        self.notification_label.setStyleSheet("color: #00ff00; font-size: 14px; font-weight: bold; background-color: rgba(0, 0, 0, 150); padding: 10px; border-radius: 5px;")
        self.notification_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.notification_label.hide()
        self.notification_label.setWordWrap(True)
        
        # Timer to hide notification after 3 seconds
        self.notification_timer = QTimer(self)
        self.notification_timer.setSingleShot(True)
        self.notification_timer.timeout.connect(self._hide_notification)
        
        # Connect save button
        self.ui.setting_save_btn.released.connect(self.save_settings)

    def on_enter(self):
        """Load configuration from config.json and populate UI fields"""
        try:
            config = load_config()
            
            # GPS Config
            gps_config = config.get("gps_config", {})
            self.ui.edit_probe_baud_rate.setText(str(gps_config.get("probe_baud_rate", "")))
            self.ui.edit_baud_rate.setText(str(gps_config.get("baud_rate", "")))
            
            # RFID Config
            rfid_config = config.get("rfid_config", {})
            self.ui.edit_rfid_host.setText(str(rfid_config.get("host", "")))
            self.ui.edit_rfid_port.setText(str(rfid_config.get("port", "")))
            
            # API Config
            api_config = config.get("api_config", {})
            self.ui.edit_site_id.setText(str(api_config.get("site_id", "")))
            self.ui.edit_record_interval_ms.setText(str(api_config.get("record_interval_ms", "")))
            self.ui.edit_max_upload_records.setText(str(api_config.get("max_upload_records", "")))
            
            # Database Config
            database_config = config.get("database_config", {})
            self.ui.edit_max_records.setText(str(database_config.get("max_records", "")))
            self.ui.edit_duplicate_detection_seconds.setText(str(database_config.get("duplicate_detection_seconds", "")))
            
            # Filter Config - Speed
            filter_config = config.get("filter_config", {})
            speed_config = filter_config.get("speed", {})
            self.ui.edit_min_speed.setText(str(speed_config.get("min", "")))
            self.ui.edit_max_speed.setText(str(speed_config.get("max", "")))
            
            logger.info("Settings screen loaded configuration from config.json")
        except Exception as e:
            logger.error(f"Error loading configuration in settings screen: {e}")
    
    def _show_notification(self, message, is_error=False):
        """Show notification message for 3 seconds"""
        # Set message and color
        self.notification_label.setText(message)
        if is_error:
            self.notification_label.setStyleSheet("color: #ff0000; font-size: 14px; font-weight: bold; background-color: rgba(0, 0, 0, 150); padding: 10px; border-radius: 5px;")
        else:
            self.notification_label.setStyleSheet("color: #00ff00; font-size: 14px; font-weight: bold; background-color: rgba(0, 0, 0, 150); padding: 10px; border-radius: 5px;")
        
        # Position label in center of screen
        self._update_notification_position()
        
        # Show label and raise it above other widgets
        self.notification_label.show()
        self.notification_label.raise_()
        
        # Start timer to hide after 3 seconds
        self.notification_timer.start(3000)
    
    def _update_notification_position(self):
        """Update the position of the notification label to be centered"""
        if self:
            # Get screen center
            screen_rect = self.rect()
            center_x = screen_rect.center().x()
            center_y = screen_rect.center().y()
            
            # Label size
            label_width = 300
            label_height = 50
            
            # Position label in center
            label_x = center_x - label_width // 2
            label_y = center_y - label_height // 2
            self.notification_label.move(label_x, label_y)
            self.notification_label.resize(label_width, label_height)
    
    def _hide_notification(self):
        """Hide the notification label"""
        self.notification_label.hide()
    
    def resizeEvent(self, event):
        """Handle resize event to reposition notification"""
        super().resizeEvent(event)
        if self.notification_label.isVisible():
            self._update_notification_position()

    def save_settings(self):
        """Save edited settings to config.json"""
        try:
            # Load current config to preserve all existing values
            config = load_config()
            
            # GPS Config
            try:
                probe_baud_rate = int(self.ui.edit_probe_baud_rate.text()) if self.ui.edit_probe_baud_rate.text() else config["gps_config"].get("probe_baud_rate", 115200)
                baud_rate = int(self.ui.edit_baud_rate.text()) if self.ui.edit_baud_rate.text() else config["gps_config"].get("baud_rate", 115200)
                config["gps_config"]["probe_baud_rate"] = probe_baud_rate
                config["gps_config"]["baud_rate"] = baud_rate
            except ValueError:
                logger.error("Invalid GPS baud rate values")
                self._show_notification("Error: Invalid GPS baud rate values", is_error=True)
                return
            
            # RFID Config
            config["rfid_config"]["host"] = self.ui.edit_rfid_host.text() or config["rfid_config"].get("host", "169.254.10.1")
            try:
                port = int(self.ui.edit_rfid_port.text()) if self.ui.edit_rfid_port.text() else config["rfid_config"].get("port", 5084)
                config["rfid_config"]["port"] = port
            except ValueError:
                logger.error("Invalid RFID port value")
                self._show_notification("Error: Invalid RFID port value", is_error=True)
                return
            
            # API Config
            config["api_config"]["site_id"] = self.ui.edit_site_id.text() or config["api_config"].get("site_id", "")
            try:
                record_interval_ms = int(self.ui.edit_record_interval_ms.text()) if self.ui.edit_record_interval_ms.text() else config["api_config"].get("record_interval_ms", 7000)
                max_upload_records = int(self.ui.edit_max_upload_records.text()) if self.ui.edit_max_upload_records.text() else config["api_config"].get("max_upload_records", 10)
                config["api_config"]["record_interval_ms"] = record_interval_ms
                config["api_config"]["max_upload_records"] = max_upload_records
            except ValueError:
                logger.error("Invalid API config values")
                self._show_notification("Error: Invalid API config values", is_error=True)
                return
            
            # Database Config
            try:
                max_records = int(self.ui.edit_max_records.text()) if self.ui.edit_max_records.text() else config["database_config"].get("max_records", 100)
                duplicate_detection_seconds = int(self.ui.edit_duplicate_detection_seconds.text()) if self.ui.edit_duplicate_detection_seconds.text() else config["database_config"].get("duplicate_detection_seconds", 3)
                config["database_config"]["max_records"] = max_records
                config["database_config"]["duplicate_detection_seconds"] = duplicate_detection_seconds
            except ValueError:
                logger.error("Invalid database config values")
                self._show_notification("Error: Invalid database config values", is_error=True)
                return
            
            # Filter Config - Speed
            try:
                min_speed = float(self.ui.edit_min_speed.text()) if self.ui.edit_min_speed.text() else config["filter_config"]["speed"].get("min", 1)
                max_speed = float(self.ui.edit_max_speed.text()) if self.ui.edit_max_speed.text() else config["filter_config"]["speed"].get("max", 20)
                config["filter_config"]["speed"]["min"] = min_speed
                config["filter_config"]["speed"]["max"] = max_speed
            except ValueError:
                logger.error("Invalid speed filter values")
                self._show_notification("Error: Invalid speed filter values", is_error=True)
                return
            
            # Save to file
            save_config(config)
            
            # Reload config to update global variables
            reload_config()
            
            logger.info("Settings saved successfully to config.json")
            # Show success notification
            self._show_notification("Changed data is saved", is_error=False)
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            self._show_notification(f"Error: {str(e)}", is_error=True)
