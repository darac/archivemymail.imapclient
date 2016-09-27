# !env python3

import logging
import math
import os
import sys

import archivemymail

def learnbox(mbox):
    if mbox.lower().find('spam') == -1:
        # -1 means "not found"
        spamham = 'ham'
    else:
        spamham = 'spam'
    archivemymail.server.select_folder(mbox, readonly=True)
    msg_list = archivemymail.server.search(['NOT', 'DELETED'])
    logging.info('%d remaining messages to learn', len(msg_list))

    p = archivemymail.progress.Progress(len(msg_list), learning=True)

    for msg_num in msg_list:
        message = archivemymail.server.fetch(msg_num, 'RFC822')[msg_num]['RFC822']
        p.log(message, mbox, spamham == 'spam')
        if archivemymail.config.dry_run:
            logging.info('Would learn %s folder: %s', spamham, mbox)
        else:
            logging.debug('Learning %s folder: %s', spamham, mbox)
            try:
                m = message.as_bytes()
            except AttributeError:
                m = message.as_string()
            sub = archivemymail.wrappers.subprocess(['sa-learn', '--{}'.format(spamham),
                '--no-sync', '--dbpath', archivemymail.config.bayes_dir],
                input=m)
            sub.check()

