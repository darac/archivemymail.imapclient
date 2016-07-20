#!env python3

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import argparse
import os
from builtins import *

import yaml
from appdirs import user_config_dir


class Config:

    def __init__(self):
        # Start with no configuration
        self.__dict__ = {}

    def load(self):
        # Load static config from a file
        try:
            with open(os.path.join(user_config_dir('archivemymail', 'Darac'), 'config.yml'), 'r') as f:
                self.__dict__ = yaml.load(f)
        except FileNotFoundError:
            pass

        # Override the config with command line args
        parser = argparse.ArgumentParser(description="Archive mail from IMAP to compressed mbox")
        parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true',
                            default=self._pick_one(self['dry_run'], False),
                            help="show what WOULD have been done")
        parser.add_argument('-S', '--no-learn', dest='do_learning', action='store_false',
                            default=self._pick_one(self['doLearning'], True),
                            help="don't pass messages to spamassassin")
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument('-z', '--gzip', dest='compression', action='store_const', const='gz',
                           help="GZIP-compress mboxes")
        group.add_argument('-j', '--bzip2', dest='compression', action='store_const', const='bz2',
                           help="BZIP2-compress mboxes")
        group.add_argument('-J', '--xz', dest='compression', action='store_const', const='xz',
                           help="XZ-compress mboxes (default)")
        parser.add_argument('-d', '--target-dir', dest='target_dir', action='store',
                            default=self._pick_one(self['target_dir'], '/var/mail/%u/archive/'),
                            help="root location for the mboxes")
        parser.add_argument('-b', '--bayes-dir', dest='bayes_dir', action='store',
                            default=self._pick_one(self['bayes_dir'], '/var/lib/amavis/.spamassassin'),
                            help="location of spamassassin's bayes database")
        parser.add_argument('-H', '--server', dest='server', action='store',
                            default=self._pick_one(self['server'], 'mail.darac.org.uk'),
                            help="hostname of mail server")
        parser.add_argument('--debug', dest='debug', action='store_true',
                            default=self._pick_one(self['debug'], False),
                            help="output extra logging")
        parser.add_argument('-a', '--account', dest='accounts', action='append',
                            default=self['accounts'],
                            help="account to archive (can be specified multiple times)",
                            metavar="USER:PASSWORD")

        args = parser.parse_args()

        # Consolidate the options
        self.dry_run = args.dry_run
        self.do_learning = args.do_learning
        self.compression = self._pick_one(args.compression, 'xz')
        if self.compression is None:
            self.compression = 'xz'
        self.target_dir = args.target_dir
        self.bayes_dir = args.bayes_dir
        self.server = args.server
        self.debug = args.debug
        self.accounts = args.accounts

    @staticmethod
    def _pick_one(default, fallback):
        try:
            return default
        except NameError:
            try:
                return fallback
            except NameError:
                return None

    # Set of methods to make the class act like a mapping
    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __getitem__(self, key):
        try:
            return self.__dict__[key]
        except KeyError:
            return None

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]

    def clear(self):
        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        return self.__dict__.update(*args, **kwargs)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        return self.__dict__.pop(*args)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)
