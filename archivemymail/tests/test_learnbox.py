import email
import mailbox

import archivemymail

test_message1 = email.message.Message()
test_message1['Subject'] = "test"


class imapserver:
    def __init__(self, num_messages):
        self.num_messages = num_messages
        self.curr_message = 0

    @staticmethod
    def select_folder(mbox, readonly):
        assert readonly is True

    def search(self, criteria):
        assert criteria == ['NOT', 'DELETED']
        return [i for i in range(self.num_messages)]

    def fetch(self, num, searchterms, modifiers=None):
        assert num >= 0
        assert num <= self.num_messages
        assert searchterms == 'RFC822'
        assert modifiers is None
        msg = {}
        msg[b'FLAGS'] = ()
        try:
            msg[b'RFC822'] = test_message1.as_bytes()
        except AttributeError:
            msg['RFC822'] = test_message1.as_string()
        self.curr_message = num

        return {num: msg}


class spamProgress:
    def __init__(self, total, learning):
        assert total > 1
        assert learning is True

    @staticmethod
    def log(message, box, is_spam):
        assert is_spam is True
        assert box == 'foospam'
        assert isinstance(message, mailbox.mboxMessage)


class hamProgress:
    def __init__(self, total, learning):
        assert total > 1
        assert learning is True

    @staticmethod
    def log(message, box, is_spam):
        assert is_spam is False
        assert box == 'foo'
        assert isinstance(message, mailbox.mboxMessage)


class myprocess:
    def __init__(self, args, input=None):
        assert 'sa-learn' in args
        assert '--ham' in args or '--spam' in args
        try:
            assert input == test_message1.as_bytes()
        except AttributeError:
            assert input == test_message1.as_string()

    @staticmethod
    def check():
        return True


def test_learnbox(monkeypatch, caplog):
    archivemymail.server = imapserver(3)
    archivemymail.config.bayes_dir = "."
    monkeypatch.setattr(archivemymail, 'Progress', spamProgress)
    monkeypatch.setattr(archivemymail, 'subprocess', myprocess)

    archivemymail.config.dry_run = True
    archivemymail.learnbox('foospam')
    assert "Would learn spam folder: foospam" in caplog.text

    archivemymail.config.dry_run = False
    archivemymail.learnbox('foospam')
    assert "Learning spam folder: foospam" in caplog.text

    monkeypatch.setattr(archivemymail, 'Progress', hamProgress)
    archivemymail.config.dry_run = True
    archivemymail.learnbox('foo')
    assert "Would learn ham folder: foo" in caplog.text
