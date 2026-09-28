#!/usr/bin/env python3
"""Sokoban solver (NetHack rules: holes '^' swallow one boulder and become floor;
player cannot step on unfilled holes; orthogonal moves only; stairs not pushable onto).
Usage: solve.py mapfile  (map uses # walls, . floor, 0 boulder, ^ hole, @ player, < > stairs)
Outputs list of pushes: (bx,by,dir) in map coords, plus player path is left to the executor."""
import sys, heapq
from collections import deque
lines=[l.rstrip('\n') for l in open(sys.argv[1])]
W=max(len(l) for l in lines); H=len(lines)
g=[l.ljust(W) for l in lines]
walls=set(); holes=set(); boulders=set(); stairs=set(); player=None
for y in range(H):
    for x in range(W):
        c=g[y][x]
        if c in '#-| ' : walls.add((x,y))
        elif c=='^': holes.add((x,y))
        elif c=='0': boulders.add((x,y))
        elif c=='@': player=(x,y)
        elif c in '<>': stairs.add((x,y))
D={'l':(-1,0),'r':(1,0),'u':(0,-1),'d':(0,1)}
def reach(p,bs,hs):
    seen={p}; q=deque([p])
    while q:
        x,y=q.popleft()
        for dx,dy in D.values():
            n=(x+dx,y+dy)
            if n in seen or n in walls or n in bs or n in hs: continue
            if not (0<=n[0]<W and 0<=n[1]<H): continue
            seen.add(n); q.append(n)
    return seen
def canon(p,bs,hs):
    r=reach(p,bs,hs); return min(r), r
start_b=frozenset(boulders); start_h=frozenset(holes)
key0,_=canon(player,start_b,start_h)
def h(bs,hs): return len(hs)
floor=set((x,y) for y in range(H) for x in range(W) if (x,y) not in walls)
live=set(holes); q=deque(holes)
while q:
    n=q.popleft()
    for dx,dy in D.values():
        c=(n[0]-dx,n[1]-dy); pl=(c[0]-dx,c[1]-dy)
        if c in floor and pl in floor and c not in live and c not in stairs:
            live.add(c); q.append(c)

start=(start_b,start_h,key0)
seen={ (start_b,start_h,key0): None }
pq=[(len(start_h),0,0,start_b,start_h,player)]
cnt=0; parent={}
parent[(start_b,start_h,key0)]=None
while pq:
    f,gc,_,bs,hs,p=heapq.heappop(pq)
    k,r=canon(p,bs,hs)
    if not hs:
        # reconstruct
        out=[]; st=(bs,hs,k)
        while parent[st] is not None:
            prev,push=parent[st]; out.append(push); st=prev
        out.reverse(); print(len(out),'pushes'); 
        for b in out: print(*b)
        sys.exit(0)
    for b in bs:
        for dn,(dx,dy) in D.items():
            pp=(b[0]-dx,b[1]-dy); t=(b[0]+dx,b[1]+dy)
            if pp not in r: continue
            if t not in live or t in bs or t in stairs or not (0<=t[0]<W and 0<=t[1]<H): continue
            nb=set(bs); nb.discard(b); nh=set(hs)
            if t in hs: nh.discard(t)
            else: nb.add(t)
            nb=frozenset(nb); nh=frozenset(nh)
            if len(nb)<len(nh): continue
            np_=b
            nk,_=canon(np_,nb,nh)
            st=(nb,nh,nk)
            if st in parent: continue
            parent[st]=((bs,hs,k),(b[0],b[1],dn))
            cnt+=1
            heapq.heappush(pq,(gc+1+6*len(nh),gc+1,cnt,nb,nh,np_))
print('no solution', cnt)
