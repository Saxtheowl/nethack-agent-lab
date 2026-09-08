"""Translation of bothack/frame.clj, GPL-2.0, 2026-09-06."""
from dataclasses import dataclass
import re
from .position import Position

COLORMAP = (None, "red", "green", "brown", "blue", "magenta", "cyan", "gray",
            "bold", "orange", "bright-green", "yellow", "bright-blue", "bright-magenta", "bright-cyan", "white",
            "inverse", "inverse-red", "inverse-green", "inverse-brown", "inverse-blue", "inverse-magenta", "inverse-cyan", "inverse-gray",
            "inverse-bold", "inverse-orange", "inverse-bright-green", "inverse-yellow", "inverse-bright-blue", "inverse-bright-magenta", "inverse-bright-cyan", "inverse-white")


def inverse(color):
    return color in COLORMAP[16:]


def non_inverse(color):
    if color == "inverse-bold":
        return "white"  # Deliberately preserve the upstream special case.
    return COLORMAP[COLORMAP.index(color) - 16] if inverse(color) else color


@dataclass(frozen=True)
class Frame:
    lines: tuple[str, ...]
    colors: tuple[tuple[str | None, ...], ...]
    cursor: Position

    def __post_init__(self):
        if len(self.lines) != 24 or any(len(line) != 80 for line in self.lines):
            raise ValueError("BotHack requires an 80×24 terminal")
        if len(self.colors) != 24 or any(len(row) != 80 for row in self.colors):
            raise ValueError("Invalid color grid")

    @classmethod
    def text(cls, lines, cursor):
        return cls(tuple(s.ljust(80) for s in lines), tuple((None,) * 80 for _ in range(24)), cursor)

    @property
    def botls(self):
        return self.lines[22:]

    @property
    def wrapped_cursor(self):
        return self.cursor.x == 0 and self.cursor.y > 0

    @property
    def cursor_line(self):
        return self.lines[self.cursor.y - int(self.wrapped_cursor)]

    @property
    def before_cursor(self):
        return self.cursor_line if self.wrapped_cursor else self.cursor_line[:self.cursor.x]

    @property
    def topline(self):
        return self.lines[0].strip()

    @property
    def extra_topline_cursor(self):
        return self.cursor.y == 1 or ((self.cursor.y == 2 or self.topline.startswith("You read:")) and self.before_cursor.endswith("--More--"))

    @property
    def topline_cursor(self):
        return self.cursor.y == 0 or self.extra_topline_cursor

    @property
    def topline_plus(self):
        if self.extra_topline_cursor:
            return self.topline + ("" if self.wrapped_cursor else " ") + "".join(s.strip() for s in self.lines[1:self.cursor.y + 1])
        return self.topline

    @property
    def looks_engulfed(self):
        x, y = self.cursor.x, self.cursor.y
        return (0 < x < 79 and 1 < y < 21 and self.lines[y - 1][x - 1:x + 2] == "/-\\"
                and bool(re.search(r"\|.\|", self.lines[y][x - 1:x + 2]))
                and self.lines[y + 1][x - 1:x + 2] == "\\-/")
