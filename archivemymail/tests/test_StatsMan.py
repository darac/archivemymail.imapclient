import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import StatsMan
import sqlite3


class TestStatsMan(unittest.TestCase):
    def setUp(self):
        self.Manager = StatsMan.StatsMan()

    def test_check_defaults(self):
        self.assertIsInstance(self.Manager.conn, sqlite3.Connection, 'connection')
        self.assertIsInstance(self.Manager.cur, sqlite3.Cursor, 'cursor')
        self.assertIsNone(self.Manager.imapbox, 'imapbox')
        self.assertIsNone(self.Manager.user, 'user')

        # Test imapboxes table exists
        self.assertEquals(len(self.Manager.cur.execute('''
            SELECT name
              FROM sqlite_master
             WHERE type='table' AND
                   name='imapboxes'
        ''').fetchall()), 1)

        # Test data table exists
        self.assertEquals(len(self.Manager.cur.execute('''
            SELECT name
              FROM sqlite_master
             WHERE type='table' AND
                   name='data'
        ''').fetchall()), 1)

    def test_create_box(self):
        self.Manager.newbox(user='username', box='INBOX')

        self.assertEquals(self.Manager.user, 'username')
        self.assertEquals(self.Manager.imapbox, 'INBOX')
