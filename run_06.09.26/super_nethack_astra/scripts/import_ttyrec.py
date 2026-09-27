#!/usr/bin/env python3
"""Convert a ttyrec into the dashboard frame store (runs/games/<game_id>/).

  python3 scripts/import_ttyrec.py runs/<file>.ttyrec <game_id> [meta key=value ...]

Uses pyte as the terminal emulator (144x36, the harness geometry). Records
closer than 40 ms are merged into one frame."""
import struct
import sys

import pyte

import frames

NAMES = {'black': 0, 'red': 1, 'green': 2, 'brown': 3, 'yellow': 3, 'blue': 4,
         'magenta': 5, 'cyan': 6, 'white': 7}
PALETTE = ('#000000', '#cd0000', '#00cd00', '#cdcd00', '#0000ee', '#cd00cd',
           '#00cdcd', '#e5e5e5', '#7f7f7f', '#ff0000', '#00ff00', '#ffff00',
           '#5c5cff', '#ff00ff', '#00ffff', '#ffffff')


def color(name, bold=False):
    if name in (None, 'default'):
        return None
    bright = name.startswith('bright')
    base = name[6:] if bright else name
    if base in NAMES:
        return PALETTE[NAMES[base] + (8 if bright or bold else 0)]
    if len(name) == 6:
        return '#' + name.lower()
    return None


def screen_rows(screen):
    rows = []
    for y in range(frames.ROWS):
        line = screen.buffer[y]
        row = []
        for x in range(frames.COLS):
            ch = line[x]
            fg, bg = color(ch.fg, ch.bold), color(ch.bg)
            if ch.reverse:
                fg, bg = bg or '#0a1012', fg or '#e5e5e5'
            style = (fg, bg, 'b' if ch.bold else '')
            text = ch.data or ' '
            if row and tuple(row[-1][1:]) == style:
                row[-1][0] += text
            else:
                row.append([text, *style])
        # trim trailing default-styled spaces like tmux capture does
        while row and row[-1][1:] == [None, None, ''] and not row[-1][0].strip():
            row.pop()
        if row and row[-1][1:] == [None, None, '']:
            row[-1][0] = row[-1][0].rstrip()
        rows.append(row)
    return rows


def main():
    path, gid = sys.argv[1], sys.argv[2]
    screen = pyte.Screen(frames.COLS, frames.ROWS)
    stream = pyte.ByteStream(screen)
    stream.use_utf8 = False  # NetHack draws borders with SO + DEC graphics (G1)
    writer = frames.Writer(gid)
    pending = None
    with open(path, 'rb') as f:
        while True:
            head = f.read(12)
            if len(head) < 12:
                break
            sec, usec, length = struct.unpack('<III', head)
            data = f.read(length)
            when = sec + usec / 1e6
            if pending is not None and when - pending > 0.04:
                writer.add(screen_rows(screen), pending)
            stream.feed(data)
            pending = when
    if pending is not None:
        writer.add(screen_rows(screen), pending)
    meta = frames.load_meta(gid)
    meta.update(id=gid, frames=writer.index)
    if writer.last_status:
        t, dlvl, hp, hpmax, xl, ac = writer.last_status
        meta.update(turn=t, dlvl=dlvl, hp=hp, hpmax=hpmax, xl=xl, ac=ac)
    for kv in sys.argv[3:]:
        k, v = kv.split('=', 1)
        meta[k] = int(v) if v.lstrip('-').isdigit() else v
    frames.save_meta(gid, meta)
    print(gid, writer.index, 'frames', meta.get('turn'))


if __name__ == '__main__':
    main()
