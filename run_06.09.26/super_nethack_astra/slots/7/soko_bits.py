#!/usr/bin/env python3
"""Memory-lean weighted A* (bitmask states). Usage: soko_bits.py LEVEL W MAXS"""
import sys, heapq
from collections import deque
sys.path.insert(0, __file__.rsplit('/',1)[0])
from soko_solve import LEVELS, D
name=sys.argv[1]; W=float(sys.argv[2]); MAXS=int(sys.argv[3])
L=LEVELS[name]; grid=L['map']; H=len(grid)
def floor(x,y): return 0<=y<H and 0<=x<len(grid[y]) and grid[y][x]=='.'
cells=[(x,y) for y in range(H) for x in range(len(grid[y])) if floor(x,y)]
idx={c:i for i,c in enumerate(cells)}; N=len(cells)
DIRS=list(D.items())
nb=[[idx.get((c[0]+dx,c[1]+dy),-1) for _,(dx,dy) in DIRS] for c in cells]
back=[[idx.get((c[0]-dx,c[1]-dy),-1) for _,(dx,dy) in DIRS] for c in cells]
ENTRY=idx[min(L['pits'])]
dist=[10**6]*N; dist[ENTRY]=0; q=deque([ENTRY])
while q:
    c=q.popleft()
    for k in range(4):
        prev=back[c][k]
        if prev<0: continue
        stand=back[prev][k]
        if stand<0 or dist[prev]<10**6: continue
        dist[prev]=dist[c]+1; q.append(prev)
live=[d<10**6 for d in dist]
PITS=0
for p in L['pits']: PITS|=1<<idx[p]
B0=0
for b in L['boulders']: B0|=1<<idx[b]
def bits(m):
    while m:
        l=m&-m; yield l.bit_length()-1; m^=l
def reach(p,B,P):
    blocked=B|P; seen=1<<p; st=[p]
    while st:
        c=st.pop()
        for k in range(4):
            n=nb[c][k]
            if n>=0 and not (seen>>n)&1 and not (blocked>>n)&1:
                seen|=1<<n; st.append(n)
    return seen
def h(B,P):
    r=bin(P).count('1')
    if not r: return 0
    ds=sorted(dist[b] for b in bits(B))
    return sum(ds[:r])
start=idx[L['start']]
op=[(W*h(B0,PITS),0,B0,PITS,start)]
parent={}; closed=set(); n=0
first=(B0,PITS,(reach(start,B0,PITS)&-reach(start,B0,PITS)).bit_length()-1)
parent[first]=None
cnt=0
while op:
    f,g,B,P,p=heapq.heappop(op)
    r=reach(p,B,P); canon=(r&-r).bit_length()-1
    key=(B,P,canon)
    if key in closed: continue
    closed.add(key); n+=1
    if n%500000==0: print('expanded',n,'g',g,'pits',bin(P).count('1'),file=sys.stderr,flush=True)
    if n>MAXS: print('LIMIT'); sys.exit(1)
    if P==0:
        out=[]; k=key
        while parent.get(k): pk,push=parent[k]; out.append(push); k=pk
        out.reverse(); print(len(out))
        print(' '.join(f'{cells[b][0]},{cells[b][1]}{DIRS[d][0]}' for b,d in out)); sys.exit(0)
    for b in bits(B):
        for k in range(4):
            st=back[b][k]; to=nb[b][k]
            if st<0 or to<0 or not (r>>st)&1 or (B>>to)&1: continue
            if (P>>to)&1: nB=B&~(1<<b); nP=P&~(1<<to)
            else:
                if not live[to]: continue
                nB=(B&~(1<<b))|(1<<to); nP=P
            r2=reach(b,nB,nP); ck=(nB,nP,(r2&-r2).bit_length()-1)
            if ck in closed: continue
            if ck not in parent: parent[ck]=(key,(b,k))
            heapq.heappush(op,(g+1+W*h(nB,nP),g+1,nB,nP,b))
print('NO SOLUTION')
