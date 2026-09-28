#!/usr/bin/env python3
# gold.py: travel to each visible $ (except AVOID) inside box x1 y1 x2 y2, pick up gold only.
import re, subprocess, sys, os
os.environ['NH_SLOT']='3'
ROOT='/home/roro/work/projects/super_nethack/run_06.09.26/kenforthewin_ascend_3.6/claude'
x1,y1,x2,y2=map(int,sys.argv[1:5])
avoid=set(tuple(map(int,a.split(','))) for a in os.environ.get('AVOID','').split() if a)
def S(*a): return subprocess.run(['python3',ROOT+'/scripts/session.py',*a],capture_output=True,text=True,cwd=ROOT).stdout
def T(x,y): return subprocess.run([ROOT+'/slots/3/t',str(x),str(y)],capture_output=True,text=True,cwd=ROOT).stdout
out=S('screen','--compact')
m=re.search(r'^Map features.*$',out,re.M).group(0)
golds=[(int(x),int(y)) for x,y in re.findall(r' \$@(\d+),(\d+)',m)]
golds=[g for g in golds if x1<=g[0]<=x2 and y1<=g[1]<=y2 and g not in avoid]
hp0=int(re.search(r'HP:(\d+)',out)[1])
for (x,y) in golds:
    T(x,y)
    out=S('screen','--compact')
    h=re.search(r' @@(\d+),(\d+)',out)
    hp=int(re.search(r'HP:(\d+)',out)[1])
    if hp<hp0-10: print('STOP hp',hp); break
    if not h or (int(h[1]),int(h[2]))!=(x,y): print('not at',x,y); continue
    r=S('keys',',','--settle','.4')
    if 'Pick up what' in r:
        S('keys','--raw','$','--settle','.3'); r=S('keys','--named','Enter','--settle','.4')
    mm=re.findall(r'^0[67] .*$',r,re.M)
    print(x,y,mm[-1][:70] if mm else '')
out=S('screen','--compact')
print(re.search(r'^34.*$',out,re.M).group(0))
