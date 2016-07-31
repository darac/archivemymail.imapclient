#!env python3

import datetime
import math
import sqlite3
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import archivemymail


def format_size(bytes_):
    if bytes_ == 1:
        return "%d  byte " % bytes_
    elif bytes_ < 1024 * 1.5:  # 1.5 kb
        return "%d  bytes" % bytes_
    elif bytes_ < 1024 * 1024 * 1.5:  # 1.5 Mb
        return "%d kbytes" % math.floor(bytes_ / 1024)
    elif bytes_ < 1024 * 1024 * 1024 * 1.5:  # 1.5 Gb
        return "%d Mbytes" % math.floor(bytes_ / (1024 * 1024))
    else:
        return "%d Gbytes" % math.floor(bytes_ / (1024 * 1024 * 1024))


class StatsManClass:
    def __init__(self):
        self.conn = sqlite3.connect('')
        self.conn.text_factory = str
        self.cur = self.conn.cursor()
        self.cur.execute('''CREATE TABLE imapboxes
         (user text, imapbox text)''')
        self.cur.execute('''CREATE UNIQUE INDEX IF NOT EXISTS boxname ON imapboxes (user, imapbox)''')
        self.cur.execute('''CREATE TABLE data (
                user text,
                imapbox text,
                mbox text,
                sender text,
                subject text,
                date text,
                size integer,
                foreign key(user) references imapboxes(user),
                foreign key(imapbox) references imapboxes(imapbox))''')
        self.imapbox = None
        self.user = None

    def newbox(self, user, box):
        try:
            self.cur.execute('''INSERT INTO imapboxes (user, imapbox)
             VALUES (?,?)''', (user, box))
        except sqlite3.IntegrityError:
            pass
        self.imapbox = box
        self.user = user

    def add(self, message, box=None):
        if self.user is None:
            raise RuntimeError("Can't add without a username")
        if box is None:
            box=self.imapbox
        boxes = self.cur.execute ('''
            SELECT imapbox FROM imapboxes WHERE user=? AND imapbox=?
            ''', (self.user, box)).fetchall()
        if len(boxes) != 1:
            self.newbox(user=self.user, box=box)
        self.cur.execute('''INSERT INTO data
                (user, imapbox, mbox, sender, subject, date, size)
                VALUES (?,?,?,?,?,?,?)''',
                         (self.user,
                          self.imapbox,
                          box,
                          message['From'],
                          message['Subject'],
                          message['Date'],
                          len(message.as_string())))

    @staticmethod
    def text_header(text, underline='='):
        return "{}\n{}\n".format(text, underline * len(text))

    def summarise(self):
        text = self.text_header(
                "archivemymail report for {:%A %d %B %Y}".format(datetime.date.today()))
        html = '''
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width"/>
    <style type="text/css">
'''
        with open('ZurbInk/ink.css', 'r') as f:
            html += f.readlines()

        html += '''
  </head>
  <body style="background:Thistle">
    <table class="body" style="background:Thistle">
      <tr>
        <td class="center" align="center" valign="top">
          <center>
            <table class="container"><tr><td>
'''

        for user in self.cur.execute("SELECT DISTINCT user FROM imapboxes"):
            text += self.text_header("User: {}".format(user[0]), underline='-')
            html += '''\
<table class="user row"><tr><td class="wrapper last">
  <table class="twelve columns"><tr><td class="text-pad">
    <h2>User: {}</h2>
  </td><td class="expander"/></tr></table>
</td></tr></table>\n'''.format(user[0])
            for imapbox in self.cur.execute(
                    "SELECT DISTINCT imapbox FROM imapboxes WHERE user=?",
                    user):
                text += self.text_header(
                        "Folder: {}".format(imapbox[0]), underline='-')
                text += ("{:30} {:30} {:30} {:11}\n"
                         .format('Sender', 'Subject', 'Filed to', 'Size'))
                html += '''\
<table class="mailbox row"><tr><td class="wrapper last">
  <table class="twelve columns"><tr><td class="text-pad">
    <h3>Folder: {}</h3>
  </td><td class="expander"/></tr></table>
</td></tr></table>\n'''.format(imapbox[0])
                html += '''\
<table class="header row"><tr>
  <td class="wrapper">
    <table class="four columns"><tr>
      <td class="text-pad">Sender</td>
      <td class="expander"/>
    </tr></table>
  </td>
  <td class="wrapper">
    <table class="three columns"><tr>
      <td class="text-pad">Subject</td>
      <td class="expander"/>
    </tr></table>
  </td>
  <td class="wrapper">
    <table class="three columns"><tr>
      <td class="text-pad">Filed to</td>
      <td class="expander"/>
    </tr></table>
  </td>
  <td class="wrapper last">
    <table class="two columns"><tr>
      <td class="text-pad">Size</td>
      <td class="expander"/>
    </tr></table>
  </td>
</tr></table>\n'''
                boxsize = 0
                evenrow = True
                for message in self.cur.execute('''
                        SELECT sender, subject, date, size, mbox
                        FROM data
                        WHERE user=? AND imapbox=?''', (user[0], imapbox[0])):
                    text += "{:.<30} {:.<30} {:.<30} {:<11}\n".format(
                            message[0][-30:],
                            archivemymail.parse_subject(message[1], left=-30),
                            message[4][-30:],
                            format_size(message[3]))
                    if evenrow:
                        html += '<table class="even row"><tr>'
                    else:
                        html += '<table class="odd row"><tr>'
                    evenrow = not evenrow
                    for h in (['four', message[0]],
                              ['three', archivemymail.parse_subject(message[1])],
                              ['three', message[4]],
                              ['two', format_size(message[3])]):
                        html += '''\
<td class="wrapper">
  <table class="{0[0]} columns"><tr>
    <td class="text-pad">{0[1]}</td>
    <td class="expander"/>
  </tr></table>
</td>\n'''.format(h)
                    html += '</tr></table>'
                    boxsize += message[3]
                # End of imapbox
                text += "{:.>104}".format(
                        "Total Uncompressed Size: " + format_size(boxsize))
                html += '''\
<table class="total row"><tr>
  <td class="wrapper last">
    <table class="twelve columns"><tr>
      <td class="text-pad">{}</td>
    </tr></table>
  </td></tr>
</table>\n'''.format("Total Uncompressed Size: " + format_size(boxsize))
            # End of user
            html += '</td></tr></table>'
        # End of message
        html += '''\
          </center>
        </td>
      </tr>
    </table>
  </body>
</html>
'''

        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'archivemymail report for ' + \
                         datetime.date.today().strftime("%A %d %B %Y")
        msg['From'] = 'root'
        msg['To'] = 'root'
        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))
        p = subprocess.Popen(["/usr/sbin/sendmail", "-t", "-oi"],
                             stdin=subprocess.PIPE)
        p.communicate(msg.as_string())
