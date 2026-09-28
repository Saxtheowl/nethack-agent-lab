#!/usr/bin/env python3
"""Record a truly important moment of the current game (rare item, unexpected
monster, near death, big decision...) with an explanation. Saved in
runs/games/<game_id>/chronicle.jsonl and shown on the dashboard (expandable).

  python3 scripts/chronicle.py [--importance 1-3] [--kind item|monster|danger|progress|decision|death] "Titre" "Explication"

Importance: 3 = exceptionnel, 2 = important, 1 = notable. Uses NH_SLOT."""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import frames
import session

p = argparse.ArgumentParser()
p.add_argument('--importance', type=int, default=2, choices=(1, 2, 3))
p.add_argument('--kind', default='event')
p.add_argument('--game', help='game id (default: the slot\'s current game)')
p.add_argument('--turn', type=int)
p.add_argument('--dlvl')
p.add_argument('--at', type=float, help='epoch seconds (default: now)')
p.add_argument('title')
p.add_argument('text', nargs='?', default='')
a = p.parse_args()
gid = a.game or json.loads(session.SLOTFILE.read_text())['game_id']
status = None if a.game else frames.parse_status(frames.segment_rows(
    __import__('terminal').text_runs(session.screen(ansi=True))))
entry = {'t': a.at or round(time.time(), 3), 'turn': a.turn or (status[0] if status else None),
         'dlvl': a.dlvl or (status[1] if status else None), 'importance': a.importance,
         'kind': a.kind, 'title': a.title, 'text': a.text}
path = frames.GAMES / gid / 'chronicle.jsonl'
path.parent.mkdir(parents=True, exist_ok=True)
with open(path, 'a') as f:
    f.write(json.dumps(entry, ensure_ascii=False) + '\n')
print('chronicle +', gid, entry['turn'], a.title)
