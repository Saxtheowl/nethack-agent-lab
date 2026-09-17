import sys, random, shutil, logging
sys.path.insert(0,'.')
from nhbot.engine import Engine
from pybothack.bh36 import new_bh36
from pybothack.nhbridge import Bridge
from pybothack.handlers import register_handler
from pybothack.delegator import Handler
from pybothack.util import PRIORITY_TOP
from pybothack.dungeon import at_curlvl
logging.basicConfig(level=logging.ERROR)
d='scratch/door'; shutil.rmtree(d, ignore_errors=True)
eng = Engine(d, seed=102, assists={'NH_ASSIST_INVINCIBLE':1,'NH_ASSIST_NOSTARVE':1,'NH_ASSIST_KIT':'config/kit-default.txt'}).start()
bh = new_bh36({'bot':'mainbot'}, rng=random.Random(102))
br = Bridge(bh, eng, None)
acts=[]
register_handler(bh, PRIORITY_TOP-1, Handler(action_chosen=lambda a: (br.on_action(a), acts.append(a.get('type')))))
orig_message = None
def msg(text):
    g=bh.game.deref()
    if 'locked' in text:
        print("MSG", text, "player", g['player'].get('x'), g['player'].get('y'), "tile", at_curlvl(g, 33, 4).get('feature'))
register_handler(bh, PRIORITY_TOP-1, Handler(message=msg))
class Sup:
    n=0
    def on_request(s, b, req):
        s.n+=1
        g=bh.game.deref()
        if eng.status.get('turn',0)>=79:
            print(s.n, req.kind, "T", eng.status.get('turn'), "tile(33,4)", at_curlvl(g,33,4).get('feature'), "last", acts[-1:] )
        if s.n>235: raise KeyboardInterrupt
try: br.run(Sup())
except KeyboardInterrupt: pass
eng.stop()
