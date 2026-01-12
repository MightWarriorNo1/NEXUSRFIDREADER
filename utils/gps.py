import threading
import time

import serial
import pynmea2

from PySide6.QtCore import Signal, QThread

from settings import GPS_CONFIG
from utils.logger import logger


class GPS(QThread):

    sig_msg = Signal(bool)

    def __init__(self, port, baud_rate, current_status=False):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self._ser = None
        self._b_stop = threading.Event()
        self._data = {}
        self._sdata = [0, 0]
        self._last_data_timestamp = None  # Track when GPS data was last received
        self.connectivity = current_status

    def _connect(self):
        try:
            _ser = serial.Serial(port=self.port, baudrate=self.baud_rate, timeout=1, write_timeout=1)
            if self.connectivity is False:
                self.connectivity = True
                self.sig_msg.emit(True)
            return _ser
        except serial.SerialException:
            if self.connectivity is True:
                self.connectivity = False
                self.sig_msg.emit(False)
            return None

    def read_serial_data(self):
        buffer = self._ser.in_waiting
        if buffer < 80:
            time.sleep(.2)
        line = self._ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith('$GPRMC') or line.startswith('$GNRMC'):
            try:
                msg = pynmea2.parse(line)
                for field in msg.fields:
                    label, attr = field[:2]
                    value = getattr(msg, attr)
                    self._data[attr] = value
                speed_knots = msg.spd_over_grnd if msg.spd_over_grnd is not None else 0
                course_degrees = msg.true_course if msg.true_course is not None else 0
                self._sdata = [speed_knots * 1.15078, course_degrees]
                # Update timestamp when GPS data is successfully parsed
                self._last_data_timestamp = int(time.time() * 1_000_000)
                # logger.debug(f"GPS data parsed: lat={self._data.get('lat', 'N/A')}, lon={self._data.get('lon', 'N/A')}, speed={speed_knots}")
                pass
            except pynmea2.ParseError as e:
                logger.debug(f"GPS parse error: {e}")
                self._data = {}
                self._sdata = [0, 0]
        elif line.startswith('$G'):
            # Log other GPS sentences for debugging
            # logger.debug(f"GPS sentence: {line[:50]}...")
            pass

    def run(self):
        self._ser = self._connect()
        while self._ser is None and not self._b_stop.is_set():
            self._ser = self._connect()

        while not self._b_stop.is_set():
            if self._ser is None:
                self._ser = self._connect()
                time.sleep(.1)
            else:
                try:
                    self.read_serial_data()
                    if self.connectivity is False:
                        self.connectivity = True
                        self.sig_msg.emit(True)
                except Exception:
                    self._data = {}
                    self._sdata = [0, 0]
                    self._ser = None
                    if self.connectivity is True:
                        self.connectivity = False
                        self.sig_msg.emit(False)

    def stop(self):
        self._b_stop.set()
        self.wait(1)
        self._close_serial()

    def _close_serial(self):
        if self._ser and self._ser.is_open:
            self._ser.close()
        self._ser = None

    def is_alive(self):
        return not self._b_stop.is_set()

    def get_data(self):
        return self._data

    def get_sdata(self):
        return self._sdata

    def get_data_timestamp(self):
        """Get the timestamp when GPS data was last received"""
        return self._last_data_timestamp


