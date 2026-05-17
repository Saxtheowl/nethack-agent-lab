#!/opt/venv/bin/python3
"""Detect whether a finished BotHack game ended in ascension.

We look at the last screen state of the ttyrec — if NetHack ended with
'You ascended to the status of Demigoddess/Demigod' (or 'You ascended.'),
that's a win. We also extract final score/turn from the end-of-game disclose.

Used by loop.py after each run_one.sh invocation.
"""
from __future__ import annotations

import json
import os
import struct
import sys
from typing import Iterable

try:
    import pyte  # type: ignore
except ImportError:
    pyte = None  # we'll fall back to a simpler byte search


# Exact strings that NetHack 3.4.3 writes on a successful ascension.
# See src/end.c (~lines 1083-1138) and src/topten.c (~lines 821-822).
# "went to your reward" is in a ternary that's only reached for ASCENDED
# (ESCAPED prints "escaped from the dungeon" instead), so it's unambiguous.
ASCENSION_MARKERS = (
    b"went to your reward",
    b"the Demigoddess",
    b"ascended to demigod",
)
# More cautious marker: only male Demigod has "the Demigod..." (with the
# closing ellipsis) which keeps us from matching "Demigod" in other contexts.
ASCENSION_MARKERS_STRICT = ASCENSION_MARKERS + (b"the Demigod...",)


def iter_frames(path: str) -> Iterable[tuple[float, bytes]]:
    """Yield (timestamp, payload) tuples from a ttyrec file."""
    with open(path, "rb") as f:
        while True:
            hdr = f.read(12)
            if len(hdr) < 12:
                return
            sec, usec, length = struct.unpack("<III", hdr)
            data = f.read(length)
            if len(data) < length:
                return
            yield (sec + usec / 1_000_000), data


def detect(path: str) -> dict:
    """Scan ttyrec, return dict with ascension flag + extracted stats."""
    if not os.path.exists(path):
        return {"ascended": False, "reason": "no_ttyrec"}

    total_bytes = 0
    all_payloads: list[bytes] = []
    marker_hits: set[str] = set()
    tail = bytearray()

    for _, data in iter_frames(path):
        total_bytes += len(data)
        all_payloads.append(data)
        tail.extend(data)
        if len(tail) > 65536:
            del tail[:-65536]

    for m in ASCENSION_MARKERS:
        if bytes(m) in tail:
            marker_hits.add(m.decode("ascii", "replace"))

    ascended = bool(marker_hits)

    import re
    final_turn = None
    final_screen_text = None

    # Try pyte first — it tracks cursor state and gives a clean final screen.
    # Falls back to a raw-byte scan because NetHack clears the screen on quit,
    # which would otherwise hide the "T:NNN" we want.
    if pyte is not None and all_payloads:
        screen = pyte.Screen(80, 24)
        stream = pyte.ByteStream(screen)
        for chunk in all_payloads:
            try:
                stream.feed(chunk)
            except Exception:
                pass
        final_screen_text = "\n".join(screen.display)
        m = re.search(r"T:(\d+)", final_screen_text)
        if m:
            final_turn = int(m.group(1))

    # Fallback: last `T:\d+` substring anywhere in the recording's tail.
    if final_turn is None:
        all_text = bytes(tail).decode("latin-1", "replace")
        matches = re.findall(r"T:(\d+)", all_text)
        if matches:
            final_turn = int(matches[-1])

    return {
        "ascended": ascended,
        "ascension_markers": sorted(marker_hits),
        "ttyrec_bytes": total_bytes,
        "final_turn": final_turn,
        "final_screen_tail": (final_screen_text or "").splitlines()[-12:],
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: detect_ascension.py <game_dir-or-ttyrec>", file=sys.stderr)
        return 2
    arg = sys.argv[1]
    if os.path.isdir(arg):
        ttyrec = os.path.join(arg, "game.ttyrec")
        meta_path = os.path.join(arg, "meta.json")
    else:
        ttyrec = arg
        meta_path = None

    result = detect(ttyrec)
    if meta_path and os.path.exists(meta_path):
        with open(meta_path) as f:
            meta = json.load(f)
        meta.update(result)
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
