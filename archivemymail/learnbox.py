#!env python3

import email
import imaplib
import logging
import mailbox
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

    p = archivemymail.Progress(len(msg_list), learning=True)

    for msg_num in msg_list:
        try:
            imapmessage = archivemymail.server.fetch(msg_num, 'RFC822')[msg_num][b'RFC822']
            try:
                fp = email.parser.BytesFeedParser()
                fp.feed(imapmessage)
            except AttributeError:
                fp = email.parser.FeedParser()
                fp.feed(imapmessage)
            message = mailbox.mboxMessage(fp.close())

            p.log(message, mbox, spamham == 'spam')
            if archivemymail.config.dry_run:
                logging.info('Would learn %s folder: %s', spamham, mbox)
            else:
                logging.debug('Learning %s folder: %s', spamham, mbox)
                try:
                    m = message.as_bytes()
                except AttributeError:
                    m = message.as_string()
                sub = archivemymail.subprocess(['sa-learn', '--{}'.format(spamham),
                                                         '--no-sync', '--dbpath', archivemymail.config.bayes_dir],
                                                        input=m)
                sub.check()
        except imaplib.IMAP4.abort:
            (exc_type, exc_value, _) = sys.exc_info()
            logging.warning("EXCEPTION processing message %d: %s - %s" % (msg_num, exc_type, exc_value))
            logging.warning("Attempting reconnection")
            archivemymail.server.reconnect()
        except KeyboardInterrupt:
            raise
        except:
            (exc_type, exc_value, _) = sys.exc_info()
            logging.warning("EXCEPTION processing message %d: %s - %s" % (msg_num, exc_type, exc_value))
            logging.warning("Skipping to next message")
