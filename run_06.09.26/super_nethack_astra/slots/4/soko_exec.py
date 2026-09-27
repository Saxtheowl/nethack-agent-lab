#!/usr/bin/env python3
"""Execute a solver plan step by step with verification.
Usage: soko_exec.py MAPFILE OX OY NEED [--dry] [--max N]
Map coords (col,row) -> screen (col+OX,row+OY). Re-solves from the map file (which must reflect the current board)."""
import sys, re, subprocess, time
sys.path.insert(0, '/home/roro/work/projects/super_nethack/run_06.09.26/super_nethack_astra/slots/4')
import soko_solve as s
mapf, OX, OY, need = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
dry = '--dry' in sys.argv
mx = int(sys.argv[sys.argv.index('--max')+1]) if '--max' in sys.argv else 999
txt = open(mapf).read().rstrip('\n')
import json, os
plan = json.load(open(sys.argv[5])) if len(sys.argv)>5 and sys.argv[5].endswith('.json') else (s.solve_fill(txt, need) if need > 0 else s.solve(txt))
if plan is None: print('NO PLAN'); sys.exit(1)
print('plan', len(plan), 'steps')
ROOT='/home/roro/work/projects/super_nethack/run_06.09.26/super_nethack_astra'
def screen():
    return subprocess.run(['python3','scripts/session.py','screen','--compact'],capture_output=True,text=True,cwd=ROOT,env={'NH_SLOT':'4','PATH':'/usr/bin:/bin'}).stdout
def send(k):
    return subprocess.run(['python3','scripts/session.py','keys','--compact','--raw',k],capture_output=True,text=True,cwd=ROOT,env={'NH_SLOT':'4','PATH':'/usr/bin:/bin'}).stdout
def cursor(o):
    m=re.search(r'Terminal cursor[^:]*: (\d+),(\d+)',o); return (int(m[1]),int(m[2]))
def hp(o):
    m=re.search(r'HP:(\d+)\((\d+)\)',o); return int(m[1]),int(m[2])
off={'8':(0,-1),'2':(0,1),'4':(-1,0),'6':(1,0)}
o=screen(); pos=cursor(o); hp0=hp(o)[0]
start=int(sys.argv[sys.argv.index('--from')+1]) if '--from' in sys.argv else 0
done=start
for st in plan[start:]:
    if st[0]=='walk': keys=st[1]; b=None
    else: keys,b,d=st
    if dry: print(st[1:] if st[0]!='walk' else 'walk'); continue
    for i,k in enumerate(keys):
        exp=(pos[0]+off[k][0],pos[1]+off[k][1])
        o=send(k); time.sleep(0.15)
        np=cursor(o)
        if np!=exp:
            time.sleep(0.5); o=screen(); np=cursor(o)
        if np!=exp:
            print('STOP: expected',exp,'got',np, 'at step',done, 'key',i,k)
            print('\n'.join(l for l in o.splitlines() if re.match(r'^0[1-7] ',l))[-400:])
            sys.exit(2)
        h=hp(o)[0]
        if h<hp0: print('STOP: HP loss',hp0,'->',h); sys.exit(3)
        pos=np
    done+=1
    if st[0]!='walk': print('push',done,'boulder',b,'dir',d,'ok; hero',pos)
    if done-start>=mx: print('max reached'); break
print('DONE', done)
