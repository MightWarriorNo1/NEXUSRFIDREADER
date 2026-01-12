import unittest
from unittest import mock
import platform


class TestGPS(unittest.TestCase):
    def setUp(self):
        from utils import gps as gps_module
        self.gps_module = gps_module
        self.PORT = "COM3" if platform.system() == "Windows" else "/dev/ttyUSB0"

    def test_gps_init(self):
        gps = self.gps_module.GPS(port=self.PORT, baud_rate=115200, current_status=False)
        self.assertEqual(gps.port, self.PORT)
        self.assertEqual(gps.baud_rate, 115200)
        self.assertFalse(gps.connectivity)
        self.assertIsNone(gps._ser)
        self.assertEqual(gps._data, {})
        self.assertEqual(gps._sdata, [0, 0])

    def test_connect_success(self):
        gps = self.gps_module.GPS(port=self.PORT, baud_rate=115200)
        with mock.patch('utils.gps.serial.Serial') as mock_serial:
            mock_ser = mock.MagicMock()
            mock_serial.return_value = mock_ser
            result = gps._connect()
            self.assertEqual(result, mock_ser)
            self.assertTrue(gps.connectivity)

    def test_connect_failure(self):
        gps = self.gps_module.GPS(port=self.PORT, baud_rate=115200, current_status=True)
        with mock.patch('utils.gps.serial.Serial', side_effect=self.gps_module.serial.SerialException("Port not found")):
            result = gps._connect()
            self.assertIsNone(result)
            self.assertFalse(gps.connectivity)

    def test_read_serial_data_valid_nmea(self):
        gps = self.gps_module.GPS(port=self.PORT, baud_rate=115200)
        gps._ser = mock.MagicMock()
        gps._ser.in_waiting = 100
        with mock.patch('utils.gps.pynmea2.parse') as mock_parse:
            mock_msg = mock.MagicMock()
            mock_msg.fields = [("Latitude", "lat"), ("Longitude", "lon"), ("Speed", "spd_over_grnd"), ("Course", "true_course")]
            mock_msg.lat = "3342.1234"
            mock_msg.lon = "96884.5678"
            mock_msg.spd_over_grnd = 5.5
            mock_msg.true_course = 45.0
            mock_parse.return_value = mock_msg
            gps._ser.readline.return_value = b"$GPRMC,123456.00,A,3342.1234,N,96884.5678,W,5.5,45.0,200920,1.2,E,A*12\r\n"
            gps.read_serial_data()
            self.assertEqual(gps._data["lat"], "3342.1234")
            self.assertEqual(gps._data["lon"], "96884.5678")
            self.assertAlmostEqual(gps._sdata[0], 6.33, places=2)  # 5.5 knots * 1.15078 = 6.33 mph
            self.assertEqual(gps._sdata[1], 45.0)

    def test_read_serial_data_invalid_nmea(self):
        gps = self.gps_module.GPS(port=self.PORT, baud_rate=115200)
        gps._ser = mock.MagicMock()
        gps._ser.in_waiting = 100
        with mock.patch('utils.gps.pynmea2.parse', side_effect=self.gps_module.pynmea2.ParseError("Invalid", "INVALID")):
            gps._ser.readline.return_value = b"INVALID_SENTENCE\r\n"
            gps.read_serial_data()
            self.assertEqual(gps._data, {})
            self.assertEqual(gps._sdata, [0, 0])

    def test_run_connect_loop(self):
        gps = self.gps_module.GPS(port=self.PORT, baud_rate=115200)
        with mock.patch.object(gps, '_connect', side_effect=[None, mock.MagicMock()]) as mock_connect, \
             mock.patch.object(gps._b_stop, 'is_set', side_effect=[False, False, True]), \
             mock.patch.object(gps._b_stop, 'wait'):
            gps.run()
            self.assertEqual(mock_connect.call_count, 2)

    def test_run_connection_monitoring(self):
        gps = self.gps_module.GPS(port=self.PORT, baud_rate=115200)
        gps._ser = mock.MagicMock()
        gps.connectivity = True
        def raise_and_stop():
            gps._b_stop.set()
            raise Exception("Connection lost")
        with mock.patch.object(gps, 'read_serial_data', side_effect=raise_and_stop), \
             mock.patch('utils.gps.time.sleep', return_value=None):
            import threading
            t = threading.Thread(target=gps.run, daemon=True)
            t.start()
            t.join(timeout=0.5)
            if t.is_alive():
                gps._b_stop.set()
                t.join(timeout=0.5)
            self.assertFalse(gps.connectivity)
            self.assertIsNone(gps._ser)

    def test_stop(self):
        gps = self.gps_module.GPS(port=self.PORT, baud_rate=115200)
        gps._ser = mock.MagicMock()
        gps._ser.is_open = True
        with mock.patch.object(gps._b_stop, 'set') as mock_set, \
             mock.patch.object(gps, 'wait') as mock_wait:
            gps.stop()
            mock_set.assert_called_once()
            mock_wait.assert_called_once_with(1)
            self.assertIsNone(gps._ser)

    def test_close_serial(self):
        gps = self.gps_module.GPS(port=self.PORT, baud_rate=115200)
        mock_ser = mock.MagicMock()
        mock_ser.is_open = True
        gps._ser = mock_ser
        gps._close_serial()
        mock_ser.close.assert_called_once()
        self.assertIsNone(gps._ser)

    def test_close_serial_already_closed(self):
        gps = self.gps_module.GPS(port=self.PORT, baud_rate=115200)
        mock_ser = mock.MagicMock()
        mock_ser.is_open = False
        gps._ser = mock_ser
        gps._close_serial()
        mock_ser.close.assert_not_called()
        self.assertIsNone(gps._ser)

    def test_is_alive_and_getters(self):
        gps = self.gps_module.GPS(port=self.PORT, baud_rate=115200)
        self.assertTrue(gps.is_alive())
        gps._b_stop.set()
        self.assertFalse(gps.is_alive())
        gps._data = {"lat": "1", "lon": "2"}
        gps._sdata = [1.2, 34.0]
        self.assertEqual(gps.get_data(), {"lat": "1", "lon": "2"})
        self.assertEqual(gps.get_sdata(), [1.2, 34.0])


if __name__ == "__main__":
    unittest.main()