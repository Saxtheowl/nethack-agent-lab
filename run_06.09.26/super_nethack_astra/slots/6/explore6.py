#!/usr/bin/env python3
"""Frontier exploration over the remembered map: travel to the nearest known
walkable cell that touches unexplored space, repeat. Stops on HP loss, a
prompt, a new staircase, or when nothing is left. Proposes only moves the
game's own travel command performs; every travel is logged by session.py."""
import argparse
import collections
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'scripts'))
import guard
import session

THIEF_MSG = re.compile(r'stole|steals|snatches|charms you|seduces you|very attracted|Really attack|purse feels lighter|You are frozen|engulfs you')
THIEF_GLYPHS = set('nl')

FLOOR = set('▒·.<>$%!?=()[/*`"_{#') | set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ@&;:\'')
DOORS = set('-|+')
WALLS = set('│─┌┐└┘├┤┬┴┼')
DIRS = [(0, -1), (1, 0), (0, 1), (-1, 0), (1, -1), (1, 1), (-1, 1), (-1, -1)]


def tile(rows, x, y):
    return rows[y][x] if 1 <= x < 80 and 10 <= y <= 30 and x < len(rows[y]) else ' '


def is_door(rows, x, y):
    c = tile(rows, x, y)
    if c not in DOORS and c != '@':  # the hero may be standing in a doorway
        return False
    return ((tile(rows, x - 1, y) in WALLS and tile(rows, x + 1, y) in WALLS)
            or (tile(rows, x, y - 1) in WALLS and tile(rows, x, y + 1) in WALLS))


def is_gap(rows, x, y):
    """A doorless doorway: floor with wall on both sides."""
    if tile(rows, x, y) not in '·.':
        return False
    return ((tile(rows, x - 1, y) in WALLS and tile(rows, x + 1, y) in WALLS)
            or (tile(rows, x, y - 1) in WALLS and tile(rows, x, y + 1) in WALLS))


def walkable(rows, x, y):
    c = tile(rows, x, y)
    return c in FLOOR or is_door(rows, x, y) or c == '0'


def frontier(rows, x, y):
    if tile(rows, x, y) in '0^':
        return False
    for dx, dy in DIRS:
        nx, ny = x + dx, y + dy
        if 1 <= nx < 80 and 11 <= ny <= 29 and tile(rows, nx, ny) == ' ':
            return True
    return False


def openness(rows, x, y):
    """Unknown cells within radius 2: real unexplored space scores high,
    a floor cell merely touching undisplayed rock scores low."""
    return sum(1 for dy in range(-2, 3) for dx in range(-2, 3)
               if 1 <= x + dx < 80 and 11 <= y + dy <= 29 and tile(rows, x + dx, y + dy) == ' ')


MINOPEN = 7

def nearest(rows, start, dead):
    todo = collections.deque([start])
    seen = {start: 0}
    parent = {start: None}
    best = None
    while todo:
        cx, cy = todo.popleft()
        if (cx, cy) != start and frontier(rows, cx, cy) and f'{cx},{cy}' not in dead:
            o = openness(rows, cx, cy)
            corridor = tile(rows, cx, cy) in '▒#' or is_door(rows, cx, cy) or is_gap(rows, cx, cy)
            exits = sum(1 for dx, dy in DIRS if walkable(rows, cx + dx, cy + dy))
            # A corridor only leads somewhere new at a dead end (continuation
            # unseen or hidden); elsewhere its blank neighbours are just rock.
            points = any(tile(rows, cx + dx, cy + dy) == ' ' and walkable(rows, cx - dx, cy - dy)
                         for dx, dy in DIRS)
            if (points and o >= 3) if corridor else o >= MINOPEN:
                score = seen[(cx, cy)] - 3 * o
                if best is None or score < best[0]:
                    best = (score, (cx, cy), seen[(cx, cy)])
        for dx, dy in DIRS:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) in seen or not walkable(rows, nx, ny) or tile(rows, nx, ny) == '0':
                continue
            if dx and dy and (is_door(rows, cx, cy) or is_door(rows, nx, ny)):
                continue
            seen[(nx, ny)] = seen[(cx, cy)] + 1
            parent[(nx, ny)] = (cx, cy)
            todo.append((nx, ny))
    if not best:
        return None, None
    path, cur = [], best[1]
    while cur != start:
        path.append(cur)
        cur = parent[cur]
    return best[1], path[::-1]


