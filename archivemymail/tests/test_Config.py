import pytest
import yaml
import sys

import archivemymail

class TestConfig:

    @classmethod
    def setup(self):
        self.Config = archivemymail.Config()

    def test_defaults(self):
        assert len(self.Config) == 0
        for k in self.Config.keys():
            assert self.Config[k] == ""

    def test_mapping_properties(self):
        initial_size = len(self.Config)

        # Add
        self.Config["new_entry"] = 1
        assert len(self.Config) == initial_size + 1
        assert self.Config["new_entry"] == 1

        # Modify
        self.Config["new_entry"] = 2
        assert len(self.Config) == initial_size + 1
        assert self.Config["new_entry"] == 2

        # Delete
        del self.Config["new_entry"]
        assert len(self.Config) == initial_size
        assert "new_entry" not in self.Config

        # Iter
        for k in self.Config:
            assert k in self.Config

        # SetDefault
        assert "other key" not in self.Config
        assert self.Config.setdefault("other key", False) == False
        assert self.Config["other key"] is False
        self.Config["other key"] = True
        assert self.Config.setdefault("other key", False) == True

    def test_load_fileonly(self, monkeypatch, tmpdir):
        # Start by writing the config file to a temporary file
        test_data = {
            'dry_run' : False,
            'do_learning' : True,
            'compression' : 'bzip',
            'target_dir' : '/tmp/target_dir',
            'bayes_dir' : '/user/dir/bayes',
            'server' : 'imap.example.org',
            'debug' : True,
            'accounts' : [ 'user:password', 'user2@example.com:letmein'],
            }

        d = tmpdir.mkdir("config")
        p = d.join('config.yml')
        p.write(yaml.dump(test_data))

        # Now monkeypatch os.path.join to return the temporary file
        def myjoin(*args):
            if 'config.yml' in args:
                assert "archivemymail" in args[0]
                assert 'config.yml' in args[1]
                return str(p)
            else:
                return "/".join(args)
        monkeypatch.setattr("os.path.join", myjoin)

        # Now call UUT
        self.Config.load()

        for k in test_data.keys():
            assert self.Config[k] == test_data[k]

    @pytest.mark.parametrize("flag,arg,target,result", [
        ("--dry-run", None, "dry_run", True),
        ("-n", None, "dry_run", True),
        ("--no-learn", None, "do_learning", False),
        ("--gzip", None, "compression", "gz"),
        ("--bzip2", None, "compression", "bz2"),
        ("--xz", None, "compression", "xz"),
        ("--target-dir", "/tmp/source_dir", "target_dir", "/tmp/source_dir"),
        ("--bayes-dir", "/otheruser/dir/bayes", "bayes_dir", "/otheruser/dir/bayes"),
        ("--server", "imap.example.net", "server", "imap.example.net"),
        ("--debug", None, "debug", True),
    ])
    def test_load_argsonly(self, monkeypatch, flag, arg, target, result):
        while len(sys.argv) < 3:
            sys.argv.append('blah')
        # Set args
        sys.argv[1] = flag
        if arg is None:
            del sys.argv[2]
        else:
            sys.argv[2] = arg

        self.Config.load()

        assert self.Config[target] == result
