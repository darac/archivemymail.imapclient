# vim: set fileencoding=utf8 :
import logging
import math
import os
import sys

import archivemymail


class Progress:
    def __init__(self, total):
        self.total = total
        if os.isatty(sys.stdout.fileno()):
            self.field_width = int(math.floor(math.log(total, 10)) + 1)
        else:
            self.field_width = None
        self.num = 0

    def log(self, message, box, is_spam=False):
        self.num += 1
        if self.field_width is not None:
            progress = '({1:{0}}/{2:{0}}) '.format(self.field_width, self.num, self.total)
        else:
            progress = ''

        subject = archivemymail.parse_header(message['Subject'], right=50)
        if is_spam:
            spamham = "[SPAM]"
        else:
            spamham = "[HAM ]"
        try:
            line = "{progress}{spamham} {subject:50} → {box}".format(subject=subject, box=box, spamham=spamham,
                                                                      progress=progress)
        except TypeError:
            line = "{progress}{spamham} {subject:50} → {box}".format(subject="<No Subject>", box=box, spamham=spamham,
                                                                      progress=progress)
        logging.info(line)
