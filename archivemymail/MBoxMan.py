#!env python3

import os
import subprocess


class NullBox:
    def __init__(self):
        pass

    def unlock(self):
        pass


class MBoxMan:
    def __init__(self, user, boxroot, statsman, dryrun=True, compression='gz'):
        self.user = (user.split('@', 1))[0]  # Strip off '@...'
        self.boxroot = boxroot
        self.statsman = statsman
        self.dryrun = dryrun
        self.compression = compression

        self.currentbox = None
        self.boxpath = None
        self.spambox = False

    def __del__(self):
        # Unlock any locked boxes
        self.currentbox.unlock()

    def _deoompress(self, fullpath):
        if os.path.exists(fullpath):
            # Already decompressed
            return
        elif os.path.exists(fullpath + '.gz'):
            subprocess.run(  # TODO )

    def setbox(self, path, spambox=False):
        if self.currentbox is not None:
            if self.boxpath != path:
                # Change of box
                self.close()
                self.open(path)
            else:
                # Setting to the current box; nothing to do
                pass
        else:
            # New box
            self.open(path)
        self.statsman.newbox(self.user, path)
        self.spambox = spambox
        return self.currentbox

    def open(self, path):
        self.boxpath = path
        fullpath = os.path.join(self.boxroot, self.boxpath)
        if not os.path.exists(os.path.dirname(fullpath)) and not self.dryrun:
            os.makedirs(os.path.dirname(fullpath))
        log_msg = "Opening "
        if os.path.exists(fullpath + '.gz')
