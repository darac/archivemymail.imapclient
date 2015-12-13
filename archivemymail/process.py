#!env python3

from imapclient import IMAPClient

import archivemymail


def process(account):
    (user, password) = account.split(':', 1)

    # Start by logging in
    server = IMAPClient(archivemymail.config.server, ssl=True)
    server.login(user, password)
