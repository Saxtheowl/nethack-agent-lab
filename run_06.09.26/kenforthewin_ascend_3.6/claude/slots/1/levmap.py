#!/usr/bin/env python3
"""Decode the MAP of a compiled special level (.lev in nhdat = static des data).
Usage: levmap.py wizard1 WIDTH [start_marker_hex]"""
import re, sys
path = '../../engine/install/games/lib/nethackdir/nhdat'
data = open(path, 'rb').read()
name = sys.argv[1] + '.lev'
width = int(sys.argv[2])
d = data[:4000].decode('latin1')
ents = re.findall(r'n([A-Za-z0-9_-]+\.?[a-z]*)\s+(\d+)', d)
offs = sorted(int(o) for _, o in ents)
start = int(dict(ents)[name])
end = min([o for o in offs if o > start] + [len(data)])
blob = data[start:end]
# stored value = levl typ + 1
ch = {0: '?', 1: ' ', 2: '|', 3: '-', 4: '-', 5: '-', 6: '-', 7: '-', 8: '-', 9: '-',
      10: '|', 11: '|', 12: '#', 13: '#', 14: 'T', 15: 'S', 16: 'H', 17: 'P', 18: '}',
      19: 'W', 20: '#', 21: 'L', 22: '#', 23: '+', 24: '#', 25: '.', 26: '<'}
m = re.search(rb'\x03{%d}' % (width - 1), blob)
if not m:
    print('no map start'); sys.exit()
i = m.start()
row = 0
while i + width <= len(blob):
    seg = blob[i:i + width]
    if any(b > 26 or b == 0 for b in seg):
        break
    print('%2d %s' % (row, ''.join(ch.get(b, '?') for b in seg)))
    i += width; row += 1
print('map offset in lev', m.start(), 'rows', row)
print('after map bytes:', blob[i:i + 600])
