#!/usr/bin/env python3
# Greedy sokoban: repeatedly route one boulder into the nearest hole (single-boulder BFS), simulate, print plan.
import sys, itertools, random
from collections import deque
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from soko import parse, reach, D
def single(floor,boulders,holes,player,b):
    others=boulders-{b}
    start=(b,player)
    R=reach(player,floor,boulders,holes)
    q=deque([(b,frozenset(R),[])]); seen={(b,min(R))}
    while q:
        bp,R,path=q.popleft()
        for dn,(dx,dy) in D.items():
            stand=(bp[0]-dx,bp[1]-dy); dest=(bp[0]+dx,bp[1]+dy)
            if stand not in R or dest not in floor or dest in others: continue
            np=path+[(bp,dn)]
            if dest in holes: return np
            nb=others|{dest}
            R2=reach(bp,floor,nb,holes)
            k=(dest,min(R2))
            if k in seen: continue
            seen.add(k); q.append((dest,frozenset(R2),np))
    return None
def compress(path):
    out=[]
    for (bp,dn) in path:
        if out and out[-1][1]==dn and out[-1][3]==bp: 
            dx,dy=D[dn]; out[-1]=(out[-1][0],dn,out[-1][2]+1,(bp[0]+dx,bp[1]+dy))
        else:
            dx,dy=D[dn]; out.append((bp,dn,1,(bp[0]+dx,bp[1]+dy)))
    return [f"{a[0][0]},{a[0][1]},{a[1]},{a[2]}" for a in out]
def run(floor,b,h,p,order_seed=None):
    plan=[]
    while h:
        best=None
        cands=list(b)
        for bb in cands:
            path=single(floor,b,h,p,bb)
            if path and (best is None or len(path)<len(best[1])): best=(bb,path)
        if not best: return plan,b,h,p,False
        bb,path=best
        # apply
        bp=bb
        for (pos,dn) in path:
            dx,dy=D[dn]; bp=(pos[0]+dx,pos[1]+dy)
        b=(b-{bb}); h=h-{bp}; p=path[-1][0]
        plan.append(compress(path))
    return plan,b,h,p,True
if __name__=='__main__':
    lines=open(sys.argv[1]).read().split('\n')
    w,f,b,h,p=parse(lines,int(sys.argv[2]),int(sys.argv[3]))
    plan,b2,h2,p2,ok=run(f,b,h,p)
    for st in plan: print(' '.join(st))
    print('OK' if ok else f'STUCK holes left {sorted(h2)} boulders {sorted(b2)}')
