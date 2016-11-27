import imaplib
import imapclient

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
