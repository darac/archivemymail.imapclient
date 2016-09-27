import pytest
import email

import archivemymail

test_message1 = email.message.Message()
test_message1['Subject'] = "test"

class imapserver():
    def __init__(self):
        pass

    def select_folder(self, mbox, readonly):
        assert readonly == True

    def search(self, criteria):
        assert criteria == ['NOT', 'DELETED']
        return [1, 2, 3]

    def fetch(self, messages, data, modifiers=None):
        assert data == 'RFC822'
        return {1: {'RFC822': test_message1},
                2: {'RFC822': test_message1},
                3: {'RFC822': test_message1}}

class spamProgress:
    def __init__(self, total, learning):
        assert total > 1
        assert learning == True

    def log(self, message, box, is_spam):
        assert is_spam == True
        assert box == 'foospam'
        assert message == test_message1

class hamProgress:
    def __init__(self, total, learning):
        assert total > 1
        assert learning == True

    def log(self, message, box, is_spam):
        assert is_spam == False
        assert box == 'foo'
        assert message == test_message1
        
class myprocess:
    def __init__(self, args, input=None):
        assert 'sa-learn' in args
        assert '--ham' in args or '--spam' in args
        try:
            assert input == test_message1.as_bytes()
        except AttributeError:
            assert input == test_message1.as_string()

    def check(self):
        return True

def test_learnbox(monkeypatch, caplog):

    
    archivemymail.server = imapserver()
    archivemymail.config.bayes_dir = "."
    monkeypatch.setattr('archivemymail.progress.Progress', spamProgress)
    monkeypatch.setattr('archivemymail.wrappers.subprocess', myprocess)

    archivemymail.config.dry_run = True
    archivemymail.learnbox('foospam')
    assert "Would learn spam folder: foospam" in caplog.text

    archivemymail.config.dry_run = False
    archivemymail.learnbox('foospam')
    assert "Learning spam folder: foospam" in caplog.text
    
    monkeypatch.setattr(archivemymail.progress, 'Progress', hamProgress)
    archivemymail.config.dry_run = True
    archivemymail.learnbox('foo')
    assert "Would learn ham folder: foo" in caplog.text
