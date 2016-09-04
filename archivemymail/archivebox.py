#!env python3
# vim: set fileencoding=utf8 :

import email.parser
import logging
import mailbox
import os
import subprocess

import imapclient

import archivemymail
from Progress import Progress


def archivebox(mbox, user):
    disposition = 0

    (flags, delimiter, mbox_name) = mbox

    # Don't archive boxes in the archive
    if mbox_name.startswith("Archive") or \
            mbox_name.startswith("_ARCHIVE"):
        return disposition

    # If a box can't be selected, it can't be archived
    if b'\NoSelect' in flags:
        return disposition

    tdir = archivemymail.config.target_dir
    if tdir.startswith('~/'):
        tdir = tdir.replace('~', '/home/' +
                            (user.split('@', 1))[0], 1)
    if '%u' in tdir:
        tdir = tdir.replace('%u', user)

    logging.info("")
    logging.info("====== %s ======", mbox_name)

    archivemymail.server.select_folder(mbox_name)
    msg_list = archivemymail.server.search(['OLD', 'BEFORE', '{:%d-%b-%Y}'.format(archivemymail.archivedate)])

    archivemymail.mboxman = archivemymail.mboxman(user,
                                                  archivemymail.config.target_dir,
                                                  archivemymail.statsman,
                                                  archivemymail.config.dry_run,
                                                  archivemymail.config.compression)
    progress = Progress(len(msg_list))

    logging.debug("%d messages to archive", len(msg_list))
    for msg_num in msg_list:
        disposition &= archivemymail.HAVE_ARCHIVED
        imapmessage = archivemymail.server.fetch(msg_num, ['FLAGS', 'RFC822', 'INTERNALDATE'])[msg_num]
        mboxflags = ''
        if imapclient.RECENT in imapmessage['FLAGS']:
            mboxflags += 'R'
        if imapclient.SEEN in imapmessage['FLAGS']:
            mboxflags += 'O'
        if imapclient.DELETED in imapmessage['FLAGS']:
            mboxflags += 'D'
        if imapclient.FLAGGED in imapmessage['FLAGS']:
            mboxflags += 'F'
        if imapclient.ANSWERED in imapmessage['FLAGS']:
            mboxflags += 'A'
        logging.debug(' + Flags: %s', mboxflags)

        # Get the body of the message
        fp = email.parser.BytesFeedParser()
        fp.feed(imapmessage['RFC822'])
        message = mailbox.mboxMessage(fp.close())
        message.set_flags(mboxflags)

        # Use the internal date to determine which file to archive to
        boxname = os.path.join(tdir,
                               "{boxpath}/{year}/{month:02}".format(boxpath=mbox_name,
                                                                    year=imapmessage['INTERNALDATE'].year,
                                                                    month=imapmessage['INTERNALDATE'].month))
        logging.debug(" + File is %s.%s", boxname, archivemymail.config.compression)
        archivemymail.mboxman.set_box(boxname, mbox_name.lower().find('spam') == -1)

        # Log Progress
        progress.log(message, boxname, boxname.lower().find('spam') == 1)

        # Pass the message through SpamAssassin
        if archivemymail.config.do_learning and not archivemymail.config.dry_run:
            subprocess.run(['sa-learn', '--spam', '--no-sync',
                            '--dbpath', archivemymail.config.bayes_dir],
                           input=message.as_string()).check_returncode()
        elif not archivemymail.config.dry_run:
            subprocess.run(['sa-learn', '--ham', '--no-sync',
                            '--dbpath', archivemymail.config.bayes_dir],
                           input=message.as_string()).check_returncode()

        # Add the message to the mbox
        archivemymail.mboxman.add(message)

        # And remove it from the mailbox
        archivemymail.server.delete_messages(msg_num)

    # Archived all the necessary messages
    # Delete the folder, too, if there's nothing left
    if mbox_name.lower() not in ('inbox',  # Don't delete the special folders
                                 'drafts',
                                 'sent',
                                 'spam',
                                 'trash',
                                 'learnspam',
                                 'queue'):
        msg_list = archivemymail.server.search(['NOT', 'DELETED'])
        if len(msg_list) <= 0:
            disposition &= archivemymail.MBOX_DELETED
            if archivemymail.config.dry_run:
                logging.info("Would delete now-empty folder %s", mbox_name)
            else:
                logging.debug("Deleting now-empty folder %s")
                archivemymail.server.delete_folder(mbox_name)

    archivemymail.server.close_folder()

    return disposition
