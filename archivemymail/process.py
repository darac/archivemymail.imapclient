#!env python3

import logging
from collections import deque

import archivemymail


def process(account):
    (user, password) = account.split(':', 1)

    # Start by logging in
    logging.warning("")
    logging.warning("Archiving mail for %s", user)
    archivemymail.server = archivemymail.IMAPClient(archivemymail.config.server, ssl=True)
    archivemymail.server.login(user, password)

    mboxes = deque(archivemymail.server.list_folders())
    while len(mboxes):
        mbox = mboxes.popleft()
        disposition = archivemymail.archivebox(mbox, user)
        if disposition['have_archived'] \
                and not disposition['mbox_deleted'] \
                and archivemymail.config.do_learning:
            # mbox is (flags, delimiter, mbox_name). We just want the name
            # Actually, this SHOULD already be covered by existing filtering
            #archivemymail.learnbox(mbox[2])
            pass

    if archivemymail.config.do_learning and not archivemymail.config.dry_run:
        # Spamassassin has been filled with all the messages, but with "--no-sync"
        # So let's sync the database for this user
        sub = archivemymail.subprocess(['sa-learn', '--dbpath', archivemymail.config.bayes_dir, '--sync'],
                                       check=True)
