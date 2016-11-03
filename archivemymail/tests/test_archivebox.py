import pytest
import imapclient
import datetime
import mailbox

import archivemymail
import testdata

class mockserver():
    def __init__(self, num_messages):
        self.num_messages = num_messages
        self.curr_message = 0

    def select_folder(self, box):
        assert box == 'box' or box == 'inbox'
        
    def search(self, searchterm):
        if 'OLD' in searchterm:
            assert 'OLD' in searchterm
            assert 'BEFORE' in searchterm
        else:
            assert 'NOT' in searchterm
            assert 'DELETED' in searchterm
        return [i for i in range(self.num_messages)]

    def fetch(self, num, searchterms):
        assert num >= 0
        assert 'FLAGS' in searchterms
        assert 'RFC822' in searchterms
        assert 'INTERNALDATE' in searchterms
        msg = {}
        if num == 1:
            # No flags on the first message
            msg['FLAGS'] = ()
        else:
            msg['FLAGS'] = (imapclient.RECENT, imapclient.SEEN, imapclient.DELETED, imapclient.FLAGGED, imapclient.ANSWERED)

        try:
            msg['RFC822'] = testdata.test_message2.as_bytes()
        except AttributeError:
            msg['RFC822'] = testdata.test_message2.as_string()
        msg['INTERNALDATE'] = datetime.datetime(2016,11,3,15,12)
        self.curr_message = num

        return {num: msg}

    def delete_messages(self, msg_num):
        assert msg_num == self.curr_message

    def close_folder(self):
        pass

    def delete_folder(self, mbox_name):
        assert mbox_name == 'box'

class mockmboxman():
    def __init__(self, user, tdir, statsman, dry_run, compression):
        pass

    def set_box(self, mboxname, is_spam=False):
        assert is_spam == False
        assert mboxname.endswith('box/2016/11')

    def add(self, message):
        assert isinstance(message, mailbox.mboxMessage)

class mockprogress():
    def __init__(self, length):
        pass

    def log(self, message, box, is_spam=False):
        assert is_spam == False
        assert box.endswith('box/2016/11')
        assert isinstance(message, mailbox.mboxMessage)

class mocksubprocess():
    def __init__(self, cmd, stdin=None, input=None, check=False):
        assert 'sa-learn' in cmd
        assert '--spam' in cmd or '--ham' in cmd
        assert '--no-sync' in cmd
        assert '--dbpath' in cmd

        assert stdin == None
        assert check == True

@pytest.mark.parametrize('boxname', [
    ('Archive'),
    ('_ARCHIVE'),
])
def test_archivebox_archive(boxname):
    mbox = ([], '/', boxname)
    user = 'joe'

    d = archivemymail.archivebox(mbox, user)

    assert d['have_archived'] == False
    assert d['mbox_deleted'] == False


def test_archivebox_unselectable():
    mbox = ([b'\NoSelect'], '/', 'box')
    user = 'joe'

    d = archivemymail.archivebox(mbox, user)

    assert d['have_archived'] == False
    assert d['mbox_deleted'] == False

@pytest.mark.parametrize('tdir', [
    ('/bob'),
    ('~/bob'),
    ('/home/%u'),
])
def test_archivevbox_empty_dryrun(monkeypatch, caplog, tdir):
    archivemymail.config = archivemymail.Config()
    archivemymail.config.target_dir = tdir
    
    mbox = ([], '/', 'box')
    user = 'joe'

    monkeypatch.setattr("archivemymail.mboxman", mockmboxman)
    monkeypatch.setattr("archivemymail.progress.Progress", mockprogress)
    archivemymail.server = mockserver(0)
    archivemymail.config.dry_run = True
    archivemymail.config.compression = "gz"

    d = archivemymail.archivebox(mbox, user)

    assert d['have_archived'] == False
    assert d['mbox_deleted'] == True
    assert "===== box =====" in caplog.text
    assert "0 messages to archive" in caplog.text
    assert "Would delete now-empty folder box" in caplog.text

