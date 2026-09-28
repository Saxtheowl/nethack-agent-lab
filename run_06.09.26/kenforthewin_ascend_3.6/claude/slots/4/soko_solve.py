#!/usr/bin/env python3
"""Sokoban push solver (holes '^' swallow one boulder each and become floor).
Map text: '#'/'-'/'|' walls, '.' floor, '0' boulder, '^' hole, '@' hero, '<' goal (floor).
Player moves orthogonally only. Pushes orthogonal. Goal: hero can reach '<'.
Prints list of pushes as (boulder col,row, dir) and the full key path (4/6/8/2)."""
import sys, heapq, itertools
from collections import deque

def parse(txt):
    rows=txt.split('\n')
    W=max(len(r) for r in rows); H=len(rows)
    floor=set(); boulders=set(); holes=set(); hero=goal=None
    for y,r in enumerate(rows):
        for x,c in enumerate(r):
            if c in '.0^@<>?': floor.add((x,y))
            if c=='0': boulders.add((x,y))
            if c=='^': holes.add((x,y))
            if c=='@': hero=(x,y)
            if c=='<': goal=(x,y)
    return floor,frozenset(boulders),frozenset(holes),hero,goal

D={(0,-1):'8',(0,1):'2',(-1,0):'4',(1,0):'6'}

def reach(floor,boulders,holes,start):
    seen={start}; dq=deque([start]); par={start:None}
    while dq:
        p=dq.popleft()
        for d in D:
            q=(p[0]+d[0],p[1]+d[1])
            if q in floor and q not in boulders and q not in holes and q not in seen:
                seen.add(q); par[q]=(p,d); dq.append(q)
    return seen,par

def path(par,t):
    ks=[]
    while par[t]:
        p,d=par[t]; ks.append(D[d]); t=p
    return ''.join(reversed(ks))

def solve(txt, maxn=3000000):
    floor,B,Hs,hero,goal=parse(txt)
    def norm(B,Hs,hero):
        seen,_=reach(floor,B,Hs,hero)
        return min(seen),seen
    def h(B,Hs): return len(Hs)
    n0,_=norm(B,Hs,hero)
    start=(B,Hs,n0)
    cnt=itertools.count()
    pq=[(h(B,Hs),next(cnt),B,Hs,hero,[])]
    visited={(B,Hs,n0)}
    n=0
    while pq:
        f,_,B,Hs,pos,hist=heapq.heappop(pq)
        n+=1
        if n>maxn: return None
        seen,par=reach(floor,B,Hs,pos)
        if goal in seen: return hist+[('walk',path(par,goal))]
        for b in B:
            for d in D:
                src=(b[0]-d[0],b[1]-d[1]); dst=(b[0]+d[0],b[1]+d[1])
                if src not in seen or dst not in floor or dst in B: continue
                nB=set(B); nB.remove(b); nH=set(Hs)
                if dst in Hs: nH.remove(dst)
                else: nB.add(dst)
                nB=frozenset(nB); nH=frozenset(nH)
                # simple deadlock: boulder (not in hole) in a corner of walls
                if dst in nB:
                    x,y=dst
                    wall=lambda p: p not in floor
                    if (wall((x-1,y)) or wall((x+1,y))) and (wall((x,y-1)) or wall((x,y+1))):
                        # allow at most (len(B)-len(Hs)) dead boulders
                        pass
                npos=b
                k,_s=norm(nB,nH,npos)
                key=(nB,nH,k)
                if key in visited: continue
                visited.add(key)
                step=(path(par,src)+D[d], b, D[d])
                g=len(hist)+1
                heapq.heappush(pq,(g+2*len(nH),next(cnt),nB,nH,npos,hist+[step]))
    return None

if __name__=='__main__':
    txt=open(sys.argv[1]).read().rstrip('\n')
    sol=solve(txt)
    if sol is None: print('NO SOLUTION'); sys.exit(1)
    allk=''
    for s in sol:
        if s[0]=='walk': print('walk to goal:',s[1]); allk+=s[1]
        else: print('push boulder at %s dir %s  keys %s'%(s[1],s[2],s[0])); allk+=s[0]
    print('TOTAL', len(sol)-1, 'pushes')
    print('KEYS', allk)

def solve_fill(txt, need, maxn=2000000):
    """Find pushes that fill `need` holes (hero start '@'). Returns steps list."""
    floor,B,Hs,hero,goal=parse(txt)
    H0=len(Hs)
    cnt=itertools.count()
    seen0,_=reach(floor,B,Hs,hero)
    pq=[(0,next(cnt),B,Hs,hero,[])]
    visited={(B,Hs,min(seen0))}
    n=0
    while pq:
        f,_,B,Hs,pos,hist=heapq.heappop(pq)
        n+=1
        if n>maxn: return None
        if H0-len(Hs)>=need: return hist
        seen,par=reach(floor,B,Hs,pos)
        for b in B:
            for d in D:
                src=(b[0]-d[0],b[1]-d[1]); dst=(b[0]+d[0],b[1]+d[1])
                if src not in seen or dst not in floor or dst in B: continue
                nB=set(B); nB.remove(b); nH=set(Hs)
                if dst in Hs: nH.remove(dst)
                else: nB.add(dst)
                nB=frozenset(nB); nH=frozenset(nH)
                s2,_=reach(floor,nB,nH,b)
                key=(nB,nH,min(s2))
                if key in visited: continue
                visited.add(key)
                step=(path(par,src)+D[d], b, D[d])
                heapq.heappush(pq,(len(hist)+1+3*(need-(H0-len(nH))),next(cnt),nB,nH,b,hist+[step]))
    return None
