import subprocess as sp

import imapclient


class subprocess:
    def __init__(self, cmd, stdin=None, input=None, check=False):
        try:
            if input is not None:
                self.obj = sp.run(cmd, input=input, check=check)
            else:
                self.obj = sp.run(cmd, stdin=stdin, check=check)
        except AttributeError:
            # Fall back to Python2 semantics
            print(dir(sp))
            self.obj = sp.Popen(cmd, stdin=stdin)
            self.obj.communicate(input)
            if check:
                self.check()

    def check(self):
        if self.obj is None:
            return
        try:
            self.obj.check_returncode()
        except AttributeError:
            if self.obj.returncode:
                raise sp.CalledProcessError(self.obj.returncode, self.obj.args)


class IMAPClient(imapclient.IMAPClient):
    def reconnect(self):
        try:
            self.shutdown()
        except:
            pass

        self._imap = self._create_IMAP4()
        self._imap._mesg = self._log
        self._idle_tag = None

        self._set_timeout()
