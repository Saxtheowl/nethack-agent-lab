#!/usr/bin/env python3
import sys, heapq, itertools
from soksolve import parse, reach, D
from collections import deque
def stage(floor,B,H,P,target,maxn=400000):
    live=set(H); q=deque(H)
    while q:
        c=q.popleft()
        for dx,dy in D.values():
            b=(c[0]-dx,c[1]-dy); pl=(c[0]-2*dx,c[1]-2*dy)
            if b in floor and pl in floor and b not in live: live.add(b); q.append(b)
    def hh(B): return min(abs(b[0]-target[0])+abs(b[1]-target[1]) for b in B)
    cnt=itertools.count(); seen=set()
    pq=[(hh(B),0,next(cnt),B,H,P,[])]
    n=0
    while pq and n<maxn:
        f,g,_,B,H,P,path=heapq.heappop(pq); n+=1
        if target not in H: return B,H,P,path
        R=reach(P,floor,B,H)
        for b in B:
            for k,(dx,dy) in D.items():
                beh=(b[0]-dx,b[1]-dy); dst=(b[0]+dx,b[1]+dy)
                if beh not in R or dst not in floor or dst in B: continue
                if dst in H and dst!=target: continue
                if dst not in H and dst not in live: continue
                nB=set(B); nB.discard(b); nH=set(H)
                if dst in H: nH.discard(dst)
                else: nB.add(dst)
                nB=frozenset(nB); nH=frozenset(nH)
                key=(nB,min(reach(b,floor,nB,nH)))
                if key in seen: continue
                seen.add(key)
                heapq.heappush(pq,(g+1+(hh(nB) if nB else 0),g+1,next(cnt),nB,nH,b,path+[(b[0],b[1],k)]))
    return None
lines=open(sys.argv[1]).read().split('\n'); ox,oy=int(sys.argv[2]),int(sys.argv[3])
floor,B,H,P=parse(lines,ox,oy)
order=[tuple(map(int,t.split(','))) for t in sys.argv[4:]]
allp=[]
for t in order:
    r=stage(floor,B,H,P,t)
    if r is None: print('FAIL at',t); break
    B,H,P,path=r
    out=[]
    for x,y,k in path:
        dx,dy=D[k]
        if out and out[-1][3]==(x,y): out[-1][2]+=k; out[-1][3]=(x+dx,y+dy)
        else: out.append([x,y,k,(x+dx,y+dy)])
    print('hole',t,' '.join(f'{x},{y}:{k}' for x,y,k,_ in out), flush=True)
