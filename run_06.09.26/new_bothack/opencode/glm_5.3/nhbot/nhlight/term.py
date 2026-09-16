"""Terminal emulation over the PTY byte stream.

A system read() is not evidence of a complete screen.  The terminal layer
only decodes bytes into a grid; the dialogue layer decides when a screen
is *settled* (silence + parseable state) before any decision is made.

Uses pyte as the VT engine (installed on this host); we keep our own
attribute model on top of it.
"""

import pyte

COLS = 80
ROWS = 24

# map indices 0 (message) .. 1-21 (map) .. 22-23 (status)
ROW_MESSAGE = 0
ROW_STATUS1 = 22
ROW_STATUS2 = 23

_ANSI = {
    "black": 0, "red": 1, "green": 2, "brown": 3, "yellow": 3,
    "blue": 4, "magenta": 5, "cyan": 6, "gray": 7, "grey": 7,
    "white": 7,
}


def color_index(fg, bold):
    """Packed color index: 1-7 base ANSI, +8 when bold (like JTA/BotHack)."""
    if not fg or fg == "default":
        return 0
    name = fg.replace("bright-", "")
    if name in _ANSI:
        base = _ANSI[name]
        # real "bright yellow" from bold yellow
        if fg.startswith("bright-") or (bold and base == 3 and fg == "yellow"):
            base = 3
        return (8 if bold else 0) + base + 1
    return 0


class Cell:
    __slots__ = ("ch", "color", "inverse", "bold")

    def __init__(self, ch=" ", color=0, inverse=False, bold=False):
        self.ch = ch
        self.color = color
        self.inverse = inverse
        self.bold = bold


class Screen:
    """Decoded 80x24 screen with per-cell attributes and cursor."""

    def __init__(self, cols=COLS, rows=ROWS):
        self.cols = cols
        self.rows = rows
        self._screen = pyte.Screen(cols, rows)
        self._stream = pyte.ByteStream(self._screen)
        self.reset()

    def reset(self):
        self._screen.reset()
        self._blank = [[Cell() for _ in range(self.cols)] for _ in range(self.rows)]

    def feed(self, data):
        self._stream.feed(data)

    def snapshot(self):
        """Return (lines, cells, cursor_x, cursor_y).

        lines: 24 strings; cells: 24x80 Cell objects; cursor is 0-based.
        """
        scr = self._screen
        cells = []
        lines = []
        for y in range(self.rows):
            row_cells = []
            chars = []
            buf = scr.buffer[y]
            cx = scr.cursor.x
            cy = scr.cursor.y
            for x in range(self.cols):
                c = buf.get(x)
                if c is None:
                    cell = Cell()
                else:
                    cell = Cell(
                        c.data if c.data else " ",
                        color_index(c.fg, c.bold),
                        bool(c.reverse),
                        bool(c.bold),
                    )
                row_cells.append(cell)
                chars.append(cell.ch)
            cells.append(row_cells)
            lines.append("".join(chars))
        return lines, cells, scr.cursor.x, scr.cursor.y

    # -- convenience ------------------------------------------------
    def text(self):
        lines, _, _, _ = self.snapshot()
        return lines
