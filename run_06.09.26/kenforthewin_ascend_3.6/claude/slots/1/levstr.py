#!/usr/bin/env python3
"""Print printable strings of one compiled special level (.lev) from nhdat
(static game data = the des file, a spoiler). Usage: levstr.py wizard1"""
import re, sys
path = '../../engine/install/games/lib/nethackdir/nhdat'
data = open(path, 'rb').read()
name = sys.argv[1] + '.lev'
d = data[:4000].decode('latin1')
ents = re.findall(r'n([A-Za-z0-9_-]+\.?[a-z]*)\s+(\d+)', d)
offs = sorted(int(o) for _, o in ents)
start = dict(ents)[name]
start = int(start)
end = min([o for o in offs if o > start] + [len(data)])
blob = data[start:end]
for m in re.finditer(rb'[\x20-\x7e\n]{3,}', blob):
    print(m.start(), repr(m.group().decode()))
