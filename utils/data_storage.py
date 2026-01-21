import sqlite3
import time
from typing import List, Tuple, Optional

from utils.common import find_smallest_available_id
from utils.logger import logger
from settings import DATABASE_FILE


class DataStorage:

    def __init__(self, use_db: bool, max_records: int = 100):
        self.use_db = use_db
        self.max_records = max_records
        self.database: List[list] = []
        self.db_connection: Optional[sqlite3.Connection] = None
        self.db_cursor: Optional[sqlite3.Cursor] = None
        if self.use_db:
            self._init_db()

    def _init_db(self):
        self.db_connection = sqlite3.connect(DATABASE_FILE)
        self.db_cursor = self.db_connection.cursor()
        self.db_cursor.execute('''
                            CREATE TABLE IF NOT EXISTS records (
                                id INTEGER PRIMARY KEY,
                                rfidTag TEXT NOT NULL,
                                antenna INTEGER NOT NULL,
                                RSSI INTEGER NOT NULL,
                                latitude REAL NOT NULL,
                                longitude REAL NOT NULL,
                                speed REAL NOT NULL,
                                heading REAL NOT NULL,
                                locationCode TEXT NOT NULL,
                                username TEXT NOT NULL,
                                tag1 TEXT NOT NULL,
                                value1 TEXT NOT NULL,
                                tag2 TEXT NOT NULL,
                                value2 TEXT NOT NULL,
                                tag3 TEXT NOT NULL,
                                value3 TEXT NOT NULL,
                                tag4 TEXT NOT NULL,
                                value4 TEXT NOT NULL,
                                timestamp INTEGER NOT NULL
                            )
                        ''')
        self.db_connection.commit()

    def close(self):
        if self.db_connection:
            self.db_connection.close()
            self.db_connection = None
            self.db_cursor = None

    def add_record(self, record_list):
        if self.use_db:
            assert self.db_cursor and self.db_connection
            # Ensure NOT NULL columns never receive None
            record_list = ["" if v is None else v for v in record_list]
            self.db_cursor.execute('''
                INSERT INTO records
                (id, rfidTag, antenna, RSSI, latitude, longitude, speed, heading, locationCode, username,
                timestamp, tag1, value1, tag2, value2, tag3, value3, tag4, value4)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', record_list)
            self.db_connection.commit()
            # Immediately prune old records to maintain max_records limit
            self.prune_old()
        else:
            self.database.append(record_list)
            # Immediately prune old records to maintain max_records limit
            if len(self.database) > self.max_records:
                self.database = self.database[-self.max_records:]

    def fetch_all_records(self) -> List[Tuple]:
        if self.use_db:
            assert self.db_cursor
            self.db_cursor.execute('''
                SELECT id, rfidTag, antenna, RSSI, latitude, longitude, speed, heading,
                locationCode, username, tag1, value1, tag2, value2, tag3, value3, tag4, value4
                FROM records
                ORDER BY timestamp ASC
            ''')
            return self.db_cursor.fetchall()
        else:
            return self.database

    def prune_old(self):
        """Delete records beyond the max_records limit, keeping only the newest records"""
        if self.use_db:
            assert self.db_cursor and self.db_connection
            # Count total records
            self.db_cursor.execute('SELECT COUNT(*) FROM records')
            total_count = self.db_cursor.fetchone()[0]
            
            # If we exceed the limit, delete the oldest records
            if total_count > self.max_records:
                records_to_delete = total_count - self.max_records
                self.db_cursor.execute('''
                    DELETE FROM records
                    WHERE id IN (
                        SELECT id FROM records
                        ORDER BY timestamp ASC
                        LIMIT ?
                    )
                ''', [records_to_delete])
                self.db_connection.commit()
        else:
            # For in-memory storage, keep only the last max_records
            if len(self.database) > self.max_records:
                self.database = self.database[-self.max_records:]

    def delete_uploaded_records(self, record_ids: List[int]):
        """Delete specific records by their IDs after successful upload"""
        if not record_ids:
            return
        
        if self.use_db:
            assert self.db_cursor and self.db_connection
            # Delete records with the specified IDs
            placeholders = ','.join('?' for _ in record_ids)
            self.db_cursor.execute(f'DELETE FROM records WHERE id IN ({placeholders})', record_ids)
            self.db_connection.commit()
            logger.debug(f"Deleted {len(record_ids)} uploaded record(s) from database")
        else:
            # For in-memory storage, filter out records with matching IDs
            initial_count = len(self.database)
            self.database = [rec for rec in self.database if rec[0] not in record_ids]
            deleted_count = initial_count - len(self.database)
            if deleted_count > 0:
                logger.debug(f"Deleted {deleted_count} uploaded record(s) from memory")


