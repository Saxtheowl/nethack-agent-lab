#!/usr/bin/env python3
"""Castle passtune Mastermind helper (NetHack 3.6.7 music.c feedback, exact).
Usage: python3 mm.py [GUESS:TUMBLERS:GEARS ...]   e.g.  mm.py ABCDE:2:1 FGABC:0:1
Prints the number of tunes still consistent and the next guess to play.
The feedback replicates music.c: for each guess note x (x<5): gear if buf[x]==tune[x], else the first
unmatched y with buf[x]==tune[y] and buf[y]!=tune[y] is a tumbler (y then marked matched)."""
import itertools, sys, random

NOTES = 'ABCDEFG'


def fb(buf, tune):
    t = g = 0
    matched = [False] * 5
    for x in range(5):
        if buf[x] == tune[x]:
            g += 1
            matched[x] = True
        else:
            for y in range(5):
                if not matched[y] and buf[x] == tune[y] and buf[y] != tune[y]:
                    t += 1
                    matched[y] = True
                    break
    return t, g


ALL = [''.join(p) for p in itertools.product(NOTES, repeat=5)]
hist = []
for a in sys.argv[1:]:
    gss, t, g = a.split(':')
    hist.append((gss.upper(), int(t), int(g)))
cands = [c for c in ALL if all(fb(gs, c) == (t, g) for gs, t, g in hist)]
print('consistent tunes:', len(cands))
if not cands:
    sys.exit('no tune fits: check the history')
if len(cands) <= 3:
    print('candidates:', ' '.join(cands))
if not hist:
    print('next guess: AABCD')
    sys.exit()
# minimax: choose the guess (from the candidates, plus a sample of all tunes when many remain)
pool = cands if len(cands) <= 1500 else random.Random(1).sample(cands, 1500)
guesses = pool if len(cands) <= 300 else pool + random.Random(2).sample(ALL, 300)
best = None
for gs in guesses:
    parts = {}
    for c in pool:
        k = fb(gs, c)
        parts[k] = parts.get(k, 0) + 1
    score = (max(parts.values()), 0 if gs in cands else 1)
    if best is None or score < best[0]:
        best = (score, gs)
print('next guess:', best[1], '(worst case left ~%d of sample %d)' % (best[0][0], len(pool)))
