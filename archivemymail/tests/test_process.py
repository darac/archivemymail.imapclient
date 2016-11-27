import imapclient
import pytest

import archivemymail


class myIMAPClient:
    def __init__(self, server, ssl):
        assert server == "test.example.org"
        assert ssl is True

    @staticmethod
    def login(user, password):
        assert user == 'blah'
        assert password == 'foo'

    @staticmethod
    def list_folders():
        return [("one", "two", "three")]


def myarchivebox_(mbox, user):
    assert isinstance(mbox, tuple)
    return {'have_archived': False,
            'mbox_deleted': False}


def myarchivebox_A(mbox, user):
    assert isinstance(mbox, tuple)
    return {'have_archived': True,
            'mbox_deleted': False}


def myarchivebox_D(mbox, user):
    assert isinstance(mbox, tuple)
    return {'have_archived': False,
            'mbox_deleted': True}


def myarchivebox_AD(mbox, user):
    assert isinstance(mbox, tuple)
    return {'have_archived': True,
            'mbox_deleted': True}


def mylearnbox(mbox):
    assert mbox is 'three'


class mocksubprocess:
    def __init__(self, cmd, stdin=None, input=None, check=False):
        assert 'sa-learn' in cmd
        assert '--dbpath' in cmd
        assert '--sync' in cmd

        assert stdin is None
        assert check is True


@pytest.mark.parametrize("patch,dry_run,wantlearn", [
    (myarchivebox_, False, False),
    (myarchivebox_A, False, False),
    (myarchivebox_D, False, False),
    (myarchivebox_AD, False, False),
    (myarchivebox_, False, True),
    (myarchivebox_A, False, True),
    (myarchivebox_D, False, True),
    (myarchivebox_AD, False, True),
    (myarchivebox_, True, False),
    (myarchivebox_A, True, False),
    (myarchivebox_D, True, False),
    (myarchivebox_AD, True, False),
    (myarchivebox_, True, True),
    (myarchivebox_A, True, True),
    (myarchivebox_D, True, True),
    (myarchivebox_AD, True, True),
])
def test_process(caplog, monkeypatch, patch, dry_run, wantlearn):
    account = 'blah:foo'
    archivemymail.config = archivemymail.Config()
    archivemymail.config.server = 'test.example.org'
    archivemymail.config.do_learning = wantlearn
    archivemymail.config.dry_run = dry_run
    archivemymail.config.bayes_dir = '.'

    monkeypatch.setattr(imapclient, 'IMAPClient', myIMAPClient)
    monkeypatch.setattr('archivemymail.IMAPMan.IMAPClient', myIMAPClient)
    monkeypatch.setattr(archivemymail, "archivebox", patch)
    monkeypatch.setattr(archivemymail, "learnbox", mylearnbox)
    monkeypatch.setattr('archivemymail.wrappers.subprocess', mocksubprocess)

    # UUT
    archivemymail.process(account)

    assert "Archiving mail for blah" in caplog.text
