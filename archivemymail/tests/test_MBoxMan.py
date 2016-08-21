import email
import mailbox
import os
import subprocess

import pytest

import archivemymail


class TestNullBox:
    def test_defaults(self):
        box = archivemymail.MBoxMan.NullBox('/tmp/foo.mbox')
        assert box.path == '/tmp/foo.mbox'

    def test_iterations(self):
        box = archivemymail.MBoxMan.NullBox('/tmp/foo.mbox')
        counter = 0
        for b in box:
            counter += 1
            break
        assert counter == 0


@pytest.fixture(scope='session')
def mbox_file(tmpdir_factory):
    fn = tmpdir_factory.mktemp('/tmp').join('pytest.mbox')
    mbox = mailbox.mbox(str(fn))

    msg = email.message.Message()
    msg['Subject'] = 'test'
    msg['From'] = 'test@example.com'
    msg['To'] = 'test2@example.com'
    msg['Date'] = '01-Jan-2011'
    msg['Message-ID'] = '12345@example.com'
    msg.set_payload('test message\n')

    mbox.add(msg)

    msg = email.message.Message()
    msg['Subject'] = 'test'
    msg['From'] = 'test@example.com'
    msg['To'] = 'test2@example.com'
    msg['Date'] = '01-Jan-2011'
    msg['Message-ID'] = '98127@example.org'
    msg.set_payload('test message\n')

    mbox.add(msg)

    return fn


class TestMboxMan:
    @classmethod
    def setup(cls):
        cls.statsman = archivemymail.StatsMan.StatsManClass()
        cls.manager = archivemymail.MBoxMan.MBoxManClass(
            user='user@example.org',
            boxroot='/tmp',
            statsman=cls.statsman,
            dryrun=True,
            compression='gz')
        archivemymail.config = archivemymail.Config()

    def test_defaults(self):
        assert self.manager.user == 'user'
        assert self.manager.boxroot == '/tmp'
        assert self.manager.statsman == self.statsman
        assert self.manager.dryrun == True
        assert self.manager.compression == 'gz'
        assert self.manager.currentbox is None
        assert self.manager.boxpath is None
        assert self.manager.spambox is False
        assert self.manager.msgids == []

    def test_open_newbox(self, monkeypatch, caplog):
        def mymakedirs(path):
            assert path == "/tmp/boxname"

        monkeypatch.setattr(os, 'makedirs', mymakedirs)

        self.manager.open('boxname')
        assert self.manager.boxpath == 'boxname'
        assert isinstance(self.manager.currentbox, archivemymail.MBoxMan.NullBox)
        assert self.manager.currentbox.path == 'boxname'
        assert self.manager.msgids == []

    @pytest.mark.parametrize("extension,log,program", [
        ('', None, None),
        ('gz', 'GZip decompressing...', 'gzip'),
        ('bz2', 'BZip decompressing...', 'bzip2'),
        ('xz', 'XZip decompressing...', 'xz'),
        ('lz4', 'LZip decompressing...', 'lzop'),
    ])
    def test_decompress(self, monkeypatch, caplog, extension, log, program):
        path = "/tmp/pytest.mbox"
        try:
            def myrun(fullpath):
                assert fullpath == [program, '-d', path + '.' + extension]

            class Pope():
                def __init__(self, args, stdin=None, stdout=None):
                    assert args == [program, '-d', path + '.' + extension]
                    assert stdin is None
                    assert stdout is None

                def communicate(self, string=None):
                    assert string is None

                def check_returncode(self):
                    return 0

            try:
                monkeypatch.setattr(subprocess, 'run', myrun)
            except AttributeError:
                monkeypatch.setattr(subprocess, 'Popen', Pope)

            if extension is not '':
                with open(path + '.' + extension, 'a'):
                    os.utime(path + '.' + extension, None)

            self.manager._decompress(path)
            for record in caplog.records:
                assert record.levelname == 'DEBUG'
            if log is not None:
                assert log in caplog.text
        finally:
            try:
                os.remove(path + '.' + extension)
            except (OSError, IOError) as e:
                pass

    @pytest.mark.parametrize("compression,compressor,extension", [
        ('', None, ''),
        ('gz', 'gzip', 'gz'),
        ('gzip', 'gzip', 'gz'),
        ('bz2', 'bzip2', 'bz2'),
        ('bzip', 'bzip2', 'bz2'),
        ('xz', 'xz', 'xz'),
        ('xzip', 'xz', 'xz'),
        ('lz', 'lzop', 'lz4'),
        ('lzip', 'lzop', 'lz4'),
    ])
    def test_compress(self, monkeypatch, caplog, compression, compressor, extension):
        def myrun(fullpath):
            assert fullpath == [compressor, '-9', path]

        class Pope():
            def __init__(self, args, stdin=None, stdout=None):
                assert args == [compressor, '-9', path]
                assert stdin is None
                assert stdout is None

            def communicate(self, string=None):
                assert string is None

            def check_returncode(self):
                return 0

        try:
            monkeypatch.setattr(subprocess, 'run', myrun)
        except AttributeError:
            monkeypatch.setattr(subprocess, 'Popen', Pope)

        try:
            path = '/tmp/pytest.mbox'
            with open(path, 'a'):
                os.utime(path, None)
            self.manager._compress(path, compression)

            if compressor is not None:
                for record in caplog.records:
                    assert record.levelname == 'DEBUG'
                assert "Compressing {f} -> {f}.{e}".format(f=path, e=extension) in caplog.text

        finally:
            try:
                os.remove(path)
                if extension != '':
                    os.remove(path + '.' + extension)
            except (OSError, IOError) as e:
                pass

    def test_open_existing_box(self, monkeypatch, caplog, mbox_file):
        def mymakedirs(path):
            assert path == "/tmp/pytest.mbox"

        monkeypatch.setattr(os, 'makedirs', mymakedirs)

        def mydecompress(path):
            assert path.endswith('pytest.mbox')

        monkeypatch.setattr(self.manager, '_decompress', mydecompress)

        self.manager.dryrun = False
        self.manager.open(str(mbox_file))
        assert self.manager.boxpath.endswith('pytest.mbox')
        assert isinstance(self.manager.currentbox, mailbox.Mailbox)
        assert '98127@example.org' in self.manager.msgids
        assert '12345@example.com' in self.manager.msgids

    def test_close(self, monkeypatch):
        self.manager.open('pytest.mbox')

        def do_nothing():
            pass

        def mycompress(path, compression):
            assert path == '/tmp/pytest.mbox'
            assert compression == 'gz'

        monkeypatch.setattr(self.manager.currentbox, 'unlock', do_nothing)
        monkeypatch.setattr(self.manager.currentbox, 'close', do_nothing)
        monkeypatch.setattr(self.manager, 'learn', do_nothing)
        monkeypatch.setattr(self.manager, '_compress', mycompress)

        archivemymail.config.compression = 'gz'
        self.manager.boxroot = '/tmp'
        self.manager.boxpath = 'pytest.mbox'

        self.manager.currentbox = None
        self.manager.close()

        self.manager.dryrun = True
        self.manager.close()

        self.manager.dryrun = False
        self.manager.close()
