#!/usr/bin/env python3
"""dfx.py [--steps N] [--all] [--toward X Y] [--reset]: depth-first explorer for
dark mazes (walled or CORRIDOR mazes where rock stays blank). Single guarded
steps only (no travel): every square it stands on is remembered in
dfx-visited.json, so a square is explored once. Target = nearest displayed
walkable square not yet visited that still has a blank neighbour.
Stops on: HP loss, a monster letter / warning digit near, new stairs, a prompt
or --More--, level change, status change, danger messages. Never attacks
('m' prefix), never steps on traps/boulders/water.
Run ONLY via: slots/1/w python3 dfx.py --steps 150"""
import argparse
import collections
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import guard
import session

DANGER_MSG = re.compile(r'stole|steals|snatches|charms you|seduces|engulfs|swallows|You are frozen|'
                        r'Really attack|slime|turn to stone|stiffening|You are hit|'
                        r'bites|hits!|touches you|summon|drains|You fall|trap door|magic trap|bear trap|'
                        r'land mine|fire trap|sleeping gas|polymorph trap|level tele|anti-magic|rust trap|'
                        r'flash|explodes|You are caught|stuck to the web|teleport|You feel')
FLOOR = set('·.<>$%!?=()[/*`"_{#▒|-')
DIRS = {(0, -1): '8', (1, 0): '6', (0, 1): '2', (-1, 0): '4',
        (1, -1): '9', (1, 1): '3', (-1, 1): '1', (-1, -1): '7'}
XMIN, XMAX, YMIN, YMAX = 1, 79, 11, 30
WARN_R = int(os.environ.get('WARN_R', '2'))
STORE = Path(__file__).resolve().parent / 'dfx-visited.json'


def tile(rows, x, y):
    if not (1 <= x < 80 and 10 <= y <= 30) or y >= len(rows) or x >= len(rows[y]):
        return ' '
    return rows[y][x]


def walk_ok(rows, x, y):
    return tile(rows, x, y) in FLOOR


def open_nb(rows, x, y):
    return any(XMIN <= x + dx <= XMAX and YMIN <= y + dy <= YMAX and tile(rows, x + dx, y + dy) == ' '
               for dx, dy in DIRS)


def plan(rows, me, visited, blocked, goal):
    """BFS from me over walkable squares; return path to the best target."""
    todo = collections.deque([me])
    parent = {me: None}
    dist = {me: 0}
    best = None
    while todo:
        c = todo.popleft()
        d = dist[c]
        if best and goal is None and d > best[0]:
            break
        if c != me and c not in visited and open_nb(rows, *c):
            g = 0 if goal is None else int(os.environ.get('GOALW', '2')) * max(abs(c[0] - goal[0]), abs(c[1] - goal[1]))
            sc = d + g
            if best is None or sc < best[0]:
                best = (sc, c)
        # orthogonal first: corridors are orthogonal
        for (dx, dy) in sorted(DIRS, key=lambda v: abs(v[0]) + abs(v[1])):
            n = (c[0] + dx, c[1] + dy)
            if n in parent or (n not in SAFE and (not walk_ok(rows, *n) or tile(rows, *n) in '^0}')):
                continue
            if (c, n) in blocked:
                continue
            parent[n] = c
            dist[n] = d + 1
            todo.append(n)
    if not best:
        return None
    path, cur = [], best[1]
    while cur != me:
        path.append(cur)
        cur = parent[cur]
    return path[::-1]


IGN = set()
SAFE = set()


