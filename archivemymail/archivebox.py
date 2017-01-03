#!env python3
# vim: set fileencoding=utf8 :

import email.parser
import imaplib
import logging
import mailbox
import os
import sys

import imapclient

import archivemymail


def archivebox(mbox, user):
    disposition = \
        {'have_archived': False,
         'mbox_deleted': False}

    (flags, delimiter, mbox_name) = mbox

    # Don't archive boxes in the archive
    if mbox_name.startswith("Archive") or \
            mbox_name.startswith("_ARCHIVE"):
        return disposition

    # If a box can't be selected, it can't be archived
    if b'\\Noselect' in flags or b'\\NoSelect' in flags:
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

    archivemymail.mboxman = archivemymail.MBoxManClass(user,
                                                       archivemymail.config.target_dir,
                                                       archivemymail.statsman,
                                                       archivemymail.config.dry_run,
                                                       archivemymail.config.compression)
    progress = archivemymail.Progress(len(msg_list))

    logging.debug("%d messages to archive", len(msg_list))
    for msg_num in msg_list:
        try:
            imapmessage = archivemymail.server.fetch(msg_num, ['FLAGS', 'RFC822', 'INTERNALDATE'])[msg_num]
            mboxflags = ''
            if imapclient.RECENT not in imapmessage[b'FLAGS']:
                mboxflags += 'O'
            if imapclient.SEEN in imapmessage[b'FLAGS']:
                mboxflags += 'R'
            if imapclient.DELETED in imapmessage[b'FLAGS']:
                mboxflags += 'D'
            if imapclient.FLAGGED in imapmessage[b'FLAGS']:
                mboxflags += 'F'
            if imapclient.ANSWERED in imapmessage[b'FLAGS']:
                mboxflags += 'A'
            if imapclient.DRAFT in imapmessage[b'FLAGS']:
                mboxflags += 'T'
            logging.debug(' + Flags: %s', mboxflags)

            # Get the body of the message
            try:
                fp = email.parser.BytesFeedParser()
                fp.feed(imapmessage[b'RFC822'])
            except (AttributeError, KeyError):
                fp = email.parser.FeedParser()
                fp.feed(imapmessage['RFC822'])
            message = mailbox.mboxMessage(fp.close())
            message.set_flags(mboxflags)

            # Use the internal date to determine which file to archive to
            boxname = os.path.join(tdir,
                                   "{boxpath}/{year}/{month:02}".format(boxpath=mbox_name,
                                                                        year=imapmessage[b'INTERNALDATE'].year,
                                                                        month=imapmessage[b'INTERNALDATE'].month))
            logging.debug(" + File is %s.%s", boxname, archivemymail.config.compression)
            archivemymail.mboxman.set_box(boxname, mbox_name.lower().find('spam') != -1)

            # Log Progress
            progress.log(message, boxname, boxname.lower().find('spam') != -1)

            try:
                flatmessage = message.as_bytes()
            except AttributeError:
                flatmessage = message.as_string()

            # Pass the message through SpamAssassin
            # Nope. This is done in MBoxMan :)
#            if archivemymail.config.do_learning and not archivemymail.config.dry_run:
#                archivemymail.subprocess(
#                    ['sa-learn', '--spam', '--no-sync',
#                     '--dbpath', archivemymail.config.bayes_dir],
#                    input=flatmessage, check=True)
#            elif not archivemymail.config.dry_run:
#                archivemymail.subprocess(
#                    ['sa-learn', '--ham', '--no-sync',
#                     '--dbpath', archivemymail.config.bayes_dir],
#                    input=flatmessage, check=True)

            # Add the message to the mbox
            archivemymail.mboxman.add(message)

            # And remove it from the mailbox
            if not archivemymail.config.dry_run:
                archivemymail.server.delete_messages(msg_num)
            else:
                logging.debug(" + Not deleting in dry-run")

            disposition['have_archived'] = True
        except imaplib.IMAP4.abort:
            (exc_type, exc_value, _) = sys.exc_info()
            logging.warning("EXCEPTION processing message %d: %s - %s" % (msg_num, exc_type, exc_value))
            logging.warning("Attempting reconnection")
            archivemymail.server.reconnect()
        except (imapclient.IMAPClient.Error, imaplib.IMAP4.error):
            (exc_type, exc_value, exc_trace) = sys.exc_info()
            logging.warning("EXCEPTION processing message %d: %s - %s" % (msg_num, exc_type, exc_value))
            [logging.warning("%s", x) for x in traceback.format_tb(exc_trace)]
            logging.warning("Skipping to next message")

    archivemymail.server.expunge()

    # Archived all the necessary messages
    # Delete the folder, too, if there's nothing left
    if mbox_name.lower() not in ('inbox',  # Don't delete the special folders
                                 'drafts',
                                 'sent',
                                 'spam',
                                 'trash',
                                 'learnspam',
                                 'learn-spam',
                                 'queue'):
        msg_list = archivemymail.server.search(['NOT', 'DELETED'])
        if len(msg_list) <= 0:
            disposition['mbox_deleted'] = True
            if archivemymail.config.dry_run:
                logging.info("Would delete now-empty folder %s", mbox_name)
            else:
                logging.debug("Deleting now-empty folder %s")
                try:
                    archivemymail.server.select_folder('INBOX')
                    archivemymail.server.unsubscribe_folder(mbox_name)
                    archivemymail.server.delete_folder(mbox_name)
                except imaplib.IMAP4.abort:
                    (exc_type, exc_value, _) = sys.exc_info()
                    logging.warning("EXCEPTION processing message %d: %s - %s" % (msg_num, exc_type, exc_value))
                    logging.warning("Attempting reconnection")
                    archivemymail.server.reconnect()

    archivemymail.server.close_folder()
    archivemymail.mboxman.close()

    return disposition
