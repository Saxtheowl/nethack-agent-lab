import sys, shutil, json
sys.path.insert(0,'.')
from nhbot.engine import Engine
d='scratch/disco'; shutil.rmtree(d, ignore_errors=True)
eng = Engine(d, seed=101, assists={'NH_ASSIST_KIT':'config/kit-default.txt'}).start()
req = eng.next_request(); keys=['\\']
while req is not None:
    for e in req.events:
        if e[0] in ('text','menu_show'): print(json.dumps(e, indent=0)[:3000])
    if req.kind=='cmd' and keys: eng.key(keys.pop(0))
    elif req.kind=='cmd': break
    else: eng.escape()
    req=eng.next_request()
eng.stop()
