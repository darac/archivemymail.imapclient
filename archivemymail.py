#!env python3

import argparse

import archivemymail

archivemymail.config.load()

if archivemymail.config['debug']:
    logging.basicConfig(level=logging.DEBUG,
            format="%(message)s",
            stream=sys.stdout)
elif os.isatty(sys.stdout.fileno()):
    logging.basicConfig(level=logging.INFO,
            format="%(message)s",
            stream=sys.stdout)
else:
    logging.basicConfig(level=logging.WARNING,
            format="%(message)s",
            stream=sys.stdout)

logging.info ("Archiving mails received before {:%A %d %B %Y}".format(testday))

for account in archivemymail.config['accounts']:
    archivemymail.process(account)

archivemymail.statsman.summarise()
