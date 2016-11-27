import email
import mailbox
import os
import subprocess

import pytest

import archivemymail

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError
    FileExistsError = IOError


class TestNullBox:
    def test_defaults(self):
        box = archivemymail.NullBoxClass('/tmp/foo.mbox')
        assert box.path == '/tmp/foo.mbox'

    def test_iterations(self):
        box = archivemymail.NullBoxClass('/tmp/foo.mbox')
        counter = 0
        for b in box:
            counter += 1
            break
        assert counter == 0

    def test_add(self):
        box = archivemymail.NullBoxClass('/tmp/foo.mbox')
        box.add("test")

    def test_close(self):
        box = archivemymail.NullBoxClass('/tmp/foo.mbox')
        box.close()


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
        cls.statsman = archivemymail.StatsManClass()
        cls.manager = archivemymail.MBoxManClass(
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
        assert self.manager.dryrun is True
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
        assert isinstance(self.manager.currentbox, archivemymail.NullBoxClass)
        assert self.manager.currentbox.path == 'boxname'
        assert self.manager.msgids == []

    @pytest.mark.parametrize("extension,log,program", [
        ('', None, None),
        ('gz', 'GZip decompressing...', 'gzip'),
        ('bz2', 'BZip decompressing...', 'bzip2'),
        ('xz', 'XZip decompressing...', 'xz'),
        ('lz4', 'LZip decompressing...', 'lzop'),
        ('lz4', 'LZip decompressing...', 'invalid'),
        ('exists', None, None)
    ])
    def test_decompress(self, monkeypatch, caplog, extension, log, program):
        path = "/tmp/pytest.mbox"
        try:
            class myretclass:
                def __init__(self):
                    self.returncode = 1

                def check_returncode(self):
                    pass

            def myrun(fullpath, stdin=None, input=None, check=False):
                if program == 'invalid':
                    return myretclass()
                assert fullpath == [program, '-d', path + '.' + extension]

            class Pope:
                def __init__(self, args, stdin=None, stdout=None):
                    if program != 'invalid':
                        assert args == [program, '-d', path + '.' + extension]
                    assert stdin is None
                    assert stdout is None

                @staticmethod
                def communicate(string=None):
                    assert string is None
                    if program == 'invalid':
                        return myretclass()

                @staticmethod
                def check_returncode():
                    return 0

            if extension == 'exists':
                with open(path, 'a'):
                    os.utime(path, None)

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
        ('nonexist', None, None),
        ('exists', None, 'gz'),
    ])
    def test_compress(self, monkeypatch, caplog, compression, compressor, extension):
        def myrun(fullpath, stdin=None, input=None, check=False):
            assert fullpath == [compressor, '-9', path]

        class Pope:
            def __init__(self, args, stdin=None, stdout=None):
                assert args == [compressor, '-9', path]
                assert stdin is None
                assert stdout is None

            @staticmethod
            def communicate(self, string=None):
                assert string is None

            @staticmethod
            def check_returncode(self):
                return 0

        try:
            monkeypatch.setattr(subprocess, 'run', myrun)
        except AttributeError:
            monkeypatch.setattr(subprocess, 'Popen', Pope)

        try:
            path = '/tmp/pytest.mbox'
            if compression != 'nonexist':
                with open(path, 'a'):
                    os.utime(path, None)

                if compression == "exists":
                    compression = "gz"
                    with open(path + '.' + compression, 'a'):
                        os.utime(path + '.' + compression, None)

                    with pytest.raises(FileExistsError):
                        self.manager._compress(path, compression)
                else:
                    self.manager._compress(path, compression)
            else:
                with pytest.raises(FileNotFoundError):
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

        monkeypatch.setattr('os.makedirs', mymakedirs)

        def mydecompress(path):
            assert path.endswith('pytest.mbox')

        monkeypatch.setattr(self.manager, '_decompress', mydecompress)

        self.manager.dryrun = False
        self.manager.open(str(mbox_file))
        assert self.manager.boxpath.endswith('pytest.mbox')
        assert isinstance(self.manager.currentbox, mailbox.Mailbox)
        assert '98127@example.org' in self.manager.msgids
        assert '12345@example.com' in self.manager.msgids

    def test_open_nonexistant_box(self, monkeypatch, caplog, mbox_file):
        def mymakedirs(path):
            assert path == "/tmp/nonexistant"

        monkeypatch.setattr('os.makedirs', mymakedirs)

        def mydecompress(path):
            assert path.endswith('blah')

        monkeypatch.setattr(self.manager, '_decompress', mydecompress)

        self.manager.dryrun = False
        self.manager.boxroot = '/tmp/nonexistant'

        self.manager.open('blah')
        assert self.manager.boxpath.endswith('blah')
        assert isinstance(self.manager.currentbox, mailbox.Mailbox)
        assert self.manager.msgids == []

    def test_set_box(self, monkeypatch):
        def myclose(self):
            pass

        def myopen(self, path):
            assert path.endswith('_box.mbox')
            self.currentbox = archivemymail.NullBoxClass(path)
            self.boxpath = path

        def mynewbox(self, user, path):
            assert path.endswith('_box.mbox')
            assert user == 'user'

        monkeypatch.setattr('archivemymail.MBoxManClass.close', myclose)
        monkeypatch.setattr('archivemymail.MBoxManClass.open', myopen)
        monkeypatch.setattr('archivemymail.StatsManClass.new_box', mynewbox)

        # Test when no box is open
        self.manager.currentbox = None
        result = self.manager.set_box(path='another_box.mbox', spambox=False)
        assert result == self.manager.currentbox
        assert result.path == 'another_box.mbox'
        assert self.manager.spambox is False

        # Test when re-opening the box
        assert self.manager.boxpath == 'another_box.mbox'
        assert self.manager.currentbox is not None
        result = self.manager.set_box(path='another_box.mbox', spambox=False)
        assert result == self.manager.currentbox
        assert result.path == 'another_box.mbox'
        assert self.manager.spambox is False

        # Test when changing box
        result = self.manager.set_box(path='a_box.mbox', spambox=True)
        assert result == self.manager.currentbox
        assert result.path == 'a_box.mbox'
        assert self.manager.spambox is True

    @pytest.mark.parametrize("mid,inlist", [
        ("12345", False),
        ("23456", True),
        (None, False),
    ])
    def test_add(self, monkeypatch, mid, inlist):
        if inlist:
            self.manager.msgids.append(mid)
        else:
            try:
                self.manager.msgids.remove(mid)
            except ValueError:
                pass

        self.manager.currentbox = archivemymail.NullBoxClass('/path')

        def myadd(message):
            assert message is not None
            if mid is not None:
                assert message['Message-ID'] == mid

        def myotheradd(path, message):
            assert message is not None
            if mid is not None:
                assert message['Message-ID'] == mid

        monkeypatch.setattr(self.manager.currentbox, 'add', myadd)
        monkeypatch.setattr(self.manager.statsman, 'add', myotheradd)

        msg = email.message.Message()
        msg['Subject'] = 'test'
        msg['From'] = 'test@example.com'
        msg['To'] = 'test2@example.com'
        msg['Date'] = '01-Jan-2011'
        if mid is not None:
            msg['Message-ID'] = mid
        msg.set_payload('test message\n')

        # Run the UUT
        self.manager.add(msg)

        if mid is not None:
            assert mid in self.manager.msgids

    @pytest.mark.parametrize("spambox,dryrun", [
        (False, False),
        (False, True),
        (True, False),
        (True, True)
    ])
    def test_leanspam(self, monkeypatch, caplog, spambox, dryrun):
        self.manager.spambox = spambox
        self.manager.dryrun = dryrun

        def myrun(fullpath, stdin=None, input=None, check=False):
            assert 'sa-learn' in fullpath
            assert '--no-sync' in fullpath
            assert '--dbpath' in fullpath
            return

        class Pope:
            def __init__(self, args, stdin=None, stdout=None):
                assert 'sa-learn' in args
                assert '--no-sync' in args
                assert '--dbpath' in args
                assert stdin is None
                assert stdout is None
                self.returncode = 0

            @staticmethod
            def communicate(string=None):
                assert string is None

            @staticmethod
            def check_returncode():
                return 0

        try:
            monkeypatch.setattr(subprocess, 'run', myrun)
        except AttributeError:
            monkeypatch.setattr(subprocess, 'Popen', Pope)

        archivemymail.config['bayes_dir'] = '/tmp'
        self.manager.boxroot = '/tmp'
        self.manager.boxpath = 'blah'

        self.manager.learn()
        if dryrun:
            assert 'Would learn' in caplog.text
        else:
            assert 'Learning' in caplog.text

    def test_close(self, monkeypatch):
        self.manager.open('pytest.mbox')
        assert self.manager.currentbox is not None

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

        self.manager.currentbox = archivemymail.NullBoxClass('/path')
        self.manager.dryrun = True
        archivemymail.config['do_learning'] = True
        self.manager.close()

        self.manager.dryrun = False
        archivemymail.config['do_learning'] = False
        self.manager.close()
