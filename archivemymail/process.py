#!env python3

import logging
from collections import deque

import archivemymail
from imapclient import IMAPClient

def process(account):
    (user, password) = account.split(':', 1)

    # Start by logging in
    logging.info("")
    logging.info("Archiving mail for %s", user)
    archivemymail.server = IMAPClient(archivemymail.config.server, ssl=True)
    archivemymail.server.login(user, password)

    mboxes = deque(archivemymail.server.list_folders())
    while len(mboxes):
        mbox = mboxes.popleft()
        disposition = archivemymail.archivebox(mbox)
        if disposition & archivemymail.HAVE_ARCHIVED \
                and not disposition & archivemymail.MBOX_DELETED \
                and archivemymail.config.do_learning:
            archivemymail.learnbox(mbox)
