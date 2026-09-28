#!/usr/bin/env python3
"""pick.py PATTERN X,Y [X,Y...]: travel to each cell, ',' and select menu entries whose text matches PATTERN (regex). Single-object squares: picked only if pattern matches the 'You see here' text."""
import re, subprocess, sys, os
R = os.path.dirname(os.path.abspath(__file__)) + '/../..'
os.environ['NH_SLOT'] = '4'
def sess(*a): return subprocess.run(['python3','scripts/session.py',*a],cwd=R,capture_output=True,text=True).stdout
pat = re.compile(sys.argv[1])
for c in sys.argv[2:]:
    x, y = c.split(',')
    subprocess.run(['scripts/go', x, y, '6'], cwd=R, capture_output=True, text=True)
    s = sess('screen')
    if f'Neighbors of @({x},{y})' not in sess('screen','--compact'): print(c, 'not reached'); continue
    here = sess('keys','--compact','--raw',':')
    sess('keys','--named','Escape')
    hl = [l for l in here.splitlines() if re.match(r'^0[1-7] ', l)]
    if hl and 'You see here' in hl[-1] and not pat.search(hl[-1]): print(c, 'skip', hl[-1][5:70]); continue
    s = sess('keys','--raw',',')
    if 'Pick up what?' in s:
        keys = ''
        L = s.splitlines(); col = None
        for l in L:
            if col is None and 'Pick up what?' in l: col = l.index('Pick up what?')
            elif col is not None:
                seg = l[col:].split('│')[0]
                m = re.match(r' ?([a-zA-Z$])\) (.*)', seg)
                if m and pat.search(m.group(2)) and m.group(1) not in keys: keys += m.group(1)
        if keys: sess('keys','--raw',keys)
        out = sess('keys','--compact','--named','Enter')
        print(c, 'menu', keys, [l[5:80].strip() for l in out.splitlines() if l.startswith('07')])
    else:
        print(c, [l[5:80].strip() for l in s.splitlines() if re.match(r'^0[67] |^│',l)][-1:])
