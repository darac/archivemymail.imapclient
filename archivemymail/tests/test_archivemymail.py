#!env python3

import archivemymail
import archivemymail.StatsMan

def test_format_size():
    test_data = [
        [-1,              "-1  bytes"],
        [0,                "0  bytes"],
        [1,                "1  byte "],
        [10,              "10  bytes"],
        [1023,          "1023  bytes"],
        [1024,          "1024  bytes"],
        [1025,          "1025  bytes"],
        [1535,          "1535  bytes"],
        [1536,             "1 kbytes"],
        [1537,             "1 kbytes"],
        [1234,          "1234  bytes"],
        [1234567,       "1205 kbytes"],
        [1234567890,    "1177 Mbytes"],
        [1234567890123, "1149 Gbytes"]
        ]

    for t in test_data:
        assert archivemymail.StatsMan.format_size(t[0]) == t[1]
