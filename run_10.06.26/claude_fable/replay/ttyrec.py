"""Minimal ttyrec parser + turn indexer.

ttyrec format = stream of frames:
  [sec(uint32 LE) | usec(uint32 LE) | length(uint32 LE) | payload(length bytes)]

We expose:
  parse(path)            → list[Frame]
  build_turn_index(...)  → dict[turn_number → first_frame_index_at_that_turn]
"""
from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from typing import Iterator

import pyte


TURN_RE = re.compile(rb"T:(\d+)")


@dataclass
class Frame:
    sec: int
    usec: int
    payload: bytes

    @property
    def t(self) -> float:
        return self.sec + self.usec / 1_000_000


def parse(path: str) -> list[Frame]:
    frames: list[Frame] = []
    with open(path, "rb") as f:
        while True:
            hdr = f.read(12)
            if len(hdr) < 12:
                break
            sec, usec, length = struct.unpack("<III", hdr)
            data = f.read(length)
            if len(data) < length:
                break
            frames.append(Frame(sec, usec, data))
    return frames


def build_turn_index(frames: list[Frame], cols: int = 80, rows: int = 24) -> dict:
    """Run frames through a pyte screen, capture turn # at each frame.

    Returns:
      {
        "frame_count": int,
        "turn_at_frame": list[int|None]  # turn shown after applying frame i
        "turn_first_frame": dict[str, int]  # turn → smallest frame index
        "duration_sec": float,
        "byte_offsets": list[int]  # cumulative bytes through frame i
      }
    """
    screen = pyte.Screen(cols, rows)
    stream = pyte.ByteStream(screen)

    turn_at_frame: list[int | None] = []
    byte_offsets: list[int] = []
    turn_first_frame: dict[int, int] = {}
    cumulative = 0
    current_turn: int | None = None

    for i, f in enumerate(frames):
        cumulative += 12 + len(f.payload)
        try:
            stream.feed(f.payload)
        except Exception:
            pass
        # Concatenated rendered rows — turn counter appears at bottom-of-screen
        rendered = "\n".join(screen.display).encode("latin-1", "ignore")
        m = TURN_RE.search(rendered)
        if m:
            t = int(m.group(1))
            current_turn = t
            if t not in turn_first_frame:
                turn_first_frame[t] = i
        turn_at_frame.append(current_turn)
        byte_offsets.append(cumulative)

    duration = 0.0
    if frames:
        duration = frames[-1].t - frames[0].t

    return {
        "frame_count": len(frames),
        "turn_at_frame": turn_at_frame,
        "turn_first_frame": {str(k): v for k, v in turn_first_frame.items()},
        "duration_sec": duration,
        "byte_offsets": byte_offsets,
        "first_ts": frames[0].t if frames else 0.0,
    }


def frame_bytes_concat(frames: list[Frame], start: int, end: int) -> bytes:
    """Return the concatenated payloads of frames[start:end]."""
    return b"".join(f.payload for f in frames[start:end])
