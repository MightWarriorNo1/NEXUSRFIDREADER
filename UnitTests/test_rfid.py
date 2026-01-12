import unittest
from unittest import mock


class TestRFID(unittest.TestCase):
    def setUp(self):
        from utils import rfid as r
        self.r = r

    def test_parse_args_from_settings_defaults(self):
        args = self.r._parse_args_from_settings({})
        self.assertEqual(args['every_n'], 1)
        self.assertEqual(args['antennas'], '1')
        self.assertEqual(args['port'], self.r.LLRP_DEFAULT_PORT)

    def test_convert_to_unicode(self):
        self.assertEqual(self.r._convert_to_unicode(b'abc'), 'abc')
        self.assertEqual(self.r._convert_to_unicode({'k': b'v'})['k'], 'v')
        self.assertEqual(self.r._convert_to_unicode([b'a', 'b'])[0], 'a')

    def test_init_sets_reader(self):
        with mock.patch('utils.rfid.LLRPReaderClient') as mclient, \
             mock.patch('utils.rfid.LLRPReaderConfig') as mconfig:
            rf = self.r.RFID()
            self.assertIsNotNone(rf.reader)
            mclient.assert_called()
            mconfig.assert_called()

    def test_set_reader_reconfigures(self):
        with mock.patch('utils.rfid.LLRPReaderClient') as mclient, \
             mock.patch('utils.rfid.LLRPReaderConfig') as mconfig:
            rf = self.r.RFID()
            rf._set_reader('1.2.3.4', True)
            self.assertEqual(rf.host, '1.2.3.4')
            self.assertTrue(rf.connectivity)
            mclient.assert_called()

    def test_tag_seen_callback_updates_state(self):
        rf = self.r.RFID()
        rf.tag_seen_callback(None, [{'EPC-96': '123'}])
        self.assertEqual(rf.tag_data[0]['EPC-96'], '123')

    def test_run_connect_flow(self):
        with mock.patch('utils.rfid.LLRPReaderClient') as mclient, \
             mock.patch('utils.rfid.LLRPReaderConfig'):
            rf = self.r.RFID()
            rf.reader = mock.MagicMock()
            rf.reader.connect.side_effect = [Exception('x'), None]
            with mock.patch.object(rf._b_stop, 'is_set', side_effect=[False, False, True]):
                rf.run()
                # reader.connect should have been called twice total (failure then success)
                self.assertEqual(rf.reader.connect.call_count, 2)

    def test_run_ping_monitoring(self):
        with mock.patch('utils.rfid.LLRPReaderClient') as mclient, \
             mock.patch('utils.rfid.LLRPReaderConfig'), \
             mock.patch('utils.rfid.ping', return_value=None):
            rf = self.r.RFID()
            rf.reader = mock.MagicMock()
            rf.connectivity = True
            # First False consumed by connect loop, second False allows one main-loop iteration, then stop
            with mock.patch.object(rf._b_stop, 'is_set', side_effect=[False, False, True]):
                rf.run()
                # connectivity should be marked False when ping fails
                self.assertFalse(rf.connectivity)

    def test_stop_disconnects(self):
        with mock.patch('utils.rfid.LLRPReaderClient.disconnect_all_readers') as disc:
            rf = self.r.RFID()
            with mock.patch.object(rf, 'wait') as w:
                rf.stop()
                w.assert_called()
                disc.assert_called()


if __name__ == '__main__':
    unittest.main()


