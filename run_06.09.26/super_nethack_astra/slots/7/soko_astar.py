#!/usr/bin/env python3
"""Weighted A* on the whole Sokoban level (holes/pits filled in any order), 4-dir player.
h = sum of the R smallest push-distances (boulder -> nearest remaining pit). Prints MAP-coord pushes."""
import sys, heapq, itertools
from collections import deque
sys.path.insert(0, __file__.rsplit('/',1)[0])
from soko_solve import LEVELS, D
name=sys.argv[1]; W=float(sys.argv[2]) if len(sys.argv)>2 else 2.0; MAXS=int(sys.argv[3]) if len(sys.argv)>3 else 5000000
L=LEVELS[name]; grid=L['map']; H=len(grid)
def floor(x,y): return 0<=y<H and 0<=x<len(grid[y]) and grid[y][x]=='.'
cells=[(x,y) for y in range(H) for x in range(len(grid[y])) if floor(x,y)]
def pdist(targets):
    d={t:0 for t in targets}; q=deque(targets)
    while q:
        c=q.popleft()
        for dx,dy in D.values():
            prev=(c[0]-dx,c[1]-dy); stand=(c[0]-2*dx,c[1]-2*dy)
            if prev not in d and floor(*prev) and floor(*stand):
                d[prev]=d[c]+1; q.append(prev)
    return d
DM={}
def dm(P):
    k=frozenset(P)
    if k not in DM: DM[k]=pdist(list(P))
    return DM[k]
def reach(p,B,P):
    s={p}; q=deque([p])
    while q:
        x,y=q.popleft()
        for dx,dy in D.values():
            n=(x+dx,y+dy)
            if n not in s and floor(*n) and n not in B and n not in P: s.add(n); q.append(n)
    return s
ENTRY=[min(L['pits'])]  # first hole in fill order (west-most / top-left)
def h(B,P):
    if not P: return 0
    d=dm(ENTRY); ds=sorted(d.get(b,10**6) for b in B)
    return sum(ds[:len(P)])
B0=frozenset(L['boulders']); P0=frozenset(L['pits'])
cnt=itertools.count()
op=[(W*h(B0,P0),0,next(cnt),B0,P0,L['start'],None)]
parent={}; seen=set(); n=0
while op:
    f,g,_,B,P,p,link=heapq.heappop(op)
    r=reach(p,B,P); key=(B,P,min(r))
    if key in seen: continue
    seen.add(key); parent[key]=link; n+=1
    if n%200000==0: print('expanded',n,'g',g,'pits',len(P),file=sys.stderr,flush=True)
    if n>MAXS: print('LIMIT'); sys.exit(1)
    if not P:
        path=[]; k=key
        while parent[k]: pk,push=parent[k]; path.append(push); k=pk
        path.reverse()
        print(len(path)); print(' '.join(f'{x},{y}{dd}' for x,y,dd in path)); sys.exit(0)
    d=dm(P)
    for bo in B:
        for dn,(dx,dy) in D.items():
            st=(bo[0]-dx,bo[1]-dy); to=(bo[0]+dx,bo[1]+dy)
            if st not in r or not floor(*to) or to in B: continue
            if to in P: nB=B-{bo}; nP=P-{to}
            else:
                if to not in d: continue
                nB=(B-{bo})|{to}; nP=P
            if len(nB)<len(nP): continue
            nb=frozenset(nB); npp=frozenset(nP)
            heapq.heappush(op,(g+1+W*h(nb,npp),g+1,next(cnt),nb,npp,bo,(key,(bo[0],bo[1],dn))))
print('NO SOLUTION')
