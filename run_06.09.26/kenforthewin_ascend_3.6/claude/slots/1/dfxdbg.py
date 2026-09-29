#!/usr/bin/env python3
"""dfxdbg.py: print which frontier squares dfx sees and whether they are reachable (read-only)."""
import collections, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard, session
import dfx
st = guard.state(*guard.observe(session))
rows, me = st['rows'], st['position']
data = json.loads(dfx.STORE.read_text())
lv = str(st['level'])
visited = {tuple(v) for v in data.get(lv, [])}
dfx.SAFE.update(tuple(v) for v in data.get('safe' + lv, []))
seen = {me}; q = collections.deque([me])
while q:
    c = q.popleft()
    for dx, dy in dfx.DIRS:
        n = (c[0]+dx, c[1]+dy)
        if n in seen: continue
        if n not in dfx.SAFE and (not dfx.walk_ok(rows, *n) or dfx.tile(rows, *n) in '^0}'): continue
        seen.add(n); q.append(n)
fr = [(x, y) for y in range(10, 31) for x in range(1, 80) if dfx.walk_ok(rows, x, y) and (x, y) not in visited and dfx.open_nb(rows, x, y)]
print('me', me, 'reachable', len(seen))
print('frontier reachable:', [f for f in fr if f in seen][:40])
print('frontier unreachable:', [f for f in fr if f not in seen][:60])
