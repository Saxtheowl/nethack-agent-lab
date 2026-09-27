#!/usr/bin/env python3
"""Stage-wise Sokoban solver: fill pits in the given order, each stage a BFS on pushes.
Prints per stage the push list 'x,y dir' in MAP coords. Uses soko_solve.LEVELS."""
import sys
from collections import deque
sys.path.insert(0, __file__.rsplit('/',1)[0])
from soko_solve import LEVELS, D

def run(name, maxstates=400000):
    L=LEVELS[name]; grid=L['map']; H=len(grid)
    def floor(x,y): return 0<=y<H and 0<=x<len(grid[y]) and grid[y][x]=='.'
    def reach(p,B,P):
        s={p}; q=deque([p])
        while q:
            x,y=q.popleft()
            for dx,dy in D.values():
                n=(x+dx,y+dy)
                if n not in s and floor(*n) and n not in B and n not in P: s.add(n); q.append(n)
        return s
    def dead(x,y,P):
        if (x,y) in P: return False
        w=[not floor(x+dx,y+dy) for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]]
        return (w[0] or w[1]) and (w[2] or w[3])
    B=frozenset(L['boulders']); P=set(L['pits']); p=L['start']
    allsol=[]
    for target in L['pits']:
        start=(B,p)
        q=deque([(B,p,[])]); seen=set()
        found=None; n=0
        while q:
            b,pp,path=q.popleft(); n+=1
            if n>maxstates: break
            r=reach(pp,b,P)
            key=(b,min(r))
            if key in seen: continue
            seen.add(key)
            for bo in b:
                for dn,(dx,dy) in D.items():
                    st=(bo[0]-dx,bo[1]-dy); to=(bo[0]+dx,bo[1]+dy)
                    if st not in r or not floor(*to) or to in b: continue
                    np=path+[(bo,dn)]
                    if to==target:
                        found=(b-{bo},bo,np); break
                    if to in P: continue   # don't fill other pits out of order
                    if dead(*to,P): continue
                    q.append(((b-{bo})|{to},bo,np))
                if found: break
            if found: break
        if not found:
            print('STAGE FAIL', target, 'states', n); return
        B,p,path=found; B=frozenset(B); P.discard(target)
        print(f'# pit {target}: ' + ' '.join(f'{x},{y}{d}' for (x,y),d in path))
        allsol.append(path)

run(sys.argv[1])
