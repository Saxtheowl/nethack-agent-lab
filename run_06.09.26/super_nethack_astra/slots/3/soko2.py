#!/usr/bin/env python3
import sys, heapq, itertools, time
from collections import deque
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from soko import parse, reach, D
from greedy import compress
def distmap(floor,holes):
    # reverse push distance: boulder at s can be pushed to reach hole; pull from holes
    dist={hh:0 for hh in holes}; q=deque(holes)
    while q:
        c=q.popleft()
        for dx,dy in D.values():
            prev=(c[0]-dx,c[1]-dy); stand=(c[0]-2*dx,c[1]-2*dy)
            if prev in floor and stand in floor and prev not in dist:
                dist[prev]=dist[c]+1; q.append(prev)
    return dist
def solve(floor,boulders,holes,player,W=3,maxn=2000000):
    dist=distmap(floor,holes)
    def h(b,hs):
        if not hs: return 0
        ds=sorted(dist.get(x,999) for x in b)
        return sum(ds[:len(hs)])+len(hs)*2
    cnt=itertools.count()
    R=reach(player,floor,boulders,holes)
    pq=[(W*h(boulders,holes),0,next(cnt),boulders,holes,player,None)]
    parent={}
    seen={(boulders,holes,min(R)):0}
    n=0; t0=time.time()
    while pq:
        f,g,_,b,hs,pl,pa=heapq.heappop(pq)
        n+=1
        if n%50000==0: print('expanded',n,'g',g,'holes',len(hs),time.time()-t0,file=sys.stderr)
        if n>maxn: return None
        if not hs:
            # reconstruct
            path=[]; node=pa
            while node:
                path.append(node[0]); node=node[1]
            return path[::-1]
        R=reach(pl,floor,b,hs)
        for bx,by in b:
            for dn,(dx,dy) in D.items():
                stand=(bx-dx,by-dy); dest=(bx+dx,by+dy)
                if stand not in R or dest not in floor or dest in b: continue
                if dest not in hs and dest not in dist: continue  # dead square
                nb=set(b); nb.discard((bx,by)); nh=hs
                if dest in hs: nh=hs-{dest}
                else: nb.add(dest)
                if len(nb)<len(nh): continue
                nb=frozenset(nb); npl=(bx,by)
                R2=reach(npl,floor,nb,nh)
                k=(nb,nh,min(R2))
                if k in seen and seen[k]<=g+1: continue
                seen[k]=g+1
                heapq.heappush(pq,(g+1+W*h(nb,nh),g+1,next(cnt),nb,nh,npl,(((bx,by),dn),pa)))
    return None
if __name__=='__main__':
    lines=open(sys.argv[1]).read().split('\n')
    w,f,b,hs,p=parse(lines,int(sys.argv[2]),int(sys.argv[3]))
    W=float(sys.argv[4]) if len(sys.argv)>4 else 3
    sol=solve(f,b,hs,p,W)
    if sol is None: print('NO SOLUTION'); sys.exit()
    print(len(sol),'pushes')
    print(' '.join(compress(sol)))
