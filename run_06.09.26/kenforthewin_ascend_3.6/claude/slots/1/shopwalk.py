#!/usr/bin/env python3
"""shopwalk.py KEYS : one step per key inside a shop; after each step print the
position and the newest 'You see here' / 'There are several' message.
Stops on 'Really attack', a prompt, HP loss, a mimic ('Wait!'), or a
position that did not change. Run via: slots/1/w python3 shopwalk.py 6688"""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import guard
import session

MOVES = {'1': (-1, 1), '2': (0, 1), '3': (1, 1), '4': (-1, 0), '6': (1, 0), '7': (-1, -1), '8': (0, -1), '9': (1, -1)}
st = guard.state(*guard.observe(session))
if st is None:
    sys.exit('not at map prompt')
for k in sys.argv[1]:
    x, y = st['position']
    dx, dy = MOVES[k]
    tgt = st['rows'][y + dy][x + dx]
    if tgt.isalpha() or tgt in '@]':
        print(f'stop: {tgt} on target square {x+dx},{y+dy}')
        break
    session.send(k, publish=False)
    time.sleep(.3)
    obs = guard.settled(session) or guard.observe(session)
    new = guard.state(*obs)
    text = obs[0]
    if 'Really attack' in text or 'Wait!' in text or '--More--' in text or new is None:
        print('stop: prompt/mimic/--More--')
        break
    msgs = [r[1:81].strip(' │') for r in text.splitlines()[1:9]]
    seen = [m for m in msgs if re.search(r'You see here|There (are|is) (several|many)|for sale', m)]
    print(new['position'], seen[-1] if seen else '-')
    if new['hp'] < st['hp']:
        print('stop: HP loss'); break
    if new['position'] == st['position']:
        print('stop: did not move'); break
    st = new
