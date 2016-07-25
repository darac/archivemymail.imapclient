import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import StatsMan
import sqlite3
import email.message

test_message1 = email.message.Message()
test_message1['Subject'] = "Test subject"
test_message1['From'] = 'test@example.com'
test_message1['To'] = 'recip@example.com'
test_message1['Date'] = "01-Jan-2010"
test_message1.set_payload("This is a test message\n")


class TestStatsMan(unittest.TestCase):
    def setUp(self):
        self.Manager = StatsMan.StatsMan()

    def test_check_defaults(self):
        self.assertIsInstance(self.Manager.conn, sqlite3.Connection, 'connection')
        self.assertIsInstance(self.Manager.cur, sqlite3.Cursor, 'cursor')
        self.assertIsNone(self.Manager.imapbox, 'imapbox')
        self.assertIsNone(self.Manager.user, 'user')

        # Test imapboxes table exists
        self.assertEqual(len(self.Manager.cur.execute('''
            SELECT name
              FROM sqlite_master
             WHERE type='table' AND
                   name='imapboxes'
        ''').fetchall()), 1)

        # Test data table exists
        self.assertEqual(len(self.Manager.cur.execute('''
            SELECT name
              FROM sqlite_master
             WHERE type='table' AND
                   name='data'
        ''').fetchall()), 1)

    def test_create_box(self):
        self.Manager.newbox(user='username', box='INBOX')

        self.assertEqual(self.Manager.user, 'username')
        self.assertEqual(self.Manager.imapbox, 'INBOX')

        self.assertEqual(len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()), 1)
        

    def test_change_box(self):
        self.Manager.newbox(user='username', box='INBOX')

        self.assertEqual(self.Manager.user, 'username')
        self.assertEqual(self.Manager.imapbox, 'INBOX')
        self.assertEqual(len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()), 1)

        self.Manager.newbox(user='username', box='INBOX')

        self.assertEqual(self.Manager.user, 'username')
        self.assertEqual(self.Manager.imapbox, 'INBOX')
        self.assertEqual(len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()), 1)
        
        self.Manager.newbox(user='banana', box='INBOX')

        self.assertEqual(self.Manager.user, 'banana')
        self.assertEqual(self.Manager.imapbox, 'INBOX')
        self.assertEqual(len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()), 2)
        
        self.Manager.newbox(user='banana', box='Sent')

        self.assertEqual(self.Manager.user, 'banana')
        self.assertEqual(self.Manager.imapbox, 'Sent')
        self.assertEqual(len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()), 3)

    def test_add_without_box(self):
        self.Manager.add('test', test_message1)
