import sys, shutil, hashlib
sys.path.insert(0, '.')
from nhbot.engine import Engine, read_xlogfile
def game(d, seed, moves):
    shutil.rmtree(d, ignore_errors=True)
    eng = Engine(d, seed=seed, assists={'NH_ASSIST_KIT':'config/kit-test.txt','NH_ASSIST_NOSTARVE':1}).start()
    req = eng.next_request(); keys = list(moves)
    maps = []
    while req is not None:
        if req.kind == 'cmd':
            if keys: eng.key(keys.pop(0))
            else: eng.key('#')
        elif req.kind == 'ext': eng.ext('quit')
        elif req.kind == 'yn': eng.yn('y')
        else: eng.escape()
        req = eng.next_request()
        if req: maps.append("".join(eng.screen_lines()))
    eng.stop()
    return eng, hashlib.md5("".join(maps).encode()).hexdigest()
a, ha = game('scratch/s1', 1234, "llllhhhhjjjjkkkk"*3)
b, hb = game('scratch/s2', 1234, "llllhhhhjjjjkkkk"*3)
c, hc = game('scratch/s3', 999, "llllhhhhjjjjkkkk"*3)
print("same seed identical:", ha == hb, " different seed differs:", ha != hc)
print("verdict:", a.verdict)
print("assist:", a.assist_events)
print("inv:", a.inventory[:6])
print("xlog:", read_xlogfile('scratch/s1'))
print("bye:", a.bye and a.bye.get('msg'), "rc", a.returncode)