@pytest.mark.parametrize('tdir', [
    ('/bob'),
    ('~/bob'),
    ('/home/%u'),
])
def test_archivevbox_empty(monkeypatch, caplog, tdir):
    archivemymail.config = archivemymail.Config()
    archivemymail.config.target_dir = tdir
    
    mbox = ([], '/', 'box')
    user = 'joe'

    monkeypatch.setattr("archivemymail.mboxman", mockmboxman)
    monkeypatch.setattr("archivemymail.progress.Progress", mockprogress)
    archivemymail.server = mockserver(0)
    archivemymail.config.dry_run = False
    archivemymail.config.compression = "gz"

    d = archivemymail.archivebox(mbox, user)

    assert d['have_archived'] == False
    assert d['mbox_deleted'] == True
    assert "===== box =====" in caplog.text
    assert "0 messages to archive" in caplog.text
    assert "Deleting now-empty folder %s" in caplog.text

@pytest.mark.parametrize('tdir', [
    ('/bob'),
    ('~/bob'),
    ('/home/%u'),
])
def test_archivevbox_nonempty_dryrun(monkeypatch, caplog, tdir):
    archivemymail.config = archivemymail.Config()
    archivemymail.config.target_dir = tdir
    
    mbox = ([], '/', 'box')
    user = 'joe'

    monkeypatch.setattr("archivemymail.mboxman", mockmboxman)
    monkeypatch.setattr("archivemymail.progress.Progress", mockprogress)
    archivemymail.server = mockserver(2)
    archivemymail.config.dry_run = True
    archivemymail.config.compression = "gz"
    archivemymail.config.do_learning = False

    d = archivemymail.archivebox(mbox, user)

    assert d['have_archived'] == True
    assert d['mbox_deleted'] == False
    assert "===== box =====" in caplog.text
    assert "2 messages to archive" in caplog.text

@pytest.mark.parametrize('tdir', [
    ('/bob'),
    ('~/bob'),
    ('/home/%u'),
])
def test_archivevbox_nonempty_nolearn(monkeypatch, caplog, tdir):
    archivemymail.config = archivemymail.Config()
    archivemymail.config.target_dir = tdir
    
    mbox = ([], '/', 'box')
    user = 'joe'

    monkeypatch.setattr("archivemymail.mboxman", mockmboxman)
    monkeypatch.setattr("archivemymail.progress.Progress", mockprogress)
    monkeypatch.setattr("archivemymail.wrappers.subprocess", mocksubprocess)
    archivemymail.server = mockserver(2)
    archivemymail.config.dry_run = False
    archivemymail.config.compression = "xz"
    archivemymail.config.do_learning = False
    archivemymail.config.bayes_dir = '/'

    d = archivemymail.archivebox(mbox, user)

    assert d['have_archived'] == True
    assert d['mbox_deleted'] == False
    assert "===== box =====" in caplog.text
    assert "2 messages to archive" in caplog.text

@pytest.mark.parametrize('tdir', [
    ('/bob'),
    ('~/bob'),
    ('/home/%u'),
])
def test_archivevbox_nonempty_learn(monkeypatch, caplog, tdir):
    archivemymail.config = archivemymail.Config()
    archivemymail.config.target_dir = tdir
    
    mbox = ([], '/', 'inbox')
    user = 'joe'

    monkeypatch.setattr("archivemymail.mboxman", mockmboxman)
    monkeypatch.setattr("archivemymail.progress.Progress", mockprogress)
    monkeypatch.setattr("archivemymail.wrappers.subprocess", mocksubprocess)
    archivemymail.server = mockserver(2)
    archivemymail.config.dry_run = False
    archivemymail.config.compression = "xz"
    archivemymail.config.do_learning = True
    archivemymail.config.bayes_dir = '/'

    d = archivemymail.archivebox(mbox, user)

    assert d['have_archived'] == True
    assert d['mbox_deleted'] == False
    assert "===== inbox =====" in caplog.text
    assert "2 messages to archive" in caplog.text
