#!env python3

from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import argparse
import os
import sys

try:
    from builtins import *
except ImportError:
    from future_builtins import *

import yaml
from appdirs import user_config_dir
import collections


class Config(collections.MutableMapping):
    def __init__(self):
        # Start with no configuration
        self.__dict__ = {}

    def load(self):
        # Load static config from a file
        try:
            with open(os.path.join(user_config_dir('archivemymail', 'Darac'), 'config.yml'), 'r') as f:
                self.__dict__ = yaml.load(f)
        except (OSError, IOError) as e:
            pass

        # Override the config with command line args
        parser = argparse.ArgumentParser(description="Archive mail from IMAP to compressed mbox")
        parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true',
                            default=self.setdefault('dry_run', False),
                            help="show what WOULD have been done")
        parser.add_argument('-S', '--no-learn', dest='do_learning', action='store_false',
                            default=self.setdefault('do_learning', True),
                            help="don't pass messages to spamassassin")
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument('-z', '--gzip', dest='compression', action='store_const', const='gz',
                           help="GZIP-compress mboxes")
        group.add_argument('-j', '--bzip2', dest='compression', action='store_const', const='bz2',
                           help="BZIP2-compress mboxes")
        group.add_argument('-J', '--xz', dest='compression', action='store_const', const='xz',
                           help="XZ-compress mboxes (default)")
        parser.add_argument('-d', '--target-dir', dest='target_dir', action='store',
                            default=self.setdefault('target_dir', '/var/mail/%u/archive/'),
                            help="root location for the mboxes")
        parser.add_argument('-b', '--bayes-dir', dest='bayes_dir', action='store',
                            default=self.setdefault('bayes_dir', '/var/lib/amavis/.spamassassin'),
                            help="location of spamassassin's bayes database")
        parser.add_argument('-H', '--server', dest='server', action='store',
                            default=self.setdefault('server', 'mail.darac.org.uk'),
                            help="hostname of mail server")
        parser.add_argument('--debug', dest='debug', action='store_true',
                            default=self.setdefault('debug', False),
                            help="output extra logging")
        parser.add_argument('-a', '--account', dest='accounts', action='append',
                            default=self.setdefault('accounts', []),
                            help="account to archive (can be specified multiple times)",
                            metavar="USER:PASSWORD")
        parser.add_argument('--dump-config', dest='dump_config', action='store_true',
                            default=self.setdefault('dump_config', False),
                            help="dump configuration to the config file (%s)" % os.path.join(user_config_dir('archivemymail', 'Darac'), 'config.yml'))

        args, unknowns = parser.parse_known_args()

        # Consolidate the options
        self['dry_run'] = args.dry_run
        self['do_learning'] = args.do_learning
        if args.compression is None:
            if 'compression' not in self.__dict__ or self['compression'] is None:
                self['compression'] = 'xz'
                # Else keep with self.compression
        else:
            self['compression'] = args.compression

        self['target_dir'] = args.target_dir
        self['bayes_dir'] = args.bayes_dir
        self['server'] = args.server
        self['debug'] = args.debug
        self['accounts'] = args.accounts

        if args.dump_config:
            fname = os.path.join(user_config_dir('archivemymail', 'Darac'), 'config.yml')
            os.makedirs(user_config_dir('archivemymail', 'Darac'), exist_ok=True)
            with open(fname, 'w') as f:
                yaml.dump(self.__dict__, f)
            print("Configuration dumped to %s" % fname)
            sys.exit(0)

    # These are the methods required by collections.MutableMapping,
    #  which uses them to synthesize this class as a dict-like object
    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, item):
        self.__dict__[key] = item

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)
