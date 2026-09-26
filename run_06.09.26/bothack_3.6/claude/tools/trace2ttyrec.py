#!/usr/bin/env python3
"""Turn a recorded protocol trace (rungame --record / --protocol-trace) into a
ttyrec that `ttyplay` can show, like the ttyrecs of the 3.4.3 BotHack port.

    python3 tools/trace2ttyrec.py runs/replays/g011/protocol.trace.gz \
        runs/replays/g011.ttyrec
    ttyplay runs/replays/g011.ttyrec        # '+'/'-' speed, space pause

The engine has no terminal (window port "bot"), so the screen is rebuilt from
the protocol: row 0 = last message, rows 1-21 = map (engine y + 1), rows
22-23 = status lines.  Only changed cells are written (cursor addressing), so
a 50000-turn game stays small.  Time: DELAY seconds per frame (default 0.03),
TURN_DELAY extra seconds when the game turn advances.
"""
import gzip
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DELAY = float(os.environ.get('DELAY', '0.03'))
TURN_DELAY = float(os.environ.get('TURN_DELAY', '0.0'))

# NetHack colour -> ANSI SGR (NO_COLOR/gray -> default white)
ANSI = {0: '34', 1: '31', 2: '32', 3: '33', 4: '34', 5: '35', 6: '36',
        7: '37', 8: '37', 9: '91', 10: '92', 11: '93', 12: '94', 13: '95',
        14: '96', 15: '97'}
ALIGN = {-1: 'Chaotic', 0: 'Neutral', 1: 'Lawful'}
HUNGER = {0: 'Satiated', 2: 'Hungry', 3: 'Weak', 4: 'Fainting', 5: 'Fainted'}
COND = [(0x01, 'Stone'), (0x02, 'Slime'), (0x04, 'Strngl'),
        (0x08, 'FoodPois'), (0x10, 'TermIll'), (0x20, 'Blind'),
        (0x40, 'Deaf'), (0x80, 'Stun'), (0x100, 'Conf'), (0x200, 'Hallu'),
        (0x400, 'Lev'), (0x800, 'Fly'), (0x1000, 'Ride')]


def str_string(v):
    if isinstance(v, str):
        return v
    if v is None:
        return '?'
    if v <= 18:
        return str(v)
    if v <= 117:
        return '18/%02d' % (v - 18)
    if v == 118:
        return '18/**'
    return str(v - 100)


def status_lines(st):
    a = "%s the %s  St:%s Dx:%s Co:%s In:%s Wi:%s Ch:%s  %s" % (
        'bot', st.get('title', '?'), str_string(st.get('str')),
        st.get('dex'), st.get('con'), st.get('int'), st.get('wis'),
        st.get('cha'), ALIGN.get(st.get('align'), ''))
    cond = [n for bit, n in COND if (st.get('cond') or 0) & bit]
    hunger = HUNGER.get(st.get('hunger'))
    b = "%s $:%s HP:%s(%s) Pw:%s(%s) AC:%s Xp:%s/%s T:%s %s %s" % (
        (st.get('lvl') or '').strip(), st.get('gold'), st.get('hp'),
        st.get('hpmax'), st.get('pw'), st.get('pwmax'), st.get('ac'),
        st.get('xl'), st.get('exp'), st.get('turn'), hunger or '',
        ' '.join(cond))
    return a[:79], b[:79]


class Screen(object):
    def __init__(self):
        self.cells = [[(' ', None)] * 80 for _ in range(24)]
        self.shown = [[(' ', None)] * 80 for _ in range(24)]

    def put_text(self, row, text):
        text = (text or '')[:80].ljust(80)
        for x, c in enumerate(text):
            self.cells[row][x] = (c, None)

    def flush(self):
        out = []
        cur_color = 'x'
        for y in range(24):
            for x in range(80):
                c = self.cells[y][x]
                if c != self.shown[y][x]:
                    out.append('\x1b[%d;%dH' % (y + 1, x + 1))
                    col = c[1]
                    if col != cur_color:
                        out.append('\x1b[0m' if col is None
                                   else '\x1b[0;%sm' % col)
                        cur_color = col
                    out.append(c[0])
                    self.shown[y][x] = c
        if out:
            out.append('\x1b[0m')
        return ''.join(out)


def _safe_lines(f):
    """A game still running (or killed) leaves a gzip stream without its end
    marker: replay what is there instead of failing."""
    try:
        for line in f:
            yield line
    except (EOFError, OSError) as e:
        sys.stderr.write("note: trace truncated (%s) - game still running or "
                         "interrupted; replaying what was recorded\n" % e)


def frames(path):
    opener = gzip.open if path.endswith('.gz') else open
    scr = Screen()
    last_msg = ''
    turn = None
    with opener(path, 'rt', errors='replace') as f:
        for line in _safe_lines(f):
            if not line.startswith('{'):
                continue            # "> answer" lines
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get('t') not in ('req', 'end'):
                continue
            for e in d.get('ev') or []:
                if e and e[0] == 'msg':
                    last_msg = e[1]
            for cell in d.get('map') or []:
                x, y, glyph, ch, color = cell[:5]
                if 0 <= x < 80 and 0 <= y < 21:
                    c = chr(ch) if 32 <= ch < 127 else ' '
                    scr.cells[y + 1][x] = (c, ANSI.get(color) if c != ' '
                                           else None)
            st = d.get('st')
            if st:
                a, b = status_lines(st)
                scr.put_text(22, a)
                scr.put_text(23, b)
            scr.put_text(0, last_msg)
            if d.get('t') == 'end':
                scr.put_text(0, "*** %s after %s turns ***"
                             % (d.get('how_s'), d.get('turns')))
            data = scr.flush()
            new_turn = (st or {}).get('turn', turn)
            extra = TURN_DELAY if (turn is not None and new_turn != turn) else 0
            turn = new_turn
            if data:
                yield DELAY + extra, data


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    src, dst = sys.argv[1], sys.argv[2]
    t = 0.0
    n = 0
    with open(dst, 'wb') as out:
        head = '\x1b[H\x1b[2J'.encode()
        out.write(struct.pack('<III', 0, 0, len(head)) + head)
        for dt, data in frames(src):
            t += dt
            b = data.encode('utf-8', 'replace')
            sec = int(t)
            out.write(struct.pack('<III', sec, int((t - sec) * 1e6), len(b)))
            out.write(b)
            n += 1
    print("%s: %d frames, %.0f s at 1x" % (dst, n, t))


if __name__ == '__main__':
    main()
