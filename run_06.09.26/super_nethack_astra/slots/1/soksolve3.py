#!/usr/bin/env python3
"""Stage solver with backtracking: fill holes in the given order; each stage yields up to K alternative results."""
import sys, heapq, itertools, time
from soksolve import parse, reach, D
from collections import deque
K=int(__import__('os').environ.get('K','6')); MAXN=int(__import__('os').environ.get('MAXN','60000'))
def live_cells(floor,H):
    live=set(H); q=deque(H)
    while q:
        c=q.popleft()
        for dx,dy in D.values():
            b=(c[0]-dx,c[1]-dy); pl=(c[0]-2*dx,c[1]-2*dy)
            if b in floor and pl in floor and b not in live: live.add(b); q.append(b)
    return live
def stage(floor,live,B,H,P,target):
    def hh(B): return min(abs(b[0]-target[0])+abs(b[1]-target[1]) for b in B)
    cnt=itertools.count(); seen=set(); results=set(); n=0
    pq=[(hh(B),0,next(cnt),B,H,P,[])]
    while pq and n<MAXN:
        f,g,_,B1,H1,P1,path=heapq.heappop(pq); n+=1
        if target not in H1:
            k=(B1,min(reach(P1,floor,B1,H1)))
            if k not in results:
                results.add(k); yield B1,H1,P1,path
                if len(results)>=K: return
            continue
        R=reach(P1,floor,B1,H1)
        for b in B1:
            for kk,(dx,dy) in D.items():
                beh=(b[0]-dx,b[1]-dy); dst=(b[0]+dx,b[1]+dy)
                if beh not in R or dst not in floor or dst in B1: continue
                if dst in H1 and dst!=target: continue
                if dst not in H1 and dst not in live: continue
                nB=set(B1); nB.discard(b); nH=set(H1)
                if dst in H1: nH.discard(dst)
                else: nB.add(dst)
                nB=frozenset(nB); nH=frozenset(nH)
                key=(nB,min(reach(b,floor,nB,nH)))
                if key in seen: continue
                seen.add(key)
                heapq.heappush(pq,(g+1+(hh(nB) if nB and target in nH else 0),g+1,next(cnt),nB,nH,b,path+[(b[0],b[1],kk)]))
def dfs(floor,live,B,H,P,order,acc,t0):
    if not order: return acc
    if time.time()-t0>float(__import__('os').environ.get('TLIM','500')): return None
    for B2,H2,P2,path in stage(floor,live,B,H,P,order[0]):
        if len(B2) < len(order)-1: continue
        r=dfs(floor,live,B2,H2,P2,order[1:],acc+[(order[0],path)],t0)
        if r: return r
    print('backtrack from',order[0],file=sys.stderr,flush=True)
    return None
lines=open(sys.argv[1]).read().split('\n'); ox,oy=int(sys.argv[2]),int(sys.argv[3])
floor,B,H,P=parse(lines,ox,oy)
order=[tuple(map(int,t.split(','))) for t in sys.argv[4:]]
live=live_cells(floor,H)
res=dfs(floor,live,B,H,P,order,[],time.time())
if not res: print('NO SOLUTION'); sys.exit(1)
for t,path in res:
    out=[]
    for x,y,k in path:
        dx,dy=D[k]
        if out and out[-1][3]==(x,y): out[-1][2]+=k; out[-1][3]=(x+dx,y+dy)
        else: out.append([x,y,k,(x+dx,y+dy)])
    print('hole',t,' '.join(f'{x},{y}:{k}' for x,y,k,_ in out))
