import sys, shutil, logging, random, time, collections
sys.path.insert(0, '.')
from nhbot.engine import Engine
from pybothack.bh36 import new_bh36
from pybothack.nhbridge import Bridge
from pybothack.handlers import register_handler
from pybothack.delegator import Handler
from pybothack.util import PRIORITY_TOP
from pybothack.action import typekw

logging.basicConfig(level=logging.WARNING, filename='scratch/first_play.log', filemode='w',
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
MAXREQ = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
d = 'scratch/p1'; shutil.rmtree(d, ignore_errors=True)
eng = Engine(d, seed=seed, assists={'NH_ASSIST_INVINCIBLE':1,'NH_ASSIST_NOSTARVE':1}).start()
bh = new_bh36({'bot': 'mainbot'}, rng=random.Random(seed))
class Rec:
    def __init__(s): s.notes=collections.Counter(); s.acts=collections.Counter(); s.last=collections.deque(maxlen=40)
    def note(s, what, detail): s.notes[what]+=1; s.last.append(('NOTE', what, str(detail)[:150]))
    def answer(s, req, ans): s.last.append(('ANS', req.kind, (req.query or req.prompt or '')[:60], repr(ans)[:40]))
    def action(s, a): s.acts[typekw(a)]+=1; s.last.append(('ACT', typekw(a), str(a.get('reason'))[:80]))
rec = Rec()
br = Bridge(bh, eng, rec, nickname='Bot')
register_handler(bh, PRIORITY_TOP - 1, Handler(action_chosen=br.on_action))
class Sup:
    n = 0
    def on_request(s, bridge, req):
        s.n += 1
        if s.n >= MAXREQ: raise KeyboardInterrupt
t0=time.time()
try:
    br.run(Sup())
except KeyboardInterrupt:
    pass
dt=time.time()-t0
st = eng.status
print("requests", eng.nreq, "time %.1f" % dt, "turn", st.get('turn'), "dlvl", st.get('lvl'), "xl", st.get('xl'), "hp", st.get('hp'))
print("actions", rec.acts.most_common(20))
print("notes", rec.notes, "counters", br.counters)
print("assists", [a['kind'] for a in eng.assist_events])
for l in list(rec.last)[-25:]: print("  ", l)
print("\n".join(br.frame.lines))
eng.stop()
