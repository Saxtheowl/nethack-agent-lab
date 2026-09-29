#!/usr/bin/env python3
"""mzx.py [--steps N] [--all]: MAZE explorer for Gehennom filler mazes (dark,
1-wide corridors; maze spans screen x 2..78, rows 12..30).
Target = nearest known walkable square with an unknown neighbour inside the
maze bounds; the game's own travel command (_) walks there. Stops on: HP
loss, any monster letter / warning digit >= 2 within 4 squares that was not
there at the start, a new '>' or '<', a prompt/--More--, level change,
status change, danger messages. Never kicks, never attacks (travel only).
Run ONLY via: slots/1/w python3 mzx.py --steps 8"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import guard
import session

DANGER_MSG = re.compile(r'stole|steals|snatches|charms you|seduces|engulfs|swallows|You are frozen|'
                        r'Really attack|You feel|slime|turn to stone|stiffening|burn|You are hit|'
                        r'bites|hits!|touches you|summon|drains|You fall|trap door|magic trap|'
                        r'A trap|flash|explodes|You are caught|web|tele')
FLOOR = set('·.<>$%!?=()[/*`"_{#▒')
WALLS = set('│─┌┐└┘├┤┬┴┼')
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0), (1, -1), (1, 1), (-1, 1), (-1, -1)]
XMIN, XMAX, YMIN, YMAX = 2, 78, 12, 30
import os
WARN_R = int(os.environ.get('WARN_R', '2'))


def tile(rows, x, y):
    if not (1 <= x < 80 and 10 <= y <= 30) or y >= len(rows) or x >= len(rows[y]):
        return ' '
    return rows[y][x]


def walkable(rows, x, y, me):
    c = tile(rows, x, y)
    return (x, y) == me or c in FLOOR or c in '|-'  # '|'/'-' open doors


def frontier(rows, x, y):
    for dx, dy in DIRS:
        nx, ny = x + dx, y + dy
        if XMIN <= nx <= XMAX and YMIN <= ny <= YMAX and tile(rows, nx, ny) == ' ':
            return True
    return False


GOAL = None


def nearest(rows, start, dead):
    todo = collections.deque([start])
    seen = {start: 0}
    best = None
    while todo:
        cx, cy = todo.popleft()
        d = seen[(cx, cy)]
        if best and GOAL is None and d > best[0] + 2:
            break
        if (cx, cy) != start and f'{cx},{cy}' not in dead and frontier(rows, cx, cy):
            unk = sum(1 for dx, dy in DIRS if tile(rows, cx + dx, cy + dy) == ' ')
            g = 0 if GOAL is None else 3 * max(abs(cx - GOAL[0]), abs(cy - GOAL[1]))
            score = (d * 2 - unk + g, d)
            if best is None or score < best[1]:
                best = (d, score, (cx, cy))
        for dx, dy in DIRS:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) in seen or not walkable(rows, nx, ny, start):
                continue
            if tile(rows, nx, ny) in '^0':
                continue
            seen[(nx, ny)] = d + 1
            todo.append((nx, ny))
    return best[2] if best else None


def threats(rows, me, pets, radius=4):
    out = set()
    x, y = me
    for row in range(max(10, y - radius), min(31, y + radius + 1)):
        for col in range(max(1, x - radius), min(80, x + radius + 1)):
            if (col, row) == me or (col, row) in pets:
                continue
            c = tile(rows, col, row)
            if c.isalpha() or c in "@&;:'" or c in '2345':
                out.add((c, col, row))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--steps', type=int, default=8)
    p.add_argument('--all', action='store_true')
    p.add_argument('--toward', type=int, nargs=2, help='prefer frontiers near this x y')
    args = p.parse_args()
    global GOAL
    if args.toward:
        GOAL = tuple(args.toward)
    obs = guard.observe(session)
    st = guard.state(*obs)
    if st is None:
        raise SystemExit('Not at a map prompt.')
    level = st['level']
    store = Path(__file__).resolve().parent / 'mzx-dead.json'
    try:
        data = json.loads(store.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    dead = set(data.get(str(level), []))
    hp0, status0 = st['hp'], st['status']
    if st['hp'] * 10 < st['max_hp'] * 8:
        print('mzx stop: HP below 80%')
        session.print_screen(True)
        return
    base = {(c, x, y) for c, x, y in threats(st['rows'], st['position'], st['pets'], 8)}
    base_chars = {c for c, _, _ in base}
    stairs0 = sum(r[1:80].count('>') + r[1:80].count('<') for r in st['rows'][10:31])
    msgs0 = {r[1:81] for r in st['rows'][1:9]}
    reason = 'step budget used'
    for _ in range(args.steps):
        target = nearest(st['rows'], st['position'], dead)
        if target is None:
            reason = 'no frontier left (maze explored or blocked)'
            break
        before = st['position']
        with open('/dev/null', 'w') as sink:
            old, sys.stdout = sys.stdout, sink
            try:
                session.travel(*target)
            except RuntimeError as e:
                sys.stdout = old
                reason = f'travel failed: {e}'
                break
            finally:
                sys.stdout = old
        obs = guard.settled(session) or guard.observe(session)
        st2 = guard.state(*obs)
        if st2 is None:
            reason = 'prompt or unrecognized screen (--More--?)'
            break
        if st2['position'] == target:
            if frontier(st2['rows'], *target):
                dead.add(f'{target[0]},{target[1]}')
        elif st2['position'] == before:
            dead.add(f'{target[0]},{target[1]}')
        st = st2
        if st['hp'] < hp0:
            reason = f'HP loss {hp0}->{st["hp"]}'
            break
        if st['level'] != level:
            reason = 'level changed'
            break
        if st['status'] != status0 and re.search(r'Hungry|Weak|Faint|Blind|Conf|Stun|Hallu|Slime|Stone|Ill|Lev', st['status']):
            reason = 'status changed: ' + st['status'].strip()[-40:]
            break
        msgs = [r[1:81].strip() for r in st['rows'][1:9]]
        new = [m for m in msgs if m and m not in {x.strip() for x in msgs0}]
        bad = next((m for m in new if DANGER_MSG.search(m)), None)
        if bad:
            reason = f'message: {bad[:75]}'
            break
        th = threats(st['rows'], st['position'], st['pets'])
        me = st['position']
        dist = lambda t: max(abs(t[1] - me[0]), abs(t[2] - me[1]))
        fresh = {t for t in th if (t[0] in '345' and dist(t) <= WARN_R) or (t[0] == '2' and dist(t) <= 1)
                 or (not t[0].isdigit() and t[0] not in base_chars)}
        if fresh:
            reason = 'monster/warning near: ' + ' '.join(f'{c}@{x},{y}' for c, x, y in sorted(fresh))
            break
        if not args.all and sum(r[1:80].count('>') + r[1:80].count('<') for r in st['rows'][10:31]) > stairs0:
            reason = 'new staircase seen'
            break
    data[str(level)] = sorted(dead)
    store.write_text(json.dumps(data))
    print('mzx stop:', reason)
    session.print_screen(True)


if __name__ == '__main__':
    main()
