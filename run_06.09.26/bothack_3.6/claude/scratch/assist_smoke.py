import sys, shutil
sys.path.insert(0, '.')
from nhbot.engine import Engine, read_xlogfile
def run(d, script, **kw):
    shutil.rmtree(d, ignore_errors=True)
    eng = Engine(d, trace=open(d+'.trace','w'), **kw).start()
    req = eng.next_request(); steps = 0
    while req is not None and steps < 200:
        steps += 1
        msgs = req.messages()
        if msgs or req.kind not in ('cmd',): print("  ", req.kind, repr(req.query or req.prompt or req.goal), msgs[:4])
        if not script:
            eng.escape() if req.kind != 'cmd' else eng.key('#') ; 
            if req.kind == 'ext': pass
            if req.kind == 'cmd': pass
            req = eng.next_request(); 
            if req and req.kind == 'ext': eng.ext('quit'); req = eng.next_request()
            while req is not None:
                if req.kind == 'yn': eng.yn('y')
                else: eng.escape()
                req = eng.next_request()
            break
        kind, val = script.pop(0)
        getattr(eng, kind)(*val)
        req = eng.next_request()
    return eng
e = run('scratch/g2', [('key', ['i'])], seed=7)
print("kit/none inv:", e.inventory)
e = run('scratch/g3', [('key',[chr(23)]), ('line',['wand of death']), ('key',['z']), ('yn',['e']), ('yn',['.']), ('key',['s']), ('key',[chr(23)]), ('line',['wand of death']), ('key',['z']), ('yn',['f']), ('yn',['.']), ('key', ['s'])],
        seed=7, wizard=True, assists={'NH_ASSIST_INVINCIBLE':1, 'NH_ASSIST_KIT':'config/kit-test.txt'})
print("assists:", e.assist_events)
print("status:", e.status['hp'], e.status['ac'], "inv:", e.inventory)
print("verdict:", e.verdict)
print("xlog:", read_xlogfile('scratch/g3'))
e.stop()
