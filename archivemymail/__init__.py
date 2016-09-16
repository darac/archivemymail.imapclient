# !env python3

import datetime
import email.header

from .Config import Config
from .MBoxMan import MBoxManClass
from .Progress import Progress
from .StatsMan import StatsManClass
from .archivebox import archivebox
from .learnbox import learnbox
from .process import process

__version__ = 0.1

# Flags
HAVE_ARCHIVED = 1
MBOX_DELETED = 2

config = Config()
statsman = StatsManClass()
mboxman = None
server = None

_midnight = datetime.time(0, 0, 0)
_today = datetime.date.today()
_six_weeks = datetime.timedelta(weeks=6)

archivedate = datetime.datetime.combine(
        _today-_six_weeks,
        _midnight)


def parse_header(header, left=None, right=None):
    header_pairs = email.header.decode_header(header)
    new_header = ''
    try:
        for part in header_pairs:
            new_header += part[0].decode(part[1] or 'utf-8', 'replace')
    except UnicodeDecodeError:
        new_header = '<Unintelligible Header>'
    except AttributeError:
        new_header = header
    return new_header[left:right]

