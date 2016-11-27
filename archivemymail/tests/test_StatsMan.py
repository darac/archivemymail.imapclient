import sqlite3
import subprocess

import pytest

import archivemymail
from testdata import *


class TestStatsMan:
    @classmethod
    def setup_class(cls):
        cls.Manager = archivemymail.StatsManClass()

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
        self.Manager.new_box(user='username', box='INBOX')

        assert self.Manager.user == 'username'
        assert self.Manager.imapbox == 'INBOX'

        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 1

    def test_change_box(self):
        self.Manager.new_box(user='username', box='INBOX')

        assert self.Manager.user == 'username'
        assert self.Manager.imapbox == 'INBOX'
        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 1

        self.Manager.new_box(user='username', box='INBOX')

        assert self.Manager.user == 'username'
        assert self.Manager.imapbox == 'INBOX'
        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 1

        self.Manager.new_box(user='banana', box='INBOX')

        assert self.Manager.user == 'banana'
        assert self.Manager.imapbox == 'INBOX'
        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 2

        self.Manager.new_box(user='banana', box='Sent')

        assert self.Manager.user == 'banana'
        assert self.Manager.imapbox == 'Sent'
        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 3

        # Back to the start
        self.Manager.new_box(user='username', box='INBOX')

        assert self.Manager.user == 'username'
        assert self.Manager.imapbox == 'INBOX'
        assert len(self.Manager.cur.execute('''
            SELECT user, imapbox FROM imapboxes
        ''').fetchall()) == 3

    def test_add_without_box(self):
        self.Manager = archivemymail.StatsManClass()
        assert self.Manager.imapbox is None
        assert self.Manager.user is None
        with pytest.raises(RuntimeError):
            self.Manager.add(message=test_message1, mbox='test')
        assert self.Manager.user is None
        assert self.Manager.imapbox != 'test'

        # That failed, but if we register a user first,
        # we should be able to auto-add a box to that user

        self.Manager.new_box(user='user', box='INBOX')
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

    @pytest.mark.parametrize('dry_run', [True, False])
    def test_summarise(self, monkeypatch, dry_run):
        class Pope:
            def __init__(self, args, stdin=None):
                assert len(args) == 3
                # assert stdin == subprocess.PIPE

            @staticmethod
            def communicate(str):
                try:
                    assert b'Subject: archivemymail' in str
                except TypeError:
                    assert 'Subject: archivemymail' in str

            @staticmethod
            def check_returncode():
                pass

        monkeypatch.setattr(subprocess, 'Popen', Pope)

        archivemymail.config.dry_run = dry_run

        self.Manager = archivemymail.StatsManClass()
        self.Manager.new_box(user='tom', box='INBOX')
        self.Manager.add(mbox='INBOX.bz2', message=test_message1)
        self.Manager.add(mbox='INBOX.bz2', message=test_message1)
        self.Manager.add(mbox='INBOX2.bz2', message=test_message1)
        self.Manager.new_box(user='bill', box='INBOX')
        self.Manager.add(mbox='INBOX.bz2', message=test_message1)
        self.Manager.add(mbox='INBOX2.bz2', message=test_message1)
        self.Manager.new_box(user='bill', box='Sent')
        self.Manager.add(mbox='Sent.bz2', message=test_message2)
        self.Manager.add(mbox='Sent.bz2', message=test_message2)
        self.Manager.summarise()
