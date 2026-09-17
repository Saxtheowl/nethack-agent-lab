import sys, json
sys.path.insert(0,'.')
from nhbot.engine import Engine
from pybothack.nhbridge import GlyphRenderer
# replay: run the same seed with rungame protocol trace is heavy; instead parse hello + map from a protocol trace file
tr = sys.argv[1]; X=int(sys.argv[2]); Y=int(sys.argv[3])
hello=None; last=None
for line in open(tr):
    if line.startswith('>'): continue
    m=json.loads(line)
    if m.get('t')=='hello': hello=m
    for c in m.get('map') or []:
        if c[0]==X and c[1]==Y: last=c
r=GlyphRenderer(hello)
print("cell", last, "render", r.render(last[2], last[3], last[4], last[5]))
print("boulder idx", r.boulder, "statue idx", r.statue, "off", hello['off']['obj'])
g=last[2]; print("obj index", g-hello['off']['obj'], hello['objs'][g-hello['off']['obj']] if 0<=g-hello['off']['obj']<len(hello['objs']) else None)
