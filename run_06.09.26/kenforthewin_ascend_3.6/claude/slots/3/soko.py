#!/usr/bin/env python3
# Sokoban solver: map text with '#'=wall, '.'=floor, '0'=boulder, '^'=hole, '@'=player. Output push list.
import sys, heapq, itertools
from collections import deque
def parse(lines, ox, oy):
    walls=set(); boulders=set(); holes=set(); player=None; floor=set()
    for r,line in enumerate(lines):
        for c,ch in enumerate(line):
            p=(c+ox,r+oy)
            if ch in '#': walls.add(p); continue
            if ch==' ': walls.add(p); continue
            floor.add(p)
            if ch=='0': boulders.add(p)
            elif ch=='^': holes.add(p)
            elif ch=='@': player=p
    return walls,floor,frozenset(boulders),frozenset(holes),player
D={'u':(0,-1),'d':(0,1),'l':(-1,0),'r':(1,0)}
N8=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
def reach(start,floor,boulders,holes):
    # player can move 8-dir, not into boulder/hole/wall, diagonal blocked if both orthogonals bad (wall or boulder)
    seen={start}; q=deque([start])
    def bad(p): return p not in floor or p in boulders
    while q:
        x,y=q.popleft()
        for dx,dy in N8:
            n=(x+dx,y+dy)
            if n in seen or n not in floor or n in boulders or n in holes: continue
            if dx and dy and bad((x+dx,y)) and bad((x,y+dy)): continue
            seen.add(n); q.append(n)
    return seen
def solve(floor,boulders,holes,player,maxn=400000):
    cnt=itertools.count()
    def h(b,hs):
        t=len(hs)*30
        for hx,hy in hs:
            t+=min(abs(hx-x)+abs(hy-y) for x,y in b) if b else 99
        return t
    start=(boulders,holes,player)
    R=reach(player,floor,boulders,holes)
    key=(boulders,holes,min(R))
    pq=[(h(boulders,holes),0,next(cnt),boulders,holes,player,[])]
    seen={key:0}
    n=0
    while pq:
        f,g,_,b,hs,pl,path=heapq.heappop(pq)
        n+=1
        if n>maxn: return None
        if not hs: return path
        R=reach(pl,floor,b,hs)
        for bx,by in b:
            for dn,(dx,dy) in D.items():
                stand=(bx-dx,by-dy); dest=(bx+dx,by+dy)
                if stand not in R: continue
                if dest not in floor or dest in b: continue
                nb=set(b); nb.discard((bx,by)); nh=hs
                if dest in hs: nh=hs-{dest}
                else: nb.add(dest)
                nb=frozenset(nb); npl=(bx,by)
                R2=reach(npl,floor,nb,nh)
                k=(nb,nh,min(R2))
                if k in seen and seen[k]<=g+1: continue
                seen[k]=g+1
                heapq.heappush(pq,(0.2*(g+1)+h(nb,nh),g+1,next(cnt),nb,nh,npl,path+[((bx,by),dn)]))
    return None
if __name__=='__main__':
    lines=open(sys.argv[1]).read().split('\n')
    ox,oy=int(sys.argv[2]),int(sys.argv[3])
    w,f,b,hs,p=parse(lines,ox,oy)
    sol=solve(f,b,hs,p)
    print(sol)
