import os
import sys
import sqlite3
import email.message
import pytest

import archivemymail

test_message1 = email.message.Message()
test_message1['Subject'] = 'Test subject'
test_message1['From'] = 'test@example.com'
test_message1['To'] = 'recip@example.com'
test_message1['Date'] = '01-Jan-2010'
test_message1.set_payload('This is a test message\n')

class TestStatsMan():

    @classmethod
    def setup_class(self):
        self.Manager = archivemymail.StatsManClass()

    def test_check_defaults(self):
        assert isinstance(self.Manager.conn, sqlite3.Connection)
        assert isinstance(self.Manager.cur, sqlite3.Cursor)
        assert self.Manager.imapbox is None
        assert self.Manager.user is None

        # Test imapboxes table exists
        assert len(self.Manager.cur.execute('''
            SELECT name
              FROM sqlite_master
             WHERE type='table' AND
                   name='imapboxes'
        ''').fetchall()) == 1

        # Test data table exists
        assert len(self.Manager.cur.execute('''
            SELECT name
              FROM sqlite_master
             WHERE type='table' AND
                   name='data'
        ''').fetchall()) == 1

    def test_create_box(self):
        self.Manager.newbox(user='username', box='INBOX')

        assert self.Manager.user == 'username'
        assert self.Manager.imapbox == 'INBOX'

        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 1

    def test_change_box(self):
        self.Manager.newbox(user='username', box='INBOX')

        assert self.Manager.user == 'username'
        assert self.Manager.imapbox == 'INBOX'
        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 1

        self.Manager.newbox(user='username', box='INBOX')

        assert self.Manager.user == 'username'
        assert self.Manager.imapbox == 'INBOX'
        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 1

        self.Manager.newbox(user='banana', box='INBOX')

        assert self.Manager.user == 'banana'
        assert self.Manager.imapbox == 'INBOX'
        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 2

        self.Manager.newbox(user='banana', box='Sent')

        assert self.Manager.user == 'banana'
        assert self.Manager.imapbox == 'Sent'
        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 3

        # Back to the start
        self.Manager.newbox(user='username', box='INBOX')

        assert self.Manager.user == 'username'
        assert self.Manager.imapbox == 'INBOX'
        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 3


    def test_add_without_box(self):
        self.Manager = archivemymail.StatsMan.StatsManClass()
        assert self.Manager.imapbox is None
        assert self.Manager.user is None
        with pytest.raises(RuntimeError):
            self.Manager.add(message=test_message1, box='test')
        assert self.Manager.user is None
        assert self.Manager.imapbox != 'test'

        # That failed, but if we register a user first,
        # we should be able to auto-add a box to that user

        self.Manager.newbox(user='user', box='INBOX')
        assert self.Manager.user == 'user'
        assert self.Manager.imapbox == 'INBOX'
        self.Manager.add(message=test_message1, box='test')
        assert self.Manager.user == 'user'
        assert self.Manager.imapbox == 'test'
        
    def test_text_header(self):
        test_data = [
            ["", None, "\n\n"],
            ["1", None, "1\n=\n"],
            ["blah blah", None, "blah blah\n=========\n"],
            ["blah blah", '+', "blah blah\n+++++++++\n"],
            ["blah blah", 'foo', "blah blah\nfoofoofoofoofoofoofoofoofoo\n"],
        ]

        for t in test_data:
            if t[1] is None:
                assert self.Manager.text_header(t[0]) == t[2]
            else:
                assert self.Manager.text_header(t[0], t[1]) == t[2]

