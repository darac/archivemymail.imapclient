#!env python3

import StatsMan


def test_format_size():
    in_bytes = [-1, 0, 1, 10,
                1023, 1024, 1025,
                1535, 1536, 1537,
                1234, 1234567, 1234567890, 1234567890123]
    out_string = ["-1  bytes", "0  bytes", "1  bytes", "10  bytes",
                  "1023  bytes", "1024  bytes", "1025  bytes",
                  "1535  bytes", "1 kbytes", "1 kbytes",
                  "1234  bytes", "1205 kbytes", "1177 Mbytes", "1149 Gbytes"]

    for t in range(len(in_bytes)):
        assert StatsMan.format_size(in_bytes[t]) == out_string[t]
