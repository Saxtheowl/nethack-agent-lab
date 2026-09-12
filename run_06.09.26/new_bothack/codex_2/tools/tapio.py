#!/usr/bin/env python3
"""Strict reader for tools/pty_tap.py recordings.

The old readers stopped silently at the first malformed record, so a truncated
capture looked like a short but valid one - and a comparison over it could be
reported as a success.  This one refuses anything it cannot account for.

Record format (little endian): <dir:1><len:4><payload>, dir being b'O'
(game -> bot) or b'I' (bot -> game).
"""
import struct

#: markers that prove the recorded game actually reached its end
END_MARKERS = (
    b"You die...",
    b"Do you want your possessions identified?",
    b"Do you want to see your attributes?",
    b"You quit",
    b"Goodbye ",
)


class TapError(Exception):
    """The recording is not a well-formed tap log."""


def read_records(path):
    """Parse a tap log; raise TapError on anything malformed."""
    data = open(path, 'rb').read()
    out, i, n = [], 0, len(data)
    while i < n:
        if i + 5 > n:
            raise TapError("%s: %d trailing byte(s) at offset %d, not a "
                           "complete header" % (path, n - i, i))
        d = data[i:i + 1]
        if d not in (b'O', b'I'):
            raise TapError("%s: invalid record type %r at offset %d"
                           % (path, d, i))
        length = struct.unpack('<I', data[i + 1:i + 5])[0]
        end = i + 5 + length
        if end > n:
            raise TapError("%s: record at offset %d claims %d bytes, only %d "
                           "available (truncated capture)"
                           % (path, i, length, n - i - 5))
        out.append((d.decode(), data[i + 5:end]))
        i = end
    if not out:
        raise TapError("%s: empty capture" % path)
    return out


def keystrokes(records):
    """Everything the bot sent, in order."""
    return b"".join(c for d, c in records if d == 'I')


def output(records):
    """Everything the game sent, in order."""
    return b"".join(c for d, c in records if d == 'O')


def attested_end(records):
    """Did the recorded game actually finish?

    A capture that was cut off by a wall-clock limit can only ever prove
    "identical over what was captured", never "identical game", so the
    distinction has to be carried into the verdict.
    """
    return end_marker(records) is not None


def end_marker(records):
    """Which end marker the capture carries, or None - the same test as
    `attested_end`, but naming the evidence so a report can quote it."""
    o = output(records)
    for m in END_MARKERS:
        if m in o:
            return m
    return None


def summarise(path):
    recs = read_records(path)
    return {'records': len(recs),
            'keystroke_bytes': len(keystrokes(recs)),
            'output_bytes': len(output(recs)),
            'attested_end': attested_end(recs)}
