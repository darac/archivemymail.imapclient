# !env python3

import logging
import mailbox
import os

import archivemymail
import archivemymail.wrappers

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError
    FileExistsError = IOError


class NullBoxClass:
    def __init__(self, path):
        self.path = path
        pass

    def lock(self):
        pass

    def unlock(self):
        pass

    def add(self, message):
        pass

    def close(self):
        pass

    def __iter__(self):
        return self

    @staticmethod
    def __next__():
        raise StopIteration

    @staticmethod
    def next():
        raise StopIteration


class MBoxManClass:
    def __init__(self, user, boxroot, statsman, dryrun=True, compression='gz'):
        self.user = (user.split('@', 1))[0]  # Strip off '@...'
        self.boxroot = boxroot
        self.statsman = statsman
        self.dryrun = dryrun
        self.compression = compression

        self.currentbox = None
        self.boxpath = None
        self.spambox = False
        self.msgids = []

    def __del__(self):
        # Unlock any locked boxes
        if self.currentbox is not None:
            self.currentbox.unlock()

    @staticmethod
    def _decompress(fullpath):

        ret = None
        if os.path.exists(fullpath):
            # Already decompressed
            return
        elif os.path.exists(fullpath + '.gz'):
            logging.debug('GZip decompressing...')
            ret = archivemymail.wrappers.subprocess(['gzip', '-d', fullpath + '.gz'])
        elif os.path.exists(fullpath + '.bz2'):
            logging.debug('BZip decompressing...')
            ret = archivemymail.wrappers.subprocess(['bzip2', '-d', fullpath + '.bz2'])
        elif os.path.exists(fullpath + '.xz'):
            logging.debug('XZip decompressing...')
            ret = archivemymail.wrappers.subprocess(['xz', '-d', fullpath + '.xz'])
        elif os.path.exists(fullpath + '.lz4'):
            logging.debug('LZip decompressing...')
            ret = archivemymail.wrappers.subprocess(['lzop', '-d', fullpath + '.lz4'])
        if ret is not None:
            ret.check()

    @staticmethod
    def _compress(fullpath, compression):
        if not os.path.exists(fullpath):
            raise FileNotFoundError
        if compression == 'gz' or compression == 'gzip':
            compressor = 'gzip'
            extension = 'gz'
        elif compression == 'bz2' or compression == 'bz' or compression == 'bzip2' or compression == 'bzip':
            compressor = 'bzip2'
            extension = 'bz2'
        elif compression == 'xz' or compression == 'xzip':
            compressor = 'xz'
            extension = 'xz'
        elif compression == 'lz' or compression == 'lzip' or compression == 'lz4':
            compressor = 'lzop'
            extension = 'lz4'
        else:
            # No compression called for
            return

        if os.path.exists(fullpath + '.' + extension):
            raise FileExistsError

        logging.debug('Compressing {f} -> {f}.{e}'.format(f=fullpath, e=extension))
        archivemymail.wrappers.subprocess([compressor, '-9', fullpath])

    def set_box(self, path, spambox=False):
        if self.currentbox is not None:
            if self.boxpath != path:
                # Change of box
                self.close()
                self.open(path)
                # ELSE Setting to the current box; nothing to do
        else:
            # New box
            self.open(path)
        self.statsman.new_box(self.user, path)
        self.spambox = spambox
        return self.currentbox

    def open(self, path):
        self.boxpath = path
        fullpath = os.path.join(self.boxroot, self.boxpath)
        if not os.path.exists(os.path.dirname(fullpath)) and \
                not self.dryrun:
            # Create the target directory, if necessary
            os.makedirs(os.path.dirname(fullpath))

        logging.debug('Opening %s', fullpath)
        if self.dryrun:
            self.currentbox = NullBoxClass(path)
        else:
            self._decompress(fullpath)
            self.currentbox = mailbox.mbox(path)
        try:
            self.currentbox.lock()
        except mailbox.ExternalClashError:
            self.currentbox.unlock()
            self.currentbox.lock()

        # Scan the box, reading Message-IDs
        self.msgids = []
        for m in self.currentbox:
            self.msgids.append(m['Message-Id'])

    def add(self, message):
        if 'Message-ID' in message and \
                        message['Message-ID'] not in self.msgids:
            self.currentbox.add(message)
            self.msgids.append(message['Message-ID'])
        elif 'Message-ID' not in message:
            # If the message being added has no Message-ID,
            # we can't check for duplicates, so add it anyway
            self.currentbox.add(message)
        # If Message-ID in Message, but Message-ID already known,
        # DON'T add it to the box
        self.statsman.add(self.boxpath, message)

    def learn(self):
        if self.spambox:
            spamham = 'spam'
        else:
            spamham = 'ham'

        if self.dryrun:
            logging.info('Would learn %s mbox: %s', spamham, self.boxpath)
        else:
            logging.info('Learning %s mbox: %s', spamham, self.boxpath)
            ret = archivemymail.wrappers.subprocess(['sa-learn',
                                                     '--{}'.format(spamham),
                                                     '--no-sync',
                                                     '--dbpath', archivemymail.config.bayes_dir,
                                                     '--mbox', os.path.join(self.boxroot, self.boxpath)])
            ret.check()

    def close(self):
        if self.currentbox is None:
            return
        self.currentbox.unlock()
        self.currentbox.close()
        if archivemymail.config.do_learning:
            self.learn()
        if not self.dryrun:
            self._compress(os.path.join(self.boxroot, self.boxpath), archivemymail.config.compression)