def threats(rows, me, pets, radius=4):
    out = set()
    x, y = me
    for row in range(max(10, y - radius), min(31, y + radius + 1)):
        for col in range(max(1, x - radius), min(80, x + radius + 1)):
            if (col, row) == me or (col, row) in pets or (col, row) in IGN:
                continue
            c = tile(rows, col, row)
            if c in os.environ.get('DFX_IGN', ''):
                continue
            if c.isalpha() or c in "@&;:'" or c in '2345':
                out.add((c, col, row))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--steps', type=int, default=100)
    p.add_argument('--all', action='store_true')
    p.add_argument('--up', action='store_true', help="also stop on a new '<' (Vlad's branch levels)")
    p.add_argument('--toward', type=int, nargs=2)
    p.add_argument('--reset', action='store_true')
    p.add_argument('--ignore', default='', help='x,y;x,y statues to ignore (also remembered)')
    p.add_argument('--safe', default='', help="x,y;x,y harmless traps (squeaky boards) or boulders to walk over (remembered)")
    args = p.parse_args()
    goal = tuple(args.toward) if args.toward else None
    st = guard.state(*guard.observe(session))
    if st is None:
        raise SystemExit('Not at a map prompt.')
    level = str(st['level'])
    try:
        data = json.loads(STORE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    if args.reset:
        data[level] = []
    visited = {tuple(v) for v in data.get(level, [])}
    ign = {tuple(v) for v in data.get('ign' + level, [])}
    for part in filter(None, args.ignore.split(';')):
        x, y = part.split(',')
        ign.add((int(x), int(y)))
    data['ign' + level] = sorted(ign)
    safe = {tuple(v) for v in data.get('safe' + level, [])}
    for part in filter(None, args.safe.split(';')):
        x, y = part.split(',')
        safe.add((int(x), int(y)))
    data['safe' + level] = sorted(safe)
    SAFE.clear()
    SAFE.update(safe)
    blocked = set()
    IGN.update(ign)
    hp0, status0 = st['hp'], st['status']
    conds0 = set(re.findall(r'Hungry|Weak|Faint|Blind|Conf|Stun|Hallu|Slime|Stone|Ill|Lev|Burdened|Stressed|Strained', status0))
    if st['hp'] * 10 < st['max_hp'] * 8:
        print('dfx stop: HP below 80%')
        session.print_screen(True)
        return
    base_chars = {c for c, _, _ in threats(st['rows'], st['position'], st['pets'], 8) if not c.isdigit()}
    start = st['position']
    def nstairs(rows):
        n = 0
        for y in range(10, 31):
            for x in range(1, 80):
                c = tile(rows, x, y)
                if (x, y) != start and (c == '>' or (args.up and c == '<')):
                    n += 1
        return n
    stairs0 = nstairs(st['rows'])
    msgs0 = {r[1:81].strip() for r in st['rows'][1:9]}
    reason = 'step budget used'
    steps = 0
    path = []
    while steps < args.steps:
        me = st['position']
        visited.add(me)
        if not path:
            path = plan(st['rows'], me, visited, blocked, goal)
            if path is None:
                reason = 'nothing left to explore from here'
                break
        nxt = path.pop(0)
        d = (nxt[0] - me[0], nxt[1] - me[1])
        if d not in DIRS:
            path = []
            continue
        session.send('m' + DIRS[d])
        steps += 1
        obs = guard.settled(session) or guard.observe(session)
        st2 = guard.state(*obs)
        if st2 is None:
            reason = 'prompt or unrecognized screen (--More--?)'
            break
        if st2['position'] != nxt:
            blocked.add((me, nxt))
            path = []
        st = st2
        if st['hp'] < hp0:
            reason = f'HP loss {hp0}->{st["hp"]}'
            break
        if str(st['level']) != level:
            reason = 'level changed'
            break
        conds = set(re.findall(r'Hungry|Weak|Faint|Blind|Conf|Stun|Hallu|Slime|Stone|Ill|Lev|Burdened|Stressed|Strained', st['status']))
        if conds - conds0:
            reason = 'status changed: ' + st['status'].strip()[-40:]
            break
        msgs = [r[1:81].strip() for r in st['rows'][1:9]]
        new = [m for m in msgs if m and m not in msgs0]
        bad = next((m for m in new if DANGER_MSG.search(m) and not m.startswith('You find')), None)
        if bad:
            reason = f'message: {bad[:75]}'
            break
        msgs0 |= set(new)
        me2 = st['position']
        dd = lambda t: max(abs(t[1] - me2[0]), abs(t[2] - me2[1]))
        th = threats(st['rows'], me2, st['pets'])
        fresh = {t for t in th if (t[0] in '345' and dd(t) <= WARN_R) or (t[0] == '2' and dd(t) <= 1)
                 or (not t[0].isdigit() and (t[0] not in base_chars or dd(t) <= 2))}
        if fresh:
            reason = 'monster/warning near: ' + ' '.join(f'{c}@{x},{y}' for c, x, y in sorted(fresh))
            break
        if not args.all and nstairs(st['rows']) > stairs0:
            reason = 'new staircase seen'
            break
    visited.add(st['position'])
    data[level] = sorted(visited)
    STORE.write_text(json.dumps(data))
    print(f'dfx stop after {steps} steps: {reason}')
    session.print_screen(True)


if __name__ == '__main__':
    main()
