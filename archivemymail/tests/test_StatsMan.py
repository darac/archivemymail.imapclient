import os
import sys
import sqlite3
import email.message
import pytest
import subprocess

import archivemymail

test_message1 = email.message.Message()
test_message1['Subject'] = 'Test subject'
test_message1['From'] = 'test@example.com'
test_message1['To'] = 'recip@example.com'
test_message1['Date'] = '01-Jan-2010'
test_message1.set_payload('This is a test message\n')

test_message2 = email.message.Message()
test_message2['Subject'] = "GewSt:=?UTF-8?B?IFdlZ2ZhbGwgZGVyIFZvcmzDpHVmaWdrZWl0?="
test_message2['From'] = 'John Doe <j@example.org>'
test_message2['To'] = 'bill@example.org'
test_message2.set_payload("Another test\n")

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
            self.Manager.add(message=test_message1, mbox='test')
        assert self.Manager.user is None
        assert self.Manager.imapbox != 'test'

        # That failed, but if we register a user first,
        # we should be able to auto-add a box to that user

        self.Manager.newbox(user='user', box='INBOX')
        assert self.Manager.user == 'user'
        assert self.Manager.imapbox == 'INBOX'
        self.Manager.add(message=test_message1, mbox='test')
        assert self.Manager.user == 'user'
        assert self.Manager.imapbox == 'INBOX'
        
    def test_text_header(self):
        test_data = [
            ["", None, "\n"],
            ["1", None, "1\n="],
            ["blah blah", None, "blah blah\n========="],
            ["blah blah", '+', "blah blah\n+++++++++"],
            ["blah blah", 'foo', "blah blah\n========="],
        ]

        for t in test_data:
            if t[1] is None:
                assert self.Manager.text_header(t[0]) == t[2]
            else:
                assert self.Manager.text_header(t[0], t[1]) == t[2]

    def test_summarise(self, monkeypatch):
        class Pope():
            def __init__(self, args, stdin=None):
                assert len(args) == 3
                assert stdin == subprocess.PIPE
            def communicate(self, str):
                assert 'Subject: archivemymail' in str
        monkeypatch.setattr(subprocess, 'Popen', Pope)


        self.Manager = archivemymail.StatsMan.StatsManClass()
        self.Manager.newbox(user='tom', box='INBOX')
        self.Manager.add(mbox='INBOX.bz2', message=test_message1)
        self.Manager.add(mbox='INBOX.bz2', message=test_message1)
        self.Manager.add(mbox='INBOX2.bz2', message=test_message1)
        self.Manager.newbox(user='bill', box='INBOX')
        self.Manager.add(mbox='INBOX.bz2', message=test_message1)
        self.Manager.add(mbox='INBOX2.bz2', message=test_message1)
        self.Manager.newbox(user='bill', box='Sent')
        self.Manager.add(mbox='Sent.bz2', message=test_message2)
        self.Manager.add(mbox='Sent.bz2', message=test_message2)
        self.Manager.summarise()
