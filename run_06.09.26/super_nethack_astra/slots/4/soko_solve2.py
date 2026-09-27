import heapq, itertools, sys, json
from collections import deque
D={(0,-1):'8',(0,1):'2',(-1,0):'4',(1,0):'6'}
def parse(txt):
    floor=set(); B=set(); Hs=set(); hero=goal=None
    for y,r in enumerate(txt.split('\n')):
        for x,c in enumerate(r):
            if c in '.0^@<>': floor.add((x,y))
            if c=='0': B.add((x,y))
            if c=='^': Hs.add((x,y))
            if c=='@': hero=(x,y)
            if c=='<': goal=(x,y)
    return floor,frozenset(B),frozenset(Hs),hero,goal
def live_squares(floor,holes):
    # squares from which a boulder can be pushed (ignoring other boulders) into some hole: reverse pulls
    live=set(holes); dq=deque(holes)
    while dq:
        p=dq.popleft()
        for d in D:
            b=(p[0]-d[0],p[1]-d[1]); h=(b[0]-d[0],b[1]-d[1])  # boulder at b pushed by hero at h in dir d to p
            if b in floor and h in floor and b not in live:
                live.add(b); dq.append(b)
    return live
DD={(0,-1):'8',(0,1):'2',(-1,0):'4',(1,0):'6',(1,-1):'9',(1,1):'3',(-1,1):'1',(-1,-1):'7'}
def reach(floor,B,Hs,start):
    seen={start}; par={start:None}; dq=deque([start])
    while dq:
        p=dq.popleft()
        for d in DD:
            q=(p[0]+d[0],p[1]+d[1])
            if q in floor and q not in B and q not in Hs and q not in seen:
                if d[0] and d[1]:
                    a=(p[0]+d[0],p[1]); c=(p[0],p[1]+d[1])
                    bad=lambda z: z not in floor or z in B
                    if bad(a) and bad(c): continue
                seen.add(q); par[q]=(p,d); dq.append(q)
    return seen,par
def path(par,t):
    ks=[]
    while par[t]:
        p,d=par[t]; ks.append(DD[d]); t=p
    return ''.join(reversed(ks))
def solve(txt,need,maxn=3000000,w=2):
    floor,B,Hs,hero,goal=parse(txt)
    live=live_squares(floor,Hs)
    spare=len(B)-len(Hs)
    H0=len(Hs)
    # distance from each live square to nearest hole (push distance approx = manhattan via BFS over floor)
    dist={}
    dq=deque((h,0) for h in Hs); seen=set(Hs)
    for h in Hs: dist[h]=0
    while dq:
        p,dd=dq.popleft()
        for d in D:
            q=(p[0]+d[0],p[1]+d[1])
            if q in floor and q not in seen: seen.add(q); dist[q]=dd+1; dq.append((q,dd+1))
    def hfun(B,Hs):
        k=H0-len(Hs)
        rem=need-k
        if rem<=0: return 0
        ds=sorted(dist.get(b,99) for b in B)
        return sum(ds[:rem])
    cnt=itertools.count()
    s0,_=reach(floor,B,Hs,hero)
    pq=[(hfun(B,Hs),next(cnt),0,B,Hs,hero,None)]
    visited={(B,Hs,min(s0)):None}
    parent={}
    n=0
    while pq:
        f,_,g,B,Hs,pos,st=heapq.heappop(pq)
        n+=1
        if n>maxn: return None
        if H0-len(Hs)>=need:
            # rebuild
            steps=[]; key=st
            while key is not None:
                steps.append(parent[key][1]); key=parent[key][0]
            return list(reversed(steps))
        seen,par=reach(floor,B,Hs,pos)
        dead_now=sum(1 for b in B if b not in live)
        for b in B:
            for d in D:
                src=(b[0]-d[0],b[1]-d[1]); dst=(b[0]+d[0],b[1]+d[1])
                if src not in seen or dst not in floor or dst in B: continue
                nB=set(B); nB.remove(b); nH=set(Hs)
                if dst in Hs: nH.remove(dst); nlive=live_squares(floor,nH) if False else live
                else: nB.add(dst)
                nB=frozenset(nB); nH=frozenset(nH)
                if sum(1 for x in nB if x not in live) > spare: continue
                s2,_=reach(floor,nB,nH,b)
                key=(nB,nH,min(s2))
                if key in visited: continue
                visited[key]=1
                parent[key]=(st,(path(par,src)+D[d],b,D[d]))
                heapq.heappush(pq,(g+1+w*hfun(nB,nH),next(cnt),g+1,nB,nH,b,key))
    return None
if __name__=='__main__':
    txt=open(sys.argv[1]).read().rstrip('\n'); need=int(sys.argv[2]); w=float(sys.argv[3]) if len(sys.argv)>3 else 2
    r=solve(txt,need,w=w)
    if r is None: print('NONE'); sys.exit(1)
    json.dump(r,open(sys.argv[4] if len(sys.argv)>4 else 'plan.json','w'))
    print('pushes',len(r))
