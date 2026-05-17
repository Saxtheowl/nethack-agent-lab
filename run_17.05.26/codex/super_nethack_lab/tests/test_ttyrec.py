from __future__ import annotations

import struct
from pathlib import Path

from replay_app.ttyrec import iter_chunks, render_frames


def write_ttyrec(path: Path, chunks: list[bytes]) -> None:
    with path.open("wb") as stream:
        for i, payload in enumerate(chunks):
            stream.write(struct.pack("<III", 100 + i, 0, len(payload)))
            stream.write(payload)


def test_iter_chunks_reads_headers_and_payloads(tmp_path: Path) -> None:
    path = tmp_path / "sample.ttyrec"
    write_ttyrec(path, [b"abc", b"defg"])

    chunks = list(iter_chunks(path))

    assert [chunk.index for chunk in chunks] == [0, 1]
    assert [chunk.payload for chunk in chunks] == [b"abc", b"defg"]
    assert [chunk.time for chunk in chunks] == [100, 101]


def test_render_frames_applies_terminal_escape_sequences(tmp_path: Path) -> None:
    path = tmp_path / "sample.ttyrec"
    write_ttyrec(path, [b"hello", b"\r\nworld", b"\x1b[Htop"])

    frames = render_frames(path, width=12, height=3)

    assert frames[0].text.splitlines()[0].startswith("hello")
    assert frames[1].text.splitlines()[1].startswith("world")
    assert frames[2].text.splitlines()[0].startswith("toplo")
    assert "&" not in frames[2].html
