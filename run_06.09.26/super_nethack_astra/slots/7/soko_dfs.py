#!/usr/bin/env python3
"""Stage BFS + backtracking over up to K alternative stage results."""
import sys
from collections import deque
sys.path.insert(0, __file__.rsplit('/',1)[0])
from soko_solve import LEVELS, D
sys.setrecursionlimit(10000)
name=sys.argv[1]; K=int(sys.argv[2]) if len(sys.argv)>2 else 4; MAXS=int(sys.argv[3]) if len(sys.argv)>3 else 600000
L=LEVELS[name]; grid=L['map']; H=len(grid)
def floor(x,y): return 0<=y<H and 0<=x<len(grid[y]) and grid[y][x]=='.'
cells=[(x,y) for y in range(H) for x in range(len(grid[y])) if floor(x,y)]
PITS=L['pits']
live=set(PITS); ch=True
while ch:
    ch=False
    for c in cells:
        if c in live: continue
        for dx,dy in D.values():
            if floor(c[0]-dx,c[1]-dy) and (c[0]+dx,c[1]+dy) in live: live.add(c); ch=True; break
def reach(p,B,P):
    s={p}; q=deque([p])
    while q:
        x,y=q.popleft()
        for dx,dy in D.values():
            n=(x+dx,y+dy)
            if n not in s and floor(*n) and n not in B and n not in P: s.add(n); q.append(n)
    return s
import heapq, itertools
DIST={}
def pdist(target):
    if target in DIST: return DIST[target]
    d={target:0}; q=deque([target])
    while q:
        c=q.popleft()
        for dx,dy in D.values():
            prev=(c[0]-dx,c[1]-dy); stand=(c[0]-2*dx,c[1]-2*dy)
            if prev not in d and floor(*prev) and floor(*stand):
                d[prev]=d[c]+1; q.append(prev)
    DIST[target]=d; return d
CNT=itertools.count()
def stage(B,p,P,target):
    dm=pdist(target)
    def h(b): return min((dm.get(x,999) for x in b), default=999)
    q=[(h(B),0,next(CNT),B,p,())]; seen=set(); sols=[]; seenres=set(); n=0
    while q and len(sols)<K:
        _,g,_,b,pp,path=heapq.heappop(q); n+=1
        if n>MAXS: break
        r=reach(pp,b,P); key=(b,min(r))
        if key in seen: continue
        seen.add(key)
        for bo in b:
            for dn,(dx,dy) in D.items():
                st=(bo[0]-dx,bo[1]-dy); to=(bo[0]+dx,bo[1]+dy)
                if st not in r or not floor(*to) or to in b: continue
                np=path+((bo,dn),)
                if to==target:
                    nb=b-{bo}
                    k2=(nb,bo)
                    if k2 not in seenres:
                        seenres.add(k2); sols.append((nb,bo,np))
                    continue
                if to in P or to not in live: continue
                nb2=(b-{bo})|{to}
                heapq.heappush(q,(g+1+h(nb2),g+1,next(CNT),nb2,bo,np))
    return sols
def dfs(B,p,P,i,acc):
    if i==len(PITS): return acc
    P2=set(P)
    for nb,np_,path in stage(B,p,P,PITS[i]):
        livecount=sum(1 for b in nb if b in live)
        if livecount < len(PITS)-i-1: continue
        P3=set(P); P3.discard(PITS[i])
        print(f'depth {i} ok ({len(path)} pushes)', file=sys.stderr, flush=True)
        r=dfs(nb,np_,P3,i+1,acc+[(PITS[i],path)])
        if r: return r
    return None
res=dfs(frozenset(L['boulders']),L['start'],set(PITS),0,[])
if not res: print('NO SOLUTION'); sys.exit(1)
for t,path in res:
    print(f'# pit {t}: ' + ' '.join(f'{x},{y}{d}' for (x,y),d in path))
