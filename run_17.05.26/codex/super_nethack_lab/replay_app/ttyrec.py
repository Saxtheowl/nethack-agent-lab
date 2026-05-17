from __future__ import annotations

import html
import lzma
import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator

import pyte


TTYREC_HEADER = struct.Struct("<III")
TURN_RE = re.compile(rb"T:(\d+)")


@dataclass(frozen=True)
class Frame:
    index: int
    sec: int
    usec: int
    payload: bytes

    @property
    def t(self) -> float:
        return self.sec + self.usec / 1_000_000

    @property
    def time(self) -> float:
        return self.t


@dataclass(frozen=True)
class RenderedFrame:
    index: int
    time: float
    text: str
    html: str


def open_ttyrec(path: Path) -> BinaryIO:
    if path.suffix == ".xz":
        return lzma.open(path, "rb")
    return path.open("rb")


def iter_chunks(path: Path) -> Iterator[Frame]:
    with open_ttyrec(path) as stream:
        index = 0
        while True:
            header = stream.read(TTYREC_HEADER.size)
            if not header:
                return
            if len(header) != TTYREC_HEADER.size:
                raise ValueError(f"truncated ttyrec header in {path}")
            sec, usec, length = TTYREC_HEADER.unpack(header)
            payload = stream.read(length)
            if len(payload) != length:
                raise ValueError(f"truncated ttyrec payload in {path}")
            yield Frame(index=index, sec=sec, usec=usec, payload=payload)
            index += 1


def parse(path: str | Path) -> list[Frame]:
    return list(iter_chunks(Path(path)))


def build_turn_index(frames: list[Frame], cols: int = 80, rows: int = 24) -> dict:
    turn_at_frame: list[int | None] = []
    turn_first_frame: dict[int, int] = {}
    byte_offsets: list[int] = []
    current_turn: int | None = None
    cumulative = 0

    for i, frame in enumerate(frames):
        cumulative += len(frame.payload)
        match = TURN_RE.search(frame.payload)
        if match:
            current_turn = int(match.group(1))
            turn_first_frame.setdefault(current_turn, i)
        turn_at_frame.append(current_turn)
        byte_offsets.append(cumulative)

    duration = frames[-1].t - frames[0].t if frames else 0.0
    return {
        "frame_count": len(frames),
        "turn_at_frame": turn_at_frame,
        "turn_first_frame": {str(k): v for k, v in turn_first_frame.items()},
        "duration_sec": duration,
        "byte_offsets": byte_offsets,
        "first_ts": frames[0].t if frames else 0.0,
    }


def frame_bytes_concat(frames: list[Frame], start: int, end: int) -> bytes:
    return b"".join(frame.payload for frame in frames[start:end])


def render_frames(path: Path, width: int = 80, height: int = 24, max_frames: int | None = None) -> list[RenderedFrame]:
    screen = pyte.Screen(width, height)
    stream = pyte.ByteStream(screen)
    rendered: list[RenderedFrame] = []
    first_time: float | None = None

    for chunk in iter_chunks(path):
        if first_time is None:
            first_time = chunk.t
        stream.feed(chunk.payload)
        text = "\n".join("".join(screen.display[y]) for y in range(height))
        rendered.append(
            RenderedFrame(
                index=chunk.index,
                time=chunk.t - first_time,
                text=text,
                html=html.escape(text),
            )
        )
        if max_frames is not None and len(rendered) >= max_frames:
            break

    return rendered
