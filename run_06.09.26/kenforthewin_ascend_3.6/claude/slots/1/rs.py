#!/usr/bin/env python3
"""rs.py [target%] [max_turns]: rest (search) until HP >= target% of max.
One 's' per command below 70% HP (harness rule), 'n10s' above.
Stops on: HP loss, any non-pet creature within 3 squares, hunger change,
--More--/prompt, 'stole', level change, status change (Blind, Conf...).
Run ONLY via: slots/1/w python3 rs.py 90 300"""
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import guard
import session

target = int(sys.argv[1]) if len(sys.argv) > 1 else 90
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 300


def look():
    obs = guard.settled(session) or guard.observe(session)
    return guard.state(*obs), obs[0]


def creature_near(st, radius=3):
    x, y = st['position']
    for row in range(max(10, y - radius), min(31, y + radius + 1)):
        for col in range(max(1, x - radius), min(80, x + radius + 1)):
            if (col, row) == (x, y) or (col, row) in st['pets']:
                continue
            ch = st['rows'][row][col:col + 1]
            if ch and ch in os.environ.get('IGNORE', ''):
                continue
            if ch and (ch.isalpha() or ch in "@&;:'"):
                return f'{ch}@{col},{row}'
    return None


st, text = look()
if st is None:
    print('rs: not at a map prompt'); session.print_screen(True); sys.exit(1)
hp0, lvl0, stat0 = st['hp'], st['level'], re.sub(r'HP:\S+|Pw:\S+|T:\d+|\$:\d+|Xp:\S+', '', st['status'])
t0 = st['turn']
reason = 'turn budget used'
while st['turn'] - t0 < limit:
    if st['hp'] * 100 >= st['max_hp'] * target:
        reason = f"target reached HP {st['hp']}({st['max_hp']})"; break
    c = creature_near(st)
    if c:
        reason = f'creature near: {c}'; break
    key = 's' if st['hp'] * 10 < st['max_hp'] * 7 else 'n10s'
    session.send(key, publish=False)
    time.sleep(.2)
    new, text = look()
    if new is None:
        reason = 'prompt / --More-- / unrecognized screen'; break
    msgs = ' '.join(r[1:81] for r in new['rows'][1:9])
    if '--More--' in text:
        reason = '--More-- on screen'; st = new; break
    if new['hp'] < st['hp']:
        reason = f"HP loss {st['hp']} -> {new['hp']}"; st = new; break
    if new['level'] != lvl0:
        reason = 'level changed'; st = new; break
    stat = re.sub(r'HP:\S+|Pw:\S+|T:\d+|\$:\d+|Xp:\S+', '', new['status'])
    if stat.split() != stat0.split():
        reason = f'status changed: {stat.strip()}'; st = new; break
    if re.search(r'stole|steals|snatches|seduces|charms you', msgs):
        reason = 'theft message'; st = new; break
    st = new
print('rs stop:', reason)
session.print_screen(True)
