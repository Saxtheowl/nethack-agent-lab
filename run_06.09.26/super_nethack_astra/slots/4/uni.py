#!/usr/bin/env python3
"""uni.py n: chase glyph u: each turn, if adjacent -> F attack; else step toward it. Stops HP<55%."""
import re, subprocess, sys, os
R = os.path.dirname(os.path.abspath(__file__)) + '/../..'
os.environ['NH_SLOT'] = '4'
def sess(*a): return subprocess.run(['python3','scripts/session.py',*a],cwd=R,capture_output=True,text=True).stdout
D={(-1,-1):'7',(0,-1):'8',(1,-1):'9',(-1,0):'4',(1,0):'6',(-1,1):'1',(0,1):'2',(1,1):'3'}
sg=lambda v:(v>0)-(v<0)
s=sess('screen','--compact')
for i in range(int(sys.argv[1])):
    h,mx=map(int,re.search(r'HP:(\d+)\((\d+)\)',s).groups())
    if h*100<mx*55: print('STOP HP'); break
    m=re.search(r'^Map features.*$',s,re.M).group(0)
    me=re.search(r' @@(\d+),(\d+)',m); hx,hy=int(me[1]),int(me[2])
    u=re.search(r' u@(\d+),(\d+)',m)
    if not u: print('no u'); break
    ux,uy=int(u[1]),int(u[2]); dx,dy=ux-hx,uy-hy
    if max(abs(dx),abs(dy))==1: k='F'+D[(dx,dy)]
    else: k=D[(sg(dx),sg(dy))]
    s=sess('keys','--compact','--raw',k)
    msg=[l[5:85].strip() for l in s.splitlines() if re.match(r'^0[1-7] ',l)]
    print(i,k,re.search(r'HP:\d+',s)[0],msg[-1] if msg else '')
    if re.search(r'kill the black unicorn|--More--|\[yn',msg[-1] if msg else ''): break
