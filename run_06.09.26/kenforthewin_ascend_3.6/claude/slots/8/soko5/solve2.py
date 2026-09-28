#!/usr/bin/env python3
"""Greedy best-first Sokoban solver for NetHack Sokoban.
Map: # wall, . floor, 0 boulder, @ player, S = sink (hole row entrance, capacity N given as argv[2]),
^ = single hole. Orthogonal moves only. Prints pushes as 'x y dir' in MAP coords."""
import sys, heapq
from collections import deque
lines=[l.rstrip('\n') for l in open(sys.argv[1]) if l.strip('\n')!='']
cap=int(sys.argv[2]) if len(sys.argv)>2 else 0
W=max(len(l) for l in lines); H=len(lines); g=[l.ljust(W) for l in lines]
walls=set(); holes=set(); B=set(); player=None; sink=None
for y in range(H):
    for x in range(W):
        c=g[y][x]
        if c in '# ': walls.add((x,y))
        elif c=='^': holes.add((x,y))
        elif c=='0': B.add((x,y))
        elif c=='@': player=(x,y)
        elif c=='S': sink=(x,y)
D={'l':(-1,0),'r':(1,0),'u':(0,-1),'d':(0,1)}
floor=set((x,y) for y in range(H) for x in range(W) if (x,y) not in walls)
targets=set(holes)|({sink} if sink else set())
# push distance from each cell to nearest target (ignoring other boulders)
dist={t:0 for t in targets}; q=deque(targets)
while q:
    n=q.popleft()
    for dx,dy in D.values():
        c=(n[0]-dx,n[1]-dy); pl=(c[0]-dx,c[1]-dy)
        if c in floor and pl in floor and c not in dist and c not in targets:
            dist[c]=dist[n]+1; q.append(c)
def reach(p,bs,hs):
    seen={p}; q=deque([p])
    while q:
        x,y=q.popleft()
        for dx,dy in D.values():
            n=(x+dx,y+dy)
            if n in seen or n not in floor or n in bs or n in hs or n==sink: continue
            seen.add(n); q.append(n)
    return seen
def need(hs,c): return len(hs)+c
def hval(bs,hs,c):
    ds=sorted(dist.get(b,999) for b in bs)
    k=need(hs,c)
    return 100*k + sum(ds[:max(k,0)])
start=(frozenset(B),frozenset(holes),cap)
r0=reach(player,start[0],start[1]); k0=min(r0)
parent={(start,k0):None}
pq=[(hval(*start),0,start,player)]; cnt=0
while pq:
    f,_,st,p=heapq.heappop(pq)
    bs,hs,c=st
    r=reach(p,bs,hs); k=min(r)
    if need(hs,c)==0:
        out=[]; key=(st,k)
        while parent[key] is not None:
            key,push=parent[key]; out.append(push)
        out.reverse(); print(len(out),'pushes', cnt,'nodes')
        for x,y,d in out: print(x,y,d)
        sys.exit(0)
    for b in bs:
        for dn,(dx,dy) in D.items():
            pp=(b[0]-dx,b[1]-dy); t=(b[0]+dx,b[1]+dy)
            if pp not in r: continue
            if t not in dist or t in bs: continue
            nb=set(bs); nb.discard(b); nh=set(hs); nc=c
            if t in hs: nh.discard(t)
            elif t==sink:
                if nc<=0: continue
                nc-=1
            else: nb.add(t)
            if len(nb)<need(nh,nc): continue
            ns=(frozenset(nb),frozenset(nh),nc)
            nk=min(reach(b,ns[0],ns[1]))
            if (ns,nk) in parent: continue
            parent[(ns,nk)]=((st,k),(b[0],b[1],dn))
            cnt+=1
            if cnt%20000==0: print('nodes',cnt,'best need',need(nh,nc),'f',f,flush=True)
            heapq.heappush(pq,(hval(*ns),cnt,ns,b))
print('no solution',cnt)