def open_a_door(st, dead):
    """Go next to the nearest reachable closed door ('+') and open it
    (kick when locked, a few tries). Returns True if something was attempted."""
    rows, start = st['rows'], st['position']
    seen = {start}
    todo = collections.deque([start])
    keys = {(0, -1): '8', (1, 0): '6', (0, 1): '2', (-1, 0): '4'}
    while todo:
        cx, cy = todo.popleft()
        for (dx, dy), k in keys.items():
            nx, ny = cx + dx, cy + dy
            if tile(rows, nx, ny) == '+' and f'd{nx},{ny}' not in dead:  # walls may be unseen yet
                dead.add(f'd{nx},{ny}')
                with open('/dev/null', 'w') as sink:
                    old, sys.stdout = sys.stdout, sink
                    try:
                        if (cx, cy) != start:
                            try:
                                session.travel(cx, cy)
                            except RuntimeError:
                                return False
                    finally:
                        sys.stdout = old
                for _ in range(6):
                    session.send(k)
                    time.sleep(.6)
                    text = session.screen()
                    if 'This door is locked' in text:
                        session.send('k')  # kick
                        time.sleep(.3)
                        session.send(k)
                        time.sleep(.8)
                    now = guard.state(*guard.observe(session))
                    if now is None or tile(now['rows'], nx, ny) != '+':
                        break
                return True
        for dx, dy in DIRS:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) in seen or not walkable(rows, nx, ny) or tile(rows, nx, ny).isalpha():
                continue
            if dx and dy and (is_door(rows, cx, cy) or is_door(rows, nx, ny)):
                continue
            seen.add((nx, ny))
            todo.append((nx, ny))
    return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--steps', type=int, default=6)
    p.add_argument('--all', action='store_true', help='do not stop at new stairs')
    p.add_argument('--search', type=int, default=10, help='searches at corridor dead ends (0 = off)')
    p.add_argument('--minopen', type=int, default=7)
    args = p.parse_args()
    global MINOPEN
    MINOPEN = args.minopen
    obs = guard.observe(session)
    st = guard.state(*obs)
    if st is None:
        raise SystemExit('Not at a map prompt.')
    level_num = st['level']
    level = st['level']
    # Key the dead-end cache by level AND the upstairs position, so Mines and
    # main-dungeon levels with the same Dlvl number do not share it.
    ups = sorted((x, y) for y in range(10, 31) for x in range(1, 80) if st['rows'][y][x:x + 1] == '<')
    level = f"{level}@{ups[0][0]},{ups[0][1]}" if ups else str(level)
    store = session.RUNTIME / f'explore6b-{session.SLOT}.json'
    try:
        data = json.loads(store.read_text())
    except FileNotFoundError:
        data = {}
    dead = set(data.get(str(level), []))
    fails = {}
    hp0 = st['hp']
    hunger0 = st['status']
    msgs0 = {r[1:81] for r in st['rows'][1:9]}
    if st['hp'] * 10 < st['max_hp'] * 6:
        print('explore stop: HP below 60% — rest first: go upstairs / away from monsters, let the pet fight')
        session.print_screen(True)
        return
    known_down = sum(r[1:80].count('>') for r in st['rows'][10:31])
    reason = 'step budget used'
    for _ in range(args.steps):
        rows = st['rows']
        target, path = nearest(rows, st['position'], dead)
        if target is None:
            if open_a_door(st, dead):
                st = guard.state(*guard.observe(session)) or st
                continue
            reason = 'no reachable frontier left'
            break
        before = st['position']
        with open('/dev/null', 'w') as sink:
            old = sys.stdout
            sys.stdout = sink
            try:
                session.travel(*target)
            finally:
                sys.stdout = old
        obs = guard.observe(session)
        st2 = guard.state(*obs)
        if st2 is None:
            reason = 'prompt or unrecognized screen'
            break
        if st2['position'] == target:
            # Reached a corridor dead end: search there once for hidden passages.
            rows2 = st2['rows']
            exits = sum(1 for dx, dy in DIRS if walkable(rows2, target[0] + dx, target[1] + dy))
            if (args.search and exits <= 1 and frontier(rows2, *target)
                    and f's{target[0]},{target[1]}' not in dead):
                dead.add(f's{target[0]},{target[1]}')
                session.send(f'n{args.search}s')
                obs = guard.settled(session)
                st2 = guard.state(*obs) if obs else st2
            # If its unknown neighbours are still unknown, never revisit.
            if st2 and frontier(st2['rows'], *target) and st2['position'] == target:
                dead.add(f'{target[0]},{target[1]}')
        elif st2['position'] == before:
            # Travel refuses to start beside any non-pet monster: take up to
            # two plain steps along the path, never into a monster glyph.
            keys = {(0, -1): '8', (1, 0): '6', (0, 1): '2', (-1, 0): '4',
                    (1, -1): '9', (1, 1): '3', (-1, 1): '1', (-1, -1): '7'}
            moved = False
            for cell in path[:2]:
                cur = st2['position']
                if tile(st2['rows'], *cell).isalpha() or tile(st2['rows'], *cell) == '@':
                    break
                d = (cell[0] - cur[0], cell[1] - cur[1])
                if d not in keys:
                    break
                session.send('m' + keys[d])  # m: never attack, even an unseen monster
                obs = guard.settled(session)
                st2 = guard.state(*obs) if obs else None
                if st2 is None or st2['position'] != cell:
                    break
                moved = True
            if st2 is None:
                reason = 'prompt or unrecognized screen after a step'
                break
            if not moved:
                key = f'{target[0]},{target[1]}'
                fails[key] = fails.get(key, 0) + 1
                if fails[key] >= 3:
                    dead.add(key)
        st = st2
        if st['hp'] < hp0:
            reason = 'HP loss'
            break
        if not args.all and sum(r[1:80].count('>') for r in st['rows'][10:31]) > known_down:
            reason = 'new downstairs seen'
            break
        if st['level'] != level_num:
            reason = 'level changed'
            break
        # thieves and traps for the unwary (slot 2 lost everything to a nymph
        # during explore): stop on theft/charm messages or a nymph/leprechaun in view
        msgs = [r[1:81] for r in st['rows'][1:9]]
        new_msgs = [m for m in msgs if m.strip() and m not in msgs0]
        danger = next((m.strip() for m in new_msgs if THIEF_MSG.search(m)), None)
        if danger:
            reason = f'danger message: {danger[:70]}'
            break
        if any(c in THIEF_GLYPHS for r in st['rows'][10:31] for c in r[1:80]):
            reason = 'nymph (n) or leprechaun (l) in view: kill it at range, never explore near it'
            break
        hunger = re.search(r'\b(Hungry|Weak|Fainting)\b', st['status'])
        if hunger and hunger[1] not in hunger0:
            reason = f'{hunger[1]}: eat now (keep 2+ food items)'
            break
    data[str(level)] = sorted(dead)
    store.write_text(json.dumps(data))
    print('explore stop:', reason)
    session.print_screen(True)


if __name__ == '__main__':
    main()
