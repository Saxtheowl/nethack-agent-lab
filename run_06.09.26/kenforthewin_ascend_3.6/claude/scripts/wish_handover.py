#!/usr/bin/env python3
"""Point a local slot at the wish game found on miniforum-worker.

  python3 scripts/wish_handover.py <slot> <wishK>

The game (and its save file) stays on the worker; the slot's tmux session
attaches to it over ssh (see session.py REMOTE). Writes .runtime/slot-N.json
with style wish_abuser and the next run number, then starts the slot.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST, SOCK = 'miniforum-worker', '/tmp/wishscum.sock'


def main():
    slot, sess = sys.argv[1], sys.argv[2]
    k = sess.removeprefix('wish')
    player = f'Wish{k}'
    alive = subprocess.run(['ssh', '-o', 'BatchMode=yes', HOST, f'tmux -S {SOCK} has-session -t {sess}'])
    if alive.returncode != 0:
        sys.exit(f'no tmux session {sess} on {HOST}')
    slotfile = ROOT / '.runtime' / f'slot-{slot}.json'
    old = json.loads(slotfile.read_text()) if slotfile.exists() else {}
    run = int(old.get('run') or 0) + 1
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%d.%H:%M:%S')
    journal = f'memory/run-{run}.md' if slot == '1' else f'memory/slot{slot}-run-{run}.md'
    info = {'game_id': f'{player}-{stamp}', 'player': player, 'slot': slot, 'started': stamp,
            'journal': journal, 'run': run, 'style': 'wish_abuser',
            'remote': {'host': HOST, 'sock': SOCK, 'session': sess, 'player': player}}
    slotfile.write_text(json.dumps(info))
    subprocess.run([sys.executable, str(ROOT / 'scripts/session.py'), 'start'],
                   env={**os.environ, 'NH_SLOT': slot}, check=True)
    print(f'slot {slot} -> {HOST}:{sess} ({player}), journal {journal}')


if __name__ == '__main__':
    main()
