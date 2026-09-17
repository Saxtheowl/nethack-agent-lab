import sys, json, os, shutil
sys.path.insert(0, '.')
from nhbot.engine import Engine
d = 'scratch/g1'; shutil.rmtree(d, ignore_errors=True)
eng = Engine(d, seed=42, trace=open('scratch/g1.trace','w')).start()
req = eng.next_request()
print("hello", eng.hello and eng.hello['version'], len(eng.hello['mons']))
keys = list("ssss") + ['i', 'e', 'x']
n = 0
while req is not None and n < 40:
    n += 1
    print(n, req.kind, repr(req.query or req.prompt), req.messages()[:3], [e for e in req.events if e[0] != 'msg'][:2])
    if req.kind in ('cmd', 'key'):
        if keys: eng.key(keys.pop(0))
        else: eng.key('S')  # save prompt
    elif req.kind == 'yn':
        eng.yn('y')
    elif req.kind == 'menu':
        print("   items:", req.items[:5]); eng.escape()
    elif req.kind == 'line':
        eng.escape()
    else:
        eng.escape()
    req = eng.next_request()
print("\n".join(eng.screen_lines()))
print(eng.status); print(eng.inventory); print(eng.priv)
print("verdict", eng.verdict, "bye", eng.bye and eng.bye.get('msg'))
eng.stop(); print("rc", eng.returncode); print(open(d+'/engine.stderr').read()[-500:])
