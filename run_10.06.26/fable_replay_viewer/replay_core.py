"""Décodage ttyrec3 et rendu des frames terminal pour le viewer Fable.

Le format ttyrec3 du NLE est une suite d'enregistrements binaires :
entête de 13 octets ``<iiiB`` (secondes, microsecondes, longueur, canal)
suivi de ``longueur`` octets de données. Canal 0 : sortie terminal,
canal 1 : touche envoyée par l'agent, canal 2 : score interne (ignoré).

Chaque frame de sortie est rejouée dans un écran pyte 80x24 puis
sérialisée en segments colorés. Les lignes identiques sont mutualisées
dans un pool afin que le client puisse se déplacer en O(1) dans le replay.
"""

from __future__ import annotations

import bz2
import gzip
import struct
from pathlib import Path

import pyte

COLS = 80
ROWS = 24

FLAG_BOLD = 1
FLAG_REVERSE = 2
FLAG_UNDERLINE = 4

_HEADER = struct.Struct("<iiiB")


def _open_ttyrec(path: Path):
    suffix = path.suffixes[-1] if path.suffixes else ""
    if suffix in {".bz2", ".bzip2"}:
        return bz2.BZ2File(path)
    if suffix in {".gz", ".gzip"}:
        return gzip.GzipFile(path)
    return path.open("rb")


def iter_records(path: Path):
    """Itère sur (timestamp, canal, données) d'un ttyrec, compressé ou non."""
    with _open_ttyrec(path) as stream:
        while True:
            header = stream.read(_HEADER.size)
            if not header:
                return
            if len(header) != _HEADER.size:
                raise OSError(f"entête ttyrec incomplet dans {path}")
            sec, usec, length, channel = _HEADER.unpack(header)
            if sec < 0 or usec < 0 or length < 0 or channel not in (0, 1, 2):
                raise OSError(f"entête ttyrec illégal {(sec, usec, length, channel)}")
            data = stream.read(length)
            if len(data) != length:
                raise OSError(f"frame ttyrec incomplète dans {path}")
            yield sec + usec * 1e-6, channel, data


def describe_key(data: bytes) -> str:
    """Rend une touche agent lisible (ESC, ^X, ␣, caractère brut...)."""
    parts = []
    for byte in data:
        if byte == 0x1B:
            parts.append("ESC")
        elif byte in (0x0A, 0x0D):
            parts.append("⏎")
        elif byte == 0x20:
            parts.append("␣")
        elif byte == 0x7F:
            parts.append("DEL")
        elif byte < 0x20:
            parts.append("^" + chr(byte + 64))
        elif byte < 0x7F:
            parts.append(chr(byte))
        else:
            parts.append(f"\\x{byte:02x}")
    return "".join(parts)


def _encode_row(row, cols: int):
    """Sérialise une ligne pyte en segments [texte, fg, bg, flags] fusionnés."""
    segments: list[list] = []
    last_style = None
    for x in range(cols):
        char = row[x]
        flags = (
            (FLAG_BOLD if char.bold else 0)
            | (FLAG_REVERSE if char.reverse else 0)
            | (FLAG_UNDERLINE if getattr(char, "underscore", False) else 0)
        )
        style = (char.fg, char.bg, flags)
        text = char.data or " "
        if style == last_style:
            segments[-1][0] += text
        else:
            segments.append([text, char.fg, char.bg, flags])
            last_style = style
    while segments:
        text, fg, bg, flags = segments[-1]
        if flags == 0 and fg == "default" and bg == "default" and not text.strip():
            segments.pop()
        else:
            break
    key = tuple((text, fg, bg, flags) for text, fg, bg, flags in segments)
    return key, segments


def render_episode(path: Path, cols: int = COLS, rows: int = ROWS) -> dict:
    """Rend toutes les frames d'un ttyrec en grilles indexées sur un pool de lignes.

    Retourne un dict prêt à sérialiser en JSON :
    ``t`` timestamps relatifs, ``grid`` liste de grilles (ids de lignes),
    ``cursor`` positions [x, y], ``pool`` lignes uniques,
    ``inputs`` touches agent ``[index_frame, touche]``.
    """
    screen = pyte.Screen(cols, rows)
    stream = pyte.ByteStream(screen)

    pool_ids: dict[tuple, int] = {}
    pool_rows: list[list] = []
    times: list[float] = []
    grids: list[list[int]] = []
    cursors: list[list[int]] = []
    inputs: list[list] = []
    prev_grid: list[int] | None = None
    t0: float | None = None

    for timestamp, channel, data in iter_records(Path(path)):
        if t0 is None:
            t0 = timestamp
        if channel == 1:
            # La touche précède la frame qu'elle provoque : index = frame suivante.
            inputs.append([len(times), describe_key(data)])
            continue
        if channel != 0:
            continue
        stream.feed(data)
        if prev_grid is None:
            dirty = range(rows)
            grid = [0] * rows
        else:
            dirty = screen.dirty
            grid = list(prev_grid)
        for y in dirty:
            if y >= rows:
                continue
            row_key, row_segments = _encode_row(screen.buffer[y], cols)
            row_id = pool_ids.get(row_key)
            if row_id is None:
                row_id = len(pool_rows)
                pool_ids[row_key] = row_id
                pool_rows.append(row_segments)
            grid[y] = row_id
        screen.dirty.clear()
        times.append(round(timestamp - t0, 3))
        grids.append(grid)
        cursors.append([screen.cursor.x, screen.cursor.y])
        prev_grid = grid

    return {
        "cols": cols,
        "rows": rows,
        "t": times,
        "grid": grids,
        "cursor": cursors,
        "pool": pool_rows,
        "inputs": inputs,
    }
