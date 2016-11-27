#!env python3

import datetime
import email.header

from .Config import Config
from .MBoxMan import MBoxManClass, NullBoxClass
from .progress import Progress
from .StatsMan import StatsManClass
from .archivebox import archivebox
from .learnbox import learnbox
from .process import process
from .wrappers import *


__version__ = 0.1

config = Config()
statsman = StatsManClass()
mboxman = None
server = None

_midnight = datetime.time(0, 0, 0)
_today = datetime.date.today()
_six_weeks = datetime.timedelta(weeks=6)

archivedate = datetime.datetime.combine(
    _today - _six_weeks,
    _midnight)


def parse_header(header, left=None, right=None):
    header_pairs = email.header.decode_header(header)
    new_header = ''
    try:
        for part in header_pairs:
            try:
                new_header += part[0].decode(part[1] or 'utf-8', 'replace')
            except LookupError:
                new_header += part[0].decode('utf-8', 'replace')
    except UnicodeDecodeError:
        new_header = '<Unintelligible Header>'
    except AttributeError:
        new_header = header
    except LookupError:
        print("header: %s" % header)
        print("header pairs: %s" % header_pairs)
        print("str header: %s" % email.header.make_header(email.header.decode_header(header)))
        raise
    return new_header[left:right]
