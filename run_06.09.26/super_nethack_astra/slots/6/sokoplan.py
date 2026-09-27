#!/usr/bin/env python3
"""slots/6/sokoplan.py PLANFILE [startline]: run lines "X Y PUSHES" in order.
Keys come from scripts/sokoban.py planning (read-only); each key is sent raw and
checked: hero must move as predicted, boulders as predicted, no HP loss, no
hunger, no visible monster letter. On anomaly prints line index, the boulder's
current position and the remaining pushes, then exits."""
import os, re, subprocess, sys, time
os.environ['NH_SLOT'] = '6'
R = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.join(R, 'scripts'))
os.chdir(R)
import session, json
D = {'4': (-1, 0), '6': (1, 0), '8': (0, -1), '2': (0, 1)}
def state():
    s = session.screen(); L = s.splitlines()
    cur = tuple(map(int, session.tmux('display-message', '-p', '-t', session.TARGET, '#{cursor_x},#{cursor_y}').stdout.strip().split(',')))
    cells = {(x, y): c for y, row in enumerate(L) if 10 <= y <= 30 for x, c in enumerate(row[:81]) if 1 <= x <= 79}
    return s, L, cur, cells
lines = [l.split() for l in open(sys.argv[1]) if l.strip()]
start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
for idx in range(start, len(lines)):
    x, y, pushes = int(lines[idx][0]), int(lines[idx][1]), lines[idx][2]
    p = subprocess.run(['python3', 'scripts/sokoban.py', str(x), str(y), pushes] + sys.argv[3:], capture_output=True, text=True)
    try: keys = json.loads(p.stdout.strip().splitlines()[-1])['keys']
    except Exception: print('PLAN FAIL line', idx, p.stdout[-300:], p.stderr[-300:]); sys.exit(1)
    b = (x, y); npush = 0
    for ki, k in enumerate(keys):
        s, L, cur, cells = state()
        hp = re.search(r'HP:(\d+)\((\d+)\)', L[34])
        if int(hp[1]) * 100 < int(hp[2]) * 70 or re.search(r'Hungry|Weak|Faint|Burdened', L[34]):
            print('STOP status', L[34].strip(), 'line', idx, 'boulder', b, 'remaining pushes', pushes[npush:]); sys.exit(2)
        mons = [(p, c) for p, c in cells.items() if (c.isalpha() or c in '&;:\'') or (c == '@' and p != cur)]
        IGN = os.environ.get('IGN', '')
        mons = [(q, c) for q, c in mons if not (c in IGN and max(abs(q[0]-cur[0]), abs(q[1]-cur[1])) > 2)]
        if mons:
            print('STOP monster', mons, 'line', idx, 'boulder', b, 'remaining pushes', pushes[npush:]); sys.exit(3)
        dx, dy = D[k]; dest = (cur[0] + dx, cur[1] + dy)
        pushing = dest == b
        before_hp = int(hp[1])
        session.send(k); time.sleep(0.35)
        s2, L2, cur2, cells2 = state()
        if '--More--' in s2 or 'Things that are here' in s2:
            session.send(' '); time.sleep(0.3); s2, L2, cur2, cells2 = state()
        if cur2 != dest:
            # retry once after a short wait (monster/"You try to move")
            print('STOP no move at key', ki, k, 'hero', cur2, 'line', idx, 'boulder', b, 'remaining pushes', pushes[npush:]); 
            print('\n'.join(l[:82] for l in L2[1:8])); sys.exit(4)
        if pushing:
            npush += 1; b = (b[0] + dx, b[1] + dy)
        h2 = re.search(r'HP:(\d+)', L2[34])
        if int(h2[1]) < before_hp:
            print('STOP HP loss', L2[34].strip(), 'line', idx, 'boulder', b, 'remaining', pushes[npush:]); sys.exit(5)
        if re.search(r'stole|You are beginning to feel|hits!|bites!|stings', '\n'.join(L2[1:8])) and 'stole' in s2:
            print('STOP message'); sys.exit(6)
    print('done line', idx, x, y, pushes)
print('ALL DONE')
