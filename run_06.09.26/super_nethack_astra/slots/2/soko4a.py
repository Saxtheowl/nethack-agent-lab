#!/usr/bin/env python3
"""slot2 helper: execute the nethackwiki solution of Sokoban Level 4a move by move.
State in soko4a.state (json: labels map coords, idx, remaining dirs of current move).
Map col/row -> screen x+25, y+15.  usage: soko2b.py [max_moves]   (reset: --reset)
Stops on any STOPPED from scripts/sokoban.py (monster, HP...) and prints the screen."""
import json, os, re, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(here, '..', '..'))
SF = os.path.join(here, 'soko4a.state')
OX, OY = 27, 13
D = {'r': (1, 0), 'l': (-1, 0), 'u': (0, -1), 'd': (0, 1)}
LABELS = {'A': (3, 5), 'B': (5, 5), 'C': (7, 5), 'D': (9, 5), 'E': (11, 5), 'F': (4, 7),
          'G': (6, 7), 'H': (9, 7), 'I': (11, 7), 'J': (4, 8), 'K': (4, 10), 'L': (6, 10),
          'M': (8, 10), 'N': (7, 11), 'O': (3, 12), 'P': (5, 12), 'Q': (9, 12), 'R': (3, 14)}
MOVES = """K l | N rrr | R rrr | P rrdd dlll lur | F ll | J rddd drrd ddll lllu |
G ll | H ll | D lddd llld dddr | C rddd llld dd |
H ruuu luuu r* | G rrrr uuul uuur r* | F rrrr rruu uluu urrr* | I lllu uulu uurr rr* |
C uuuu rrru uulu uurr rrr* | K rruu urrr uuul uuur rrrr r* | L luuu rrru uulu uurr rrrr r* |
M lllu uurr ruuu luuu rrrr rrrr* | N llll luuu urrr uuul uuur rrrr rrrr* |
R ruuu ullu uurr ruuu luuu rrrr rrrr rr* | P rrru uuul luuu rrru uulu uurr rrrr rrrr r* |
J rrrr ruuu ullu uurr ruuu luuu rrrr rrrr rrrr* |
D rddd llll lurr rrru uuul luuu rrru uulu uurr rrrr rrrr rrr* |
B rrrd ddll lddd uuuu rrru uulu uurr rrrr rrrr rrrr* |
A rrrr rddd llld dduu uurr ruuu luuu rrrr rrrr rrrr rrr* |
E llld ddll lddd uuuu rrru uulu uurr rrrr rrrr rrrr rr*"""
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
    r = subprocess.run([os.environ.get('SOKO_PY', 'python3'), os.environ.get('SOKO_SCRIPT', 'scripts/sokoban.py'), str(sx), str(sy), rem, '--execute',
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
