#!/usr/bin/env python3
"""adjfight.py GLYPHS [n]: repeatedly F-attack an adjacent monster whose glyph is in GLYPHS.
Stops: none adjacent, HP < 60%, HP drop >= 1/5 max in one blow, prompt, stole/hunger."""
import re, subprocess, sys, os
os.environ['NH_SLOT'] = '4'
R = os.path.dirname(os.path.abspath(__file__)) + '/../..'
G = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 10
def sess(*a):
    return subprocess.run(['python3', 'scripts/session.py', *a], cwd=R, capture_output=True, text=True).stdout
D = {(-1,-1):'7',(0,-1):'8',(1,-1):'9',(-1,0):'4',(1,0):'6',(-1,1):'1',(0,1):'2',(1,1):'3'}
s = sess('screen', '--compact')
def hp(s):
    m = re.search(r'HP:(\d+)\((\d+)\)', s); return int(m[1]), int(m[2])
for i in range(N):
    h, mx = hp(s)
    if h * 10 < mx * 6: print('STOP HP<60%'); break
    m = re.search(r'^Map features.*$', s, re.M).group(0)
    me = re.search(r' @@(\d+),(\d+)', m); hx, hy = int(me[1]), int(me[2])
    tgt = None
    for g, x, y in re.findall(r' (\S)@(\d+),(\d+)', m):
        dx, dy = int(x)-hx, int(y)-hy
        if g in G and (dx, dy) in D:
            lk = subprocess.run(['scripts/look', x, y], cwd=R, capture_output=True, text=True).stdout
            if 'peaceful' in lk: print('skip peaceful', g, x, y); continue
            tgt = D[(dx, dy)]; break
    if not tgt: print('no adjacent target'); break
    s = sess('keys', '--compact', '--raw', 'F' + tgt)
    for _ in range(8):
        if not re.search(r'>>|--More--', s): break
        s = sess('keys', '--compact', '--named', 'Enter')
    msg = [l[5:85] for l in s.splitlines() if re.match(r'^0[1-7] ', l)]
    h2, _ = hp(s)
    print(f'[{i}] F{tgt} HP:{h2}/{mx} {msg[-1].strip() if msg else ""}')
    if 'Really attack' in s: sess('keys','--raw','n'); print('STOP peaceful (answered n)'); break
    if (h - h2) * 5 >= mx: print('STOP big loss'); break
    if re.search(r'--More--|\[yn|stole', msg[-1] if msg else '') or re.search(r'Weak|Fainting', s): print('STOP prompt/stole/hunger'); break
print(re.search(r'^Map features.*$', s, re.M).group(0))
