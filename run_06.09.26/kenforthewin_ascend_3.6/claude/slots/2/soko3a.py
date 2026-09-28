#!/usr/bin/env python3
"""slot2 helper: execute the nethackwiki solution of Sokoban Level 3a move by move.
State in soko3a.state (json: labels map coords, idx, remaining dirs of current move).
Map col/row -> screen x+25, y+15.  usage: soko2b.py [max_moves]   (reset: --reset)
Stops on any STOPPED from scripts/sokoban.py (monster, HP...) and prints the screen."""
import json, os, re, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(here, '..', '..'))
SF = os.path.join(here, 'soko3a.state')
OX, OY = 31, 15
D = {'r': (1, 0), 'l': (-1, 0), 'u': (0, -1), 'd': (0, 1)}
LABELS = {'A': (4, 2), 'B': (4, 3), 'C': (5, 3), 'D': (7, 3), 'E': (8, 3), 'F': (2, 4),
          'G': (3, 4), 'H': (5, 5), 'I': (6, 6), 'J': (9, 6), 'K': (3, 7), 'L': (4, 7),
          'M': (7, 7), 'N': (6, 9), 'O': (5, 10), 'P': (5, 11)}
MOVES = """O ll | P rr* | N ddrr* | L ddd | O u | L rrdr rr* | O rddr rrrr r* | K rddd drrr rrrr* |
G dddr dddd rrrr rrrr* | F rddd rddd drrr rrrr rr* | M rrll llld dddr rrrr rrrr r* | J uu |
I dddd drrr rrrr rr* | H rddd dddr rrrr rrrr r* | A rr | C ddrd dddd drrr rrrr rrrr*"""
moves = []
for part in MOVES.split('|'):
    part = part.strip()
    if part:
        lab, rest = part.split(None, 1)
        moves.append((lab, rest.replace(' ', '').replace('*', '')))


def load():
    if '--reset' in sys.argv or not os.path.exists(SF):
        st = {'labels': {k: list(v) for k, v in LABELS.items()}, 'idx': 0, 'rem': moves[0][1]}
        json.dump(st, open(SF, 'w'))
    return json.load(open(SF))


def boulders():
    out = subprocess.run(['python3', 'scripts/session.py', 'screen'], cwd=root,
                         capture_output=True, text=True).stdout
    b = set()
    for y, line in enumerate(out.splitlines()):
        if 10 <= y <= 30:
            for x, c in enumerate(line[:81]):
                if c == '0' and 1 <= x <= 79:
                    b.add((x, y))
    return b


st = load()
HH = [z for a in sys.argv[1:] if a.startswith('hh=') for z in ('--hidden-hole', a[3:])]
maxm = int([a for a in sys.argv[1:] if a.isdigit()][0]) if any(a.isdigit() for a in sys.argv[1:]) else 1
done_moves = 0
env = dict(os.environ, NH_SLOT='2')
while st['idx'] < len(moves) and done_moves < maxm:
    lab = moves[st['idx']][0]
    x, y = st['labels'][lab]
    rem = st['rem']
    before = boulders()
    sx, sy = x + OX, y + OY
    if (sx, sy) not in before:
        print('HALT: boulder', lab, 'not at', (sx, sy)); sys.exit(1)
    print('MOVE', st['idx'], lab, (x, y), rem, flush=True)
    r = subprocess.run(['python3', 'scripts/sokoban.py', str(sx), str(sy), rem, '--execute',
                        '--max-steps', '50'] + HH, cwd=root, env=env, capture_output=True, text=True)
    out = r.stdout + r.stderr
    after = boulders()
    gone, new = before - after, after - before
    # track the labelled boulder
    if (sx, sy) in after:
        pushed = 0
    elif len(new) == 1:
        nx, ny = next(iter(new))
        cx, cy, pushed = sx, sy, 0
        for c in rem:
            if (cx, cy) == (nx, ny):
                break
            cx += D[c][0]; cy += D[c][1]; pushed += 1
        if (cx, cy) != (nx, ny):
            print('HALT: cannot match new boulder pos', (nx, ny)); print(out[-2500:]); sys.exit(1)
        st['labels'][lab] = [nx - OX, ny - OY]
    elif len(new) == 0 and len(gone) == 1:
        pushed = len(rem)  # fell into hole
        st['labels'][lab] = None
    else:
        print('HALT: ambiguous board change', gone, new); print(out[-2500:]); sys.exit(1)
    st['rem'] = rem[pushed:]
    if not st['rem']:
        st['idx'] += 1; done_moves += 1
        st['rem'] = moves[st['idx']][1] if st['idx'] < len(moves) else ''
    json.dump(st, open(SF, 'w'))
    tail = [l for l in out.splitlines() if 'STOPPED' in l or 'Checked' in l or 'Error' in l or 'Traceback' in l]
    print('  pushed', pushed, '->', tail[-1][:150] if tail else out[-300:])
    if r.returncode != 0 or any('STOPPED' in l or 'Traceback' in l for l in tail):
        print('HALT'); print(out[-2500:]); sys.exit(1)
print('STATE idx', st['idx'], '/', len(moves), 'rem', st['rem'])
