#!env python3
# vim: set foldmethod=marker:

import datetime
import math
import os
import sqlite3
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from genshi.template import TemplateLoader
from genshi.template.text import NewTextTemplate

import archivemymail

loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), 'templates'),
    auto_reload=True
)


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
        self.conn.row_factory = sqlite3.Row
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

    def new_box(self, user, box):
        try:
            self.cur.execute('''INSERT INTO imapboxes (user, imapbox)
             VALUES (?,?)''', (user, box))
        except sqlite3.IntegrityError:
            pass
        self.imapbox = box
        self.user = user

    def add(self, mbox, message):
        if self.user is None:
            raise RuntimeError("Can't add without a username")
        self.cur.execute('''INSERT INTO data
                (user, imapbox, mbox, sender, subject, date, size)
                VALUES (?,?,?,?,?,?,?)''',
                         (self.user,
                          self.imapbox,
                          mbox,
                          message['From'],
                          message['Subject'],
                          message['Date'],
                          len(message.as_string())))

    @staticmethod
    def text_header(text, underline='='):
        if len(underline) != 1:
            underline = '='
        return "{}\n{}".format(text, underline * len(text))

    def summarise(self):
        users = sorted([x[0] for x in self.cur.execute("SELECT DISTINCT user FROM imapboxes").fetchall()])
        imapboxes = {}
        messages = {}
        boxsizes = {}
        for user in users:
            imapboxes[user] = [x['imapbox'] for x in
                               self.cur.execute("SELECT DISTINCT imapbox FROM imapboxes WHERE user=?",
                                                (user,)).fetchall()]
            messages[user] = {}
            boxsizes[user] = {}
            boxsizes[user]['%'] = 0
            for imapbox in imapboxes[user]:
                messages[user][imapbox] = self.cur.execute('''
                        SELECT sender, subject, date, size, mbox
                        FROM data
                        WHERE user=? AND imapbox=?''', (user, imapbox)).fetchall()
                # messages ends up as a list of sqlite3.Row objects
                boxsize = sum(message['size'] for message in messages[user][imapbox])
                boxsizes[user][imapbox] = format_size(boxsize)
                boxsizes[user]['%'] += boxsize
            boxsizes[user]['%'] = format_size(boxsizes[user]['%'])

        tmpl = loader.load('zurbink.html')
        htmlstream = tmpl.generate(
            users=users,
            imapboxes=imapboxes,
            messages=messages,
            boxsizes=boxsizes,
            parse=archivemymail.parse_header)
        tmpl = loader.load('plaintext.txt', cls=NewTextTemplate)
        textstream = tmpl.generate(
            users=users,
            imapboxes=imapboxes,
            messages=messages,
            boxsizes=boxsizes,
            text_header=self.text_header,
            parse=archivemymail.parse_header)

        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'archivemymail report for ' + \
                         datetime.date.today().strftime("%A %d %B %Y")
        msg['From'] = 'root'
        msg['To'] = 'root'
        msg.preamble = msg['Subject']
        html = htmlstream.render('html')
        text = textstream.render('text')
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        msg.attach(MIMEText(text, 'plain', 'utf-8'))
        p = archivemymail.wrappers.subprocess(["/usr/sbin/sendmail", "-t", "-oi"], input=msg.as_string())
