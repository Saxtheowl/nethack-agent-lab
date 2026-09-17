"""Terminal emulation - the Python counterpart of bothack.term (which drives
JTA's vt320).  We use pyte for the emulation and reproduce JTA's observable
behaviour exactly:

* the reader reads at most 256 bytes per read() and JTA's vt320.putString
  emits exactly one redraw per non-empty chunk, so the scraper sees the same
  frame boundaries as the original;
* character attributes are converted with JTA's packing rules (see
  bothack.term/unpack-colors).
"""
import pyte

from .frame import Frame, COLORMAP
from .position import Pos

# JTA stores <ansi colour>+1 in the attribute field; 0 means "default".
_ANSI = {'black': 0, 'red': 1, 'green': 2, 'brown': 3, 'blue': 4,
         'magenta': 5, 'cyan': 6, 'white': 7, 'default': 0}


def _color_index(char):
    if char.reverse:
        base = _ANSI.get(char.bg, 0)
        return base + (8 if char.bold else 0) + 16
    base = _ANSI.get(char.fg, 0)
    return base + (8 if char.bold else 0)


class Terminal(object):
    def __init__(self, columns=80, lines=24):
        self.screen = pyte.Screen(columns, lines)
        self.stream = pyte.ByteStream(self.screen)
        self.columns = columns
        self.rows = lines

    def feed(self, data):
        self.stream.feed(data)

    def frame(self):
        scr = self.screen
        buf = scr.buffer
        lines = []
        colors = []
        default = scr.default_char
        for y in range(self.rows):
            row = buf[y]
            chars = []
            cols = []
            for x in range(self.columns):
                ch = row[x] if x in row else default
                c = ch.data
                chars.append(' ' if c == '\x00' or c == '' else c)
                cols.append(COLORMAP[_color_index(ch)])
            lines.append("".join(chars))
            colors.append(cols)
        return Frame(lines, colors, Pos(scr.cursor.x, scr.cursor.y))
