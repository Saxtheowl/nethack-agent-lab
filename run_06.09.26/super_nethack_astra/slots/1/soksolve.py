#!/usr/bin/env python3
"""Tiny Sokoban solver for a NetHack board given as text lines (# wall, . floor, 0 boulder, ^ hole, @ hero).
Output: list of pushes as (bx,by,dir) with dir in l r u d, in board coordinates + offset."""
import sys, heapq, itertools
from collections import deque
D = {'l':(-1,0),'r':(1,0),'u':(0,-1),'d':(0,1)}
def parse(lines, ox, oy):
    floor=set(); B=set(); H=set(); P=None
    for y,row in enumerate(lines):
        for x,c in enumerate(row):
            p=(x+ox,y+oy)
            if c in '.0^@<>': floor.add(p)
            if c=='0': B.add(p)
            if c=='^': H.add(p)
            if c=='@': P=p
    return floor,frozenset(B),frozenset(H),P
def reach(P, floor, B, H):
    seen={P}; q=deque([P])
    while q:
        x,y=q.popleft()
        for dx,dy in D.values():
            n=(x+dx,y+dy)
            if n in floor and n not in B and n not in H and n not in seen:
                seen.add(n); q.append(n)
    return seen
def solve(floor,B,H,P, goal_cells):
    # dead squares: floor cells (not holes) from which a boulder can never reach any hole
    # compute via reverse pulls
    live=set(H); q=deque(H)
    while q:
        c=q.popleft()
        for dx,dy in D.values():
            b=(c[0]-dx,c[1]-dy); pl=(c[0]-2*dx,c[1]-2*dy)
            if b in floor and pl in floor and b not in live:
                live.add(b); q.append(b)
    cnt=itertools.count()
    def h(B,H): return len(H)*10
    start=(B,H,min(reach(P,floor,B,H)))
    seen={start}
    pq=[(h(B,H),0,next(cnt),B,H,P,[])]
    while pq:
        f,g,_,B,H,P,path=heapq.heappop(pq)
        if not (H & goal_cells): return path
        R=reach(P,floor,B,H)
        usable=sum(1 for b in B if b in live)
        for b in B:
            for k,(dx,dy) in D.items():
                beh=(b[0]-dx,b[1]-dy); dst=(b[0]+dx,b[1]+dy)
                if beh not in R or dst not in floor or dst in B: continue
                nB=set(B); nB.discard(b); nH=set(H)
                if dst in H: nH.discard(dst)
                else:
                    nB.add(dst)
                nB=frozenset(nB); nH=frozenset(nH)
                if sum(1 for x in nB if x in live) < len(nH & goal_cells): continue
                key=(nB,nH,min(reach(b,floor,nB,nH)))
                if key in seen: continue
                seen.add(key)
                heapq.heappush(pq,(g+1+h(nB,nH),g+1,next(cnt),nB,nH,b,path+[(b[0],b[1],k)]))
    return None
if __name__=='__main__':
    lines=open(sys.argv[1]).read().split('\n')
    ox,oy=int(sys.argv[2]),int(sys.argv[3])
    floor,B,H,P=parse(lines,ox,oy)
    sol=solve(floor,B,H,P,set(H))
    if sol is None: print('NO SOLUTION'); sys.exit(1)
    # compress consecutive pushes of the same boulder
    out=[]; 
    for x,y,k in sol:
        if out and out[-1][3]==(x,y):
            out[-1][2]+=k; dx,dy=D[k]; out[-1][3]=(x+dx,y+dy)
        else:
            dx,dy=D[k]; out.append([x,y,k,(x+dx,y+dy)])
    for x,y,ks,_ in out: print(x,y,ks)
