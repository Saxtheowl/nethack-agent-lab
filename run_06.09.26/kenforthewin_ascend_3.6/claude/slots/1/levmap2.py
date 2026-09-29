#!/usr/bin/env python3
"""Decode MAP blocks of a compiled special level: prints every long run of
terrain bytes (stored value = levl typ + 1) cut in rows of WIDTH.
Usage: levmap2.py fakewiz1 WIDTH [minlen]"""
import re, sys
path = '../../engine/install/games/lib/nethackdir/nhdat'
data = open(path, 'rb').read()
name = sys.argv[1] + '.lev'
width = int(sys.argv[2])
minlen = int(sys.argv[3]) if len(sys.argv) > 3 else 40
d = data[:4000].decode('latin1')
ents = re.findall(r'n([A-Za-z0-9_-]+\.?[a-z]*)\s+(\d+)', d)
offs = sorted(int(o) for _, o in ents)
start = int(dict(ents)[name])
end = min([o for o in offs if o > start] + [len(data)])
blob = data[start:end]
ch = {1: ' ', 2: '|', 3: '-', 4: '-', 5: '-', 6: '-', 7: '-', 8: '-', 9: '-',
      10: '|', 11: '|', 12: '#', 13: 'T', 14: 'T', 15: 'S', 16: 'H', 17: 'P', 18: '}',
      19: 'W', 20: '#', 21: 'L', 22: '#', 23: '+', 24: '#', 25: '.', 26: '<'}
for m in re.finditer(rb'[\x01-\x1a]{%d,}' % minlen, blob):
    seg = m.group()
    print('run at', m.start(), 'len', len(seg), 'prev bytes', list(blob[m.start()-8:m.start()]))
    for i in range(0, len(seg), width):
        print('  ' + ''.join(ch.get(b, '?') for b in seg[i:i + width]))
