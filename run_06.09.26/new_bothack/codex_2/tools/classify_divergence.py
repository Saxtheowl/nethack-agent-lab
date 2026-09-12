#!/usr/bin/env python3
"""Turn a raw byte offset into "which command did each bot send".

BotHack punctuates every action with its screen-sync sequence (`##'` then
`\\x08\\n\\n` then three ^P), so splitting the keystroke stream on `##'` yields
one token per command.  Comparing tokens instead of bytes says *what* the two
bots did differently, which is what decides where to look in the code.
"""
import re
import struct
import sys

SYNC = b"##'"


def tap_keys(path):
    d = open(path, 'rb').read()
    out, i = bytearray(), 0
    while i + 5 <= len(d):
        k = d[i:i + 1]
        n = struct.unpack('<I', d[i + 1:i + 5])[0]
        if k == b'I':
            out += d[i + 5:i + 5 + n]
        i += 5 + n
    return bytes(out)


def tokens(stream):
    """Split into commands, dropping the sync noise."""
    raw = stream.split(SYNC)
    out = []
    for t in raw:
        t = t.lstrip(b'\x08\n').lstrip(b'\x10')
        t = t.replace(b'\x10', b'').replace(b'\x08\n\n', b'')
        if t:
            out.append(t)
    return out


def describe(tok):
    """Name the command a token starts with."""
    if not tok:
        return "(sync)"
    m = re.match(rb'^;((?:[HKhjkl])+)\.', tok)
    if m:
        path = m.group(1)
        x = path.count(b'l')
        y = path.count(b'j') + 1
        return "farlook -> (%d,%d)" % (x, y)
    m = re.match(rb'^_?-?((?:[HKhjkl])+)\.', tok)
    if m and len(m.group(1)) > 6:
        path = m.group(1)
        return "travel -> (%d,%d)" % (path.count(b'l'), path.count(b'j') + 1)
    names = {b'i': 'inventory', b'\\': 'discoveries', b':': 'look here',
             b's': 'search', b'e': 'eat', b',': 'pickup', b'#': 'extended',
             b'w': 'wield', b'W': 'wear', b'q': 'quaff', b'r': 'read',
             b't': 'throw', b'a': 'apply', b'z': 'zap', b'E': 'engrave',
             b'>': 'descend', b'<': 'ascend', b'^': 'identify trap',
             b'p': 'pay', b'D': 'multidrop', b'd': 'drop', b'P': 'put on',
             b'T': 'take off', b'R': 'remove', b'o': 'open', b'c': 'close',
             b'k': 'move N', b'j': 'move S', b'h': 'move W', b'l': 'move E',
             b'y': 'move NW', b'u': 'move NE', b'b': 'move SW',
             b'n': 'move SE', b' ': '(space)', b'\n': '(enter)'}
    head = tok[:1]
    label = names.get(head, repr(head.decode('latin-1')))
    return "%s %r" % (label, tok[:24].decode('latin-1'))


def main():
    a, b = tap_keys(sys.argv[1]), sys.argv[2]
    b = open(b, 'rb').read() if not b.endswith('.log') else tap_keys(b)
    ta, tb = tokens(a), tokens(b)
    n = min(len(ta), len(tb))
    i = next((k for k in range(n) if ta[k] != tb[k]), None)
    if i is None:
        print("IDENTICAL over %d commands" % n)
        return 0
    print("first differing command: #%d of %d" % (i, len(ta)))
    for k in range(max(0, i - 3), min(n, i + 3)):
        mark = ">>" if k == i else "  "
        print("%s %5d  orig: %-34s port: %s"
              % (mark, k, describe(ta[k]), describe(tb[k])))
    return 1


if __name__ == '__main__':
    sys.exit(main())
