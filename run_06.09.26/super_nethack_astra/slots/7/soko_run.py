#!/usr/bin/env python3
"""soko_run.py PLANFILE STAGE OX OY : execute one stage of the plan via scripts/sokoban.py --execute.
Groups consecutive pushes of the same boulder. Map->screen offset OX,OY."""
import sys, subprocess, os, json, re
plan, stage, ox, oy = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
lines=[l for l in open(plan) if l.startswith('# pit')]
toks=lines[stage].split(':',1)[1].split()
pushes=[]
for t in toks:
    m=re.match(r'(\d+),(\d+)([lrud])',t); pushes.append((int(m[1]),int(m[2]),m[3]))
D={'l':(-1,0),'r':(1,0),'u':(0,-1),'d':(0,1)}
groups=[]
for x,y,d in pushes:
    if groups:
        gx,gy,ds=groups[-1]; cx,cy=gx,gy
        for dd in ds: cx+=D[dd][0]; cy+=D[dd][1]
        if (cx,cy)==(x,y): groups[-1]=(gx,gy,ds+d); continue
    groups.append((x,y,d))
env=dict(os.environ,NH_SLOT='7')
for gx,gy,ds in groups:
    cmd=['python3','scripts/sokoban.py',str(gx+ox),str(gy+oy),ds,'--execute','--max-steps','50']
    r=subprocess.run(cmd,capture_output=True,text=True,env=env)
    out=(r.stdout+r.stderr).strip()
    print(f'{gx+ox},{gy+oy} {ds}:', out[-300:])
    if r.returncode!=0 or 'error' in out.lower() or 'stop' in out.lower():
        print('HALT'); sys.exit(1)
