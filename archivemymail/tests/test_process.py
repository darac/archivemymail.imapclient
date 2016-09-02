import pytest
import imapclient

import archivemymail

class myIMAPClient():
    def __init__(self, server, ssl):
        assert server == "test.example.org"
        assert ssl == True

    def login(self, user, password):
        assert user == 'blah'
        assert password == 'foo'

    def list_folders(self):
        return [("one", "two", "three")]

def myarchivebox_(mbox, user):
    assert isinstance(mbox, tuple)
    return 0

def myarchivebox_A(mbox, user):
    assert isinstance(mbox, tuple)
    return archivemymail.HAVE_ARCHIVED

def myarchivebox_D(mbox, user):
    assert isinstance(mbox, tuple)
    return archivemymail.MBOX_DELETED

def myarchivebox_AD(mbox, user):
    assert isinstance(mbox, tuple)
    return archivemymail.HAVE_ARCHIVED | archivemymail.MBOX_DELETED

def mylearnbox(mbox):
    assert isinstance(mbox, tuple)

def mydontlearn(mbox):
    assert False

@pytest.mark.parametrize("patch,wantlearn,dolearn", [
    (myarchivebox_,   False, False),
    (myarchivebox_A,  False, False),
    (myarchivebox_D,  False, False),
    (myarchivebox_AD, False, False),
    (myarchivebox_,   True,  False),
    (myarchivebox_A,  True,  True),
    (myarchivebox_D,  True,  False),
    (myarchivebox_AD, True,  False),
    ])
def test_process(caplog, monkeypatch, patch, wantlearn, dolearn):

    account = 'blah:foo'
    archivemymail.config = archivemymail.Config()
    archivemymail.config.server = 'test.example.org'
    archivemymail.config.do_learning = wantlearn
    
    monkeypatch.setattr(imapclient, 'IMAPClient', myIMAPClient)
    monkeypatch.setattr(archivemymail, "archivebox", patch)
    if dolearn:
        monkeypatch.setattr(archivemymail, "learnbox", mylearnbox)
    else:
        monkeypatch.setattr(archivemymail, "learnbox", mydontlearn)

    # UUT
    archivemymail.process(account)
    
    assert "Archiving mail for blah" in caplog.text

