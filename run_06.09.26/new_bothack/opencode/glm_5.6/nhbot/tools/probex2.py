import os
import sys
import time

sys.path.insert(0, os.getcwd())
from nhlight import session as sm
from nhlight import world as wl
from nhlight import dialogue as dl

run = "/tmp/opencode/probex2"
s = sm.Session(run, "probex2", seed=40056)
g = dl.Dialogue(s)
w = wl.World()
b = Brain(w, g)
s.start()
t0 = time.monotonic()
try:
    while time.monotonic() - t0 < 6:
        s.read(0.5)
except Exception:
    pass
g.settle(quiet=0.3, cap=2.0)
kind, detail = dl.classify_frame(s)
lines, cells, cx, cy = s.terminal.snapshot()
w.observe(lines, cx, cy)
b.lines = lines
lvl = w.level()
front = lvl.explore_targets((cx, cy), b.blocked_cells())
act = b.choose()
print("hostiles", [(m.glyph, m.pos) for m in b.hostiles()])
print("frontier", len(front), [(t[0], t[1]) for t in front[:4]])
print("act", act.kind, repr(act.keys))
