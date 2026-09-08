"""80×24 ANSI terminal adapter and strict ttyrec I/O.

NetHack/JTA streams are Latin-1. Reverse video uses the background color in
BotHack's frame representation. pyte is only terminal emulation, not policy.
"""
from dataclasses import dataclass
import struct
import time
import pyte
from .frame import COLORMAP, Frame
from .position import Position

ANSI = {"default": 0, "black": 0, "red": 1, "green": 2, "brown": 3,
        "blue": 4, "magenta": 5, "cyan": 6, "white": 7}


class Terminal:
    def __init__(self):
        self.screen = pyte.Screen(80, 24)
        self.stream = pyte.Stream(self.screen)

    def feed(self, raw):
        self.stream.feed(raw.decode("latin1") if isinstance(raw, bytes) else raw)
        return self.snapshot()

    def snapshot(self):
        rows = []
        for y in range(24):
            row = []
            for x in range(80):
                cell = self.screen.buffer[y][x]
                color = cell.bg if cell.reverse else cell.fg
                if color not in ANSI:
                    raise ValueError(f"Color {color!r} outside BotHack's 16-color protocol")
                row.append(COLORMAP[ANSI[color] + 8 * bool(cell.bold) + 16 * bool(cell.reverse)])
            rows.append(tuple(row))
        return Frame(tuple(self.screen.display), tuple(rows),
                     Position(min(79, self.screen.cursor.x), self.screen.cursor.y))


@dataclass(frozen=True)
class TtyRecord:
    seconds: int
    microseconds: int
    payload: bytes


def read_ttyrec(stream, *, max_record_bytes=16 * 1024 * 1024):
    while header := stream.read(12):
        if len(header) != 12:
            raise ValueError("Truncated ttyrec header")
        sec, usec, size = struct.unpack("<III", header)
        if usec >= 1_000_000 or size > max_record_bytes:
            raise ValueError("Invalid ttyrec header")
        payload = stream.read(size)
        if len(payload) != size:
            raise ValueError("Truncated ttyrec payload")
        yield TtyRecord(sec, usec, payload)


def write_ttyrec(stream, payload, timestamp=None):
    timestamp = time.time() if timestamp is None else timestamp
    seconds = int(timestamp)
    microseconds = int((timestamp - seconds) * 1_000_000)
    stream.write(struct.pack("<III", seconds, microseconds, len(payload)))
    stream.write(payload)
