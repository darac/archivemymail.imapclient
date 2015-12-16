#!env python3

import logging
import math
import os
import subprocess
import sys

import archivemymail


class Progress:
    def __init__(self, total):
        self.total = total
        if os.isatty(sys.stdout.fileno()):
            self.field_width = int(math.ceil(math.log(total, 10)))
        else:
            self.field_width = None
        self.num = 0

    def log(self, message, is_spam=False):
        self.num += 1
        if self.field_width is not None:
            progress = '({1:{0}}/{2:{0}}) '.format(self.field_width, self.num, self.total)
        else:
            progress = ''

        subject = archivemymail.parse_subject(message['Subject'], right=50)
        if is_spam:
            spamham = "[Learn-SPAM]"
        else:
            spamham = "[Learn-HAM ]"
        try:
            line = "{progress}{spamham} {subject:-50}".format(subject=subject, spamham=spamham,
                                                              progress=progress)
        except TypeError:
            line = "{progress}{spamham} {subject:-50}".format(subject="<No Subject>", spamham=spamham,
                                                              progress=progress)
        logging.info(line)


def learnbox(mbox):
    if mbox.lower().find('spam') == -1:
        spamham = 'spam'
    else:
        spamham = 'ham'
    archivemymail.server.select_folder(readonly=True)
    msg_list = archivemymail.server.search(['NOT', 'DELETED'])
    logging.info("%d remaining messages to learn", len(msg_list))

    p = Progress(len(msg_list))

    for msg_num in msg_list:
        message = archivemymail.server.fetch(msg_num, 'RFC822')[msg_num]['RFC822']
        p.log(message, spamham == 'spam')
        if archivemymail.config.dry_run:
            logging.info("Would learn %s folder: %s", spamham, mbox)
        else:
            logging.debug("Learning %s folder: %s", spamham, mbox)
            subprocess.run(['sa-learn', '--{}'.format(spamham), '--no-sync',
                            '--dbpath', archivemymail.config.bayes_dir],
                           input=message).check_returncode()
