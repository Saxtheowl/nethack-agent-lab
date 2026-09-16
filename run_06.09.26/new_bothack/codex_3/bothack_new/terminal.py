"""Incremental terminal decoding for NetHack's text UI."""
from dataclasses import dataclass

import pyte


@dataclass(frozen=True)
class Screen:
    rows: tuple[str, ...]
    cursor: tuple[int, int]
    revision: int

    def text(self) -> str:
        return "\n".join(self.rows)


class Terminal:
    def __init__(self, columns: int = 80, rows: int = 24):
        self.columns, self.rows = columns, rows
        self._screen = pyte.Screen(columns, rows)
        self._stream = pyte.ByteStream(self._screen)
        self.revision = 0

    def feed(self, data: bytes) -> None:
        if data:
            self._stream.feed(data)
            self.revision += 1

    def snapshot(self) -> Screen:
        # Copy the display so later output cannot mutate an existing snapshot.
        rows = tuple(str(row) for row in self._screen.display)
        cursor = self._screen.cursor
        return Screen(rows, (cursor.x, cursor.y), self.revision)
