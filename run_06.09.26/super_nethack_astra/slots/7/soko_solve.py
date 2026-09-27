#!/usr/bin/env python3
"""Sokoban solver for NetHack levels (4-dir player moves, pits swallow boulders).
Usage: soko_solve.py LEVEL  -> prints push list as (boulder_x,boulder_y,dir) in MAP coords,
stage by stage (pits in given order)."""
import sys, heapq, itertools
from collections import deque

LEVELS = {
 'soko4-1': dict(map=[
"------  ----- ",
"|....|  |...| ",
"|....----...| ",
"|...........| ",
"|..|-|.|-|..| ",
"---------|.---",
"|......|.....|",
"|..----|.....|",
"--.|   |.....|",
" |.|---|.....|",
" |...........|",
" |..|---------",
" ----         "],
  start=(6,4),
  boulders=[(2,2),(2,3),(10,2),(9,3),(10,4),(8,7),(9,8),(9,9),(8,10),(10,10)],
  pits=[(7,10),(6,10),(5,10),(4,10),(2,9),(2,8),(3,6),(4,6),(5,6)]),
}
D = {'l':(-1,0),'r':(1,0),'u':(0,-1),'d':(0,1)}

def solve(name):
    L = LEVELS[name]
    grid = L['map']
    H = len(grid); W = max(len(r) for r in grid)
    def floor(x,y):
        return 0<=y<H and 0<=x<len(grid[y]) and grid[y][x]=='.'
    pits_all = L['pits']
    # dead cells: corners (two orthogonal walls) that are not pits
    def dead(x,y,pits):
        if (x,y) in pits: return False
        wl = [not floor(x+dx,y+dy) for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]]
        return (wl[0] or wl[1]) and (wl[2] or wl[3])
    def reach(p, B):
        seen={p}; q=deque([p])
        while q:
            x,y=q.popleft()
            for dx,dy in D.values():
                n=(x+dx,y+dy)
                if n not in seen and floor(*n) and n not in B and n not in pitsset_cur[0]:
                    seen.add(n); q.append(n)
        return seen
    pitsset_cur=[set()]
    B0=frozenset(L['boulders']); P0=frozenset(pits_all)
    start=L['start']
    # A*: state (B,P,canon) ; cost = pushes ; h = len(P)
    def canon(p,B,P):
        pitsset_cur[0]=P
        r=reach(p,B)
        return min(r), r
    c0,_=canon(start,B0,P0)
    cnt=itertools.count()
    openh=[(len(P0)*3,0,next(cnt),B0,P0,start,[])]
    seen={}
    while openh:
        f,g,_,B,P,p,path=heapq.heappop(openh)
        if not P: return path
        pitsset_cur[0]=P
        r=reach(p,B)
        key=(B,P,min(r))
        if key in seen and seen[key]<=g: continue
        seen[key]=g
        for b in B:
            for dn,(dx,dy) in D.items():
                stand=(b[0]-dx,b[1]-dy); to=(b[0]+dx,b[1]+dy)
                if stand not in r: continue
                if not floor(*to) or to in B: continue
                if to in P:
                    nB=B-{b}; nP=P-{to}
                else:
                    if dead(*to,P): continue
                    nB=(B-{b})|{to}; nP=P
                    # must not exceed spare count: boulders stuck count check skipped
                if len(nB) < len(nP): continue
                heapq.heappush(openh,(g+1+len(nP)*3,g+1,next(cnt),frozenset(nB),frozenset(nP),b,path+[(b[0],b[1],dn)]))
    return None

if __name__=='__main__':
    sol=solve(sys.argv[1])
    print(len(sol) if sol else 'NO SOLUTION')
    if sol: print(' '.join(f'{x},{y}{d}' for x,y,d in sol))
