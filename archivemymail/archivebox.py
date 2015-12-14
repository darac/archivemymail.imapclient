#!env python3

import logging

import archivemymail


def archivebox(mbox):
    disposition = 0

    (flags, delimiter, mbox_name) = mbox

    # Don't archive boxes in the archive
    if mbox_name.startswith("Archive") or \
            mbox_name.startswith("_ARCHIVE"):
        return disposition

    # If a box can't be selected, it can't be archived
    if b'\NoSelect' in flags:
        return disposition

    logging.info("")
    logging.info("====== %s ======", mbox_name)

    archivemymail.server.select_folder(mbox_name)
    msg_list = archivemymail.server.search(['OLD', 'BEFORE', '{:%d-%b-%Y}'.format(archivemymail.archivedate)])
