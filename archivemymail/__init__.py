#!env python3

import datetime

from .Config import Config
from .MBoxMan import MBoxMan
from .StatsMan import StatsMan
from .archivebox import archivebox
from .process import process

# Flags
HAVE_ARCHIVED = 1
MBOX_DELETED = 2

config = Config()
statsman = StatsMan()
mboxman = MBoxMan()
server = None

_midnight = datetime.time(0, 0, 0)
_today = datetime.date.today()
_six_weeks = datetime.timedelta(weeks=6)

archivedate = datetime.datetime.combine(
        _today - _six_weeks,
        _midnight)

__version__ = 0.1
