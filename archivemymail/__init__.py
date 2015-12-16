#!env python3

import datetime
import email.header

from .Config import Config
from .MBoxMan import MBoxMan
from .StatsMan import StatsMan
from .archivebox import archivebox
from .learnbox import learnbox
from .process import process

__version__ = 0.1

# Flags
HAVE_ARCHIVED = 1
MBOX_DELETED = 2

config = Config()
statsman = StatsMan()
mboxman = None
server = None

_midnight = datetime.time(0, 0, 0)
_today = datetime.date.today()
_six_weeks = datetime.timedelta(weeks=6)

archivedate = datetime.datetime.combine(
        _today - _six_weeks,
        _midnight)


def parse_subject(subj, left=None, right=None):
    subject_pairs = email.header.decode_header(subj)
    subject = ""
    try:
        for part in subject_pairs:
            subject += part[0].decode(part[1] or 'utf-8', 'replace')
    except UnicodeDecodeError:
        subject = "<Unintelligible Subject>"
    except AttributeError:
        subject = subj
    return subject[left:right]
