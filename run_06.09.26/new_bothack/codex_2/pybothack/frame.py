"""Port of bothack.frame."""
import re
from .position import Pos

COLORMAP = [
    None, 'red', 'green', 'brown', 'blue',            # non-bold
    'magenta', 'cyan', 'gray',
    'bold', 'orange', 'bright-green', 'yellow',       # bold
    'bright-blue', 'bright-magenta', 'bright-cyan', 'white',
    'inverse', 'inverse-red', 'inverse-green', 'inverse-brown',   # inverse
    'inverse-blue', 'inverse-magenta', 'inverse-cyan', 'inverse-gray',
    'inverse-bold', 'inverse-orange', 'inverse-bright-green', 'inverse-yellow',
    'inverse-bright-blue', 'inverse-bright-magenta', 'inverse-bright-cyan',
    'inverse-white',
]

_INVERSE = {
    'inverse', 'inverse-red', 'inverse-green', 'inverse-brown', 'inverse-blue',
    'inverse-magenta', 'inverse-cyan', 'inverse-gray', 'inverse-bold',
    'inverse-orange', 'inverse-bright-green', 'inverse-yellow',
    'inverse-bright-blue', 'inverse-bright-magenta', 'inverse-bright-cyan',
    'inverse-white',
}

_NON_INVERSE = {
    'inverse-bright-green': 'bright-green', 'inverse-green': 'green',
    'inverse': None, 'inverse-brown': 'brown', 'inverse-orange': 'orange',
    'inverse-magenta': 'magenta', 'inverse-blue': 'blue',
    'inverse-bright-cyan': 'bright-cyan', 'inverse-cyan': 'cyan',
    'inverse-red': 'red', 'inverse-bold': 'white',
    'inverse-bright-magenta': 'bright-magenta', 'inverse-yellow': 'yellow',
    'inverse-bright-blue': 'bright-blue', 'inverse-gray': 'gray',
    'inverse-white': 'white',
}


def inverse(color):
    return color in _INVERSE


def non_inverse(color):
    return _NON_INVERSE.get(color, color)


class Frame(object):
    """lines: 24 strings; colors: 24 lists of 80 color keywords; cursor: Pos"""
    __slots__ = ('lines', 'colors', 'cursor')

    def __init__(self, lines, colors, cursor):
        self.lines = lines
        self.colors = colors
        self.cursor = cursor

    def __getitem__(self, k):
        return getattr(self, k)

    def get(self, k, default=None):
        return getattr(self, k, default)

    def __repr__(self):
        return ("==== <Frame> ====\n" + "\n".join(self.lines) +
                "\n\nCursor: %s %s\n=================\n"
                % (self.cursor.x, self.cursor.y))


def nth_line(frame, n):
    return frame.lines[n]


def botls(frame):
    return frame.lines[22:]


def wrapped_cursor(frame):
    return frame.cursor.x == 0 and frame.cursor.y > 0


def cursor_line(frame):
    return nth_line(frame, frame.cursor.y - 1 if wrapped_cursor(frame)
                    else frame.cursor.y)


def before_cursor(frame):
    if wrapped_cursor(frame):
        return cursor_line(frame)
    return cursor_line(frame)[:frame.cursor.x]


def before_cursor_p(frame, text):
    return before_cursor(frame).endswith(text)


def topline(frame):
    return nth_line(frame, 0).strip()


def extra_topline_cursor(frame):
    y = frame.cursor.y
    return (y == 1 or ((y == 2 or topline(frame).startswith("You read:"))
                       and before_cursor_p(frame, "--More--")))


def topline_cursor(frame):
    return frame.cursor.y == 0 or extra_topline_cursor(frame)


def topline_plus(frame):
    """Top line with possible overflow on following lines appended."""
    if extra_topline_cursor(frame):
        parts = [topline(frame)]
        if not wrapped_cursor(frame):
            parts.append(" ")
        for i in range(1, frame.cursor.y + 1):
            parts.append(nth_line(frame, i).strip())
        return "".join(parts)
    return topline(frame)


def looks_engulfed(frame):
    cursor, lines = frame.cursor, frame.lines
    if 0 < cursor.x < 79 and 1 < cursor.y < 21:
        rb, ra = cursor.x - 1, cursor.x + 1
        line_above = lines[cursor.y - 1]
        line_at = lines[cursor.y]
        line_below = lines[cursor.y + 1]
        return bool(
            (cursor.y == 1 or line_above[rb:ra + 1] == "/-\\")
            and re.search(r'\|.\|', line_at[rb:ra + 1])
            and (line_below[rb:ra + 1] == "\\-/" or cursor.y == 21))
    return False
