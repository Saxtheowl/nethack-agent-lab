#!/usr/bin/env python3
"""slot2 helper: run a soko4-1 push plan (map coords 'x,y dir', offset +33,+15 on screen)
through scripts/sokoban.py --execute, one boulder-group at a time.
usage: soko41.py [start_group_index] [max_groups]"""
import os, sys, subprocess, re
here = os.path.dirname(os.path.abspath(__file__))
root = os.path.abspath(os.path.join(here, '..', '..'))
OX, OY = 33, 15
D = {'r': (1, 0), 'l': (-1, 0), 'u': (0, -1), 'd': (0, 1)}
entries = []
for line in open(os.path.join(here, 'soko41.plan')):
    line = line.split(':', 1)[1] if ':' in line else ''
    for tok in line.split():
        m = re.match(r'(\d+),(\d+)([rlud])', tok)
        if m: entries.append((int(m[1]), int(m[2]), m[3]))
groups = []
for x, y, d in entries:
    if groups:
        gx, gy, ds = groups[-1]
        cx, cy = gx, gy
        for c in ds: cx += D[c][0]; cy += D[c][1]
        if (cx, cy) == (x, y):
            groups[-1] = (gx, gy, ds + d); continue
    groups.append((x, y, d))
start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
count = int(sys.argv[2]) if len(sys.argv) > 2 else 1
if start == -1:
    for i, g in enumerate(groups): print(i, g)
    sys.exit()
env = dict(os.environ, NH_SLOT='2')
for i in range(start, min(start + count, len(groups))):
    x, y, ds = groups[i]
    cmd = ['python3', 'scripts/sokoban.py', str(x + OX), str(y + OY), ds, '--execute', '--max-steps', '200']
    print('GROUP', i, (x, y, ds), flush=True)
    r = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True)
    out = r.stdout + r.stderr
    tail = [l for l in out.splitlines() if 'STOPPED' in l or 'Error' in l or 'Traceback' in l or 'remaining' in l.lower()]
    print('\n'.join(tail[-5:]))
    if r.returncode != 0 or any('STOPPED' in l or 'Traceback' in l or 'Error' in l for l in tail):
        print('HALT at group', i); print(out[-1500:]); sys.exit(1)
print('DONE up to', min(start + count, len(groups)) - 1)
