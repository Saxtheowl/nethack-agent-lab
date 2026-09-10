#!/usr/bin/env python3
"""Did the two bots act on the same redraw?

The tap interleaves what the game sent with what the bot wrote, in real time,
so it records the original's alignment exactly: the screen standing when an `I`
record appears is the screen the original was looking at when it wrote those
bytes.  Walking the tap therefore gives (keystroke offset -> screen) for the
original with no JVM and no guessing.

Comparing that with the port's screen at the *same* keystroke offset separates
two very different faults:

  * screens differ at the same offset -> the port is a redraw out of step, i.e.
    the harness or the terminal, not the bot's reasoning;
  * screens agree -> the port read the same pixels and decided differently.

It matters most under hallucination, where NetHack re-randomises every monster
glyph on every redraw: being one redraw apart then looks like a completely
different monster set, and is easy to misread as a logic bug.

    tools/align_check.py TAP X Y [--from N] [--to N]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import tapio                                        # noqa: E402
from pybothack import term as T                                # noqa: E402


def original_view(tap, x, y, lo, hi):
    """[(keystroke offset, glyph at (x,y), row slice)] for the original."""
    recs = tapio.read_records(tap)
    scr = T.Terminal()
    keys = 0
    out = []
    pending_write = False
    for kind, data in recs:
        if kind == 'O':
            # JTA reads at most 256 bytes and redraws once per read
            for i in range(0, len(data), 256):
                scr.feed(data[i:i + 256])
            pending_write = True
            continue
        # an I record: this is what the bot wrote while looking at `scr`
        if pending_write and lo <= keys <= hi:
            f = scr.frame()
            out.append((keys, f.lines[y - 1][x], f.lines[y - 1][max(0, x - 6):
                                                               x + 7],
                        (f.cursor.x, f.cursor.y), data[:12]))
        pending_write = False
        keys += len(data)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tap')
    ap.add_argument('x', type=int)
    ap.add_argument('y', type=int)
    ap.add_argument('--from', dest='lo', type=int, default=0)
    ap.add_argument('--to', dest='hi', type=int, default=1 << 60)
    a = ap.parse_args()
    rows = original_view(a.tap, a.x, a.y, a.lo, a.hi)
    print('original: %d write(s) in [%s, %s]' % (len(rows), a.lo, a.hi))
    for keys, ch, row, cur, wrote in rows:
        print('  keys=%-7d (%d,%d)=%r row=%r cursor=%s wrote=%r'
              % (keys, a.x, a.y, ch, row, cur, wrote))
    return 0


if __name__ == '__main__':
    sys.exit(main())
