import unittest
from unittest import mock


class TestDataStorage(unittest.TestCase):
    def setUp(self):
        from utils import data_storage as ds
        self.ds = ds

    def test_init_db_creates_table(self):
        with mock.patch('utils.data_storage.sqlite3.connect') as mconn:
            conn = mock.MagicMock()
            cur = mock.MagicMock()
            mconn.return_value = conn
            conn.cursor.return_value = cur
            s = self.ds.DataStorage(use_db=True)
            self.assertTrue(s.use_db)
            cur.execute.assert_called()
            conn.commit.assert_called()

    def test_add_record_db_and_sanitize(self):
        s = self.ds.DataStorage(use_db=False)
        s.use_db = True
        s.db_connection = mock.MagicMock()
        s.db_cursor = mock.MagicMock()
        rec = [1, 'TAG', 1, -50, 1.0, 2.0, 3.0, 90.0, 'L', 'U', 123, None, None, None, None, None, None, None, None]
        s.add_record(rec)
        args = s.db_cursor.execute.call_args[0]
        sanitized = args[1]
        self.assertNotIn(None, sanitized)
        s.db_connection.commit.assert_called_once()

    def test_add_record_memory(self):
        s = self.ds.DataStorage(use_db=False)
        rec = [1, 'TAG', 1, -50, 1.0, 2.0, 3.0, 90.0, 'L', 'U', 123, '', '', '', '', '', '', '', '']
        s.add_record(rec)
        self.assertEqual(len(s.database), 1)

    def test_fetch_all_records_db_and_memory(self):
        s = self.ds.DataStorage(use_db=False)
        s.use_db = True
        s.db_cursor = mock.MagicMock()
        s.db_cursor.fetchall.return_value = [(1,)]
        self.assertEqual(s.fetch_all_records(), [(1,)])
        s.use_db = False
        s.database = [[1]]
        self.assertEqual(s.fetch_all_records(), [[1]])

    def test_prune_old_db_and_memory(self):
        s = self.ds.DataStorage(use_db=False)
        s.use_db = True
        s.db_cursor = mock.MagicMock()
        s.db_connection = mock.MagicMock()
        with mock.patch('utils.data_storage.time.time', return_value=1000):
            s.prune_old()
            s.db_cursor.execute.assert_called()
            s.db_connection.commit.assert_called()

        s.use_db = False
        with mock.patch('utils.data_storage.time.time', return_value=1000):
            current = int(1000 * 1_000_000)
            old = current - 700_000_000
            recent = current - 100_000_000
            s.database = [
                [1, 'TAG', 1, -50, 0, 0, 0, 0, '', '', old, '', '', '', '', '', '', '', ''],
                [2, 'TAG2', 1, -50, 0, 0, 0, 0, '', '', recent, '', '', '', '', '', '', '', '']
            ]
            s.prune_old()
            self.assertEqual(len(s.database), 1)


if __name__ == '__main__':
    unittest.main()


