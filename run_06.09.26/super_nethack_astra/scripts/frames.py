"""Replayable frame store shared by the live recorder, the ttyrec importer and
the dashboard server.

A game lives in runs/games/<game_id>/:
  meta.json     summary (slot, player, status, last status line, outcome...)
  frames.jsonl  one JSON object per screen change:
                {"i": index, "t": epoch seconds, "k": 1 on keyframes,
                 "r": {"row": [[text, fg, bg, flags], ...], ...},   changed rows only
                 "s": [turn, dlvl, hp, hpmax, xl, ac] or null}
Keyframes carry every row, so a client can start anywhere near a keyframe and
the file can be read while it is still being appended (live replay).
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAMES = ROOT / 'runs' / 'games'
COLS, ROWS = 144, 36
KEYFRAME_EVERY = 200
STATUS_ROW = 34

STATUS = re.compile(r'(?:Dlvl:(\d+)|(Home \d+|Earth|Air|Fire|Water|Astral|End Game))\b.*?HP:(\d+)\((\d+)\).*?AC:(-?\d+)'
                    r'.*?(?:Xp|Exp|HD):(\d+)(?:/\d+)?.*?T:(\d+)')


def segment_rows(runs):
    """tmux/text runs (spanning newlines) -> list of rows of [text, fg, bg, flags]."""
    rows = [[]]
    for run in runs:
        style = (run.get('fg'), run.get('bg'),
                 ''.join(f for f, k in (('b', 'bold'), ('d', 'dim'), ('u', 'underline'), ('i', 'italic')) if run.get(k)))
        parts = run['text'].split('\n')
        for n, part in enumerate(parts):
            if n:
                rows.append([])
            if part:
                row = rows[-1]
                if row and tuple(row[-1][1:]) == style:
                    row[-1][0] += part
                else:
                    row.append([part, *style])
    while len(rows) < ROWS:
        rows.append([])
    return rows[:ROWS]


def row_text(row):
    return ''.join(seg[0] for seg in row)


def parse_status(rows):
    text = row_text(rows[STATUS_ROW]) if len(rows) > STATUS_ROW else ''
    m = STATUS.search(text)
    if not m:
        return None
    dlvl = m[1] if m[1] else m[2]
    return [int(m[7]), dlvl, int(m[3]), int(m[4]), int(m[6]), int(m[5])]


class Writer:
    """Append-only frame writer that emits deltas against the previous screen."""

    def __init__(self, game_id):
        self.dir = GAMES / game_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / 'frames.jsonl'
        self.index = 0
        self.prev = None
        self.last_status = None
        if self.path.exists():
            with open(self.path) as f:
                for self.index, _ in enumerate(f, 1):
                    pass

    def add(self, rows, when):
        if rows == self.prev:
            return False
        key = self.prev is None or self.index % KEYFRAME_EVERY == 0
        changed = {str(y): row for y, row in enumerate(rows)
                   if key or self.prev[y] != row}
        status = parse_status(rows)
        if status:
            self.last_status = status
        frame = {'i': self.index, 't': round(when, 3), 'r': changed, 's': status}
        if key:
            frame['k'] = 1
        with open(self.path, 'a') as f:
            f.write(json.dumps(frame, ensure_ascii=False, separators=(',', ':')) + '\n')
        self.prev = rows
        self.index += 1
        return True


def load_meta(game_id):
    try:
        return json.loads((GAMES / game_id / 'meta.json').read_text())
    except FileNotFoundError:
        return {'id': game_id}


def save_meta(game_id, meta):
    path = GAMES / game_id / 'meta.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    tmp.replace(path)


XLOG = ROOT / 'engine/install/games/lib/nethackdir/xlogfile'


def xlog_entries():
    out = []
    try:
        for line in XLOG.read_text().splitlines():
            out.append(dict(field.split('=', 1) for field in line.split('\t') if '=' in field))
    except FileNotFoundError:
        pass
    return out
