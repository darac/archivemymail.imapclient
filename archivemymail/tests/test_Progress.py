# vim: set fileencoding=utf8 :
import pytest
import email

import archivemymail

test_message1 = email.message.Message()
test_message1['Subject'] = "Test subject"

test_message2 = email.message.Message()
test_message2['Subject'] = u"☺"

class TestProgress:

    @pytest.mark.parametrize("total,isatty,width", [
        (1,   False, None),
        (10,  False, None),
        (100, False, None),
        (1,   True,  1),
        (5,   True,  1),
        (10,  True,  2),
        (50,  True,  2),
        (99,  True,  2),
        (100, True,  3),
    ])
    def test_defaults(self, monkeypatch, total, isatty, width):
        def myisatty(fileno):
            assert fileno is not None
            return isatty

        monkeypatch.setattr("os.isatty", myisatty)

        # Call the UUT
        p = archivemymail.Progress(total)


        assert p.total == total
        assert p.field_width == width
        assert p.num == 0

    def test_log(self, monkeypatch, caplog):
        def myparse(msg, right=None, left=None):
            assert right == 50
            return "Test subject"

        def badparse(msg, right=None, left=None):
            assert right == 50
            raise TypeError
            
        p = archivemymail.Progress(5)

        p.field_width = None
        p.num = 1
        monkeypatch.setattr("archivemymail.parse_header", myparse)

        p.log(message=test_message1, box="foo", is_spam=False)

        assert p.num == 2
        assert u"[HAM ] Test subject                                       → foo" in caplog.text

        p.log(message=test_message1, box="bar", is_spam=True)

        assert p.num == 3
        assert u"[SPAM] Test subject                                       → bar" in caplog.text

        p.field_width=2
        p.log(message=test_message1, box="foo", is_spam=False)

        assert p.num == 4
        assert u"( 4/ 5) [HAM ] Test subject                                       → foo" in caplog.text

        monkeypatch.setattr("archivemymail.parse_header", badparse)
        p.log(message=test_message2, box="foo", is_spam=False)

        assert p.num == 5
        assert u"( 5/ 5) [HAM ] <No Subject>                                       → foo" in caplog.text
