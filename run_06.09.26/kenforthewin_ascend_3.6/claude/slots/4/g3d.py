import sys, json
import soko_solve2 as s
# g3.py LAB SEQ OUT DONE_PUSHES REMOVE_LABEL : simulate first DONE pushes (no output), remove label, continue skipping its lines; hero taken from screen arg
lines=open(sys.argv[1]).read().rstrip('\n').split('\n')
lab={}
for y,r in enumerate(lines):
    for x,c in enumerate(r):
        if c.isalpha() and c.isupper(): lab[c]=(x,y)
txt='\n'.join(''.join('0' if (c.isalpha() and c.isupper()) else c for c in r) for r in lines)
seq=[l.split()[0]+' '+''.join(l.split()[1:]) for l in open(sys.argv[2]).read().strip().split('\n')]
done=int(sys.argv[4]); rem=sys.argv[5]; hx,hy=map(int,sys.argv[6].split(','))
floor,B,Hs,hero,goal=s.parse(txt)
B=set(B); Hs=set(Hs); pos=dict(lab)
dirs={'u':(0,-1),'d':(0,1),'l':(-1,0),'r':(1,0)}
key={'u':'8','d':'2','l':'4','r':'6'}
plan=[]; n=0; removed=False
for line in seq:
    L,mv=line.split()
    if removed and L==rem: continue
    star=mv.endswith('*'); mv=mv.replace('*','')
    if star: mv=mv+mv[-1]*25
    for c in mv:
        if n==done and not removed:
            B.discard(pos[rem]); pos[rem]=None; removed=True; hero=(hx,hy); print("SIM",sorted(B))
            if L==rem: break
        b=pos[L]
        if b is None: break
        d=dirs[c]
        src=(b[0]-d[0],b[1]-d[1]); dst=(b[0]+d[0],b[1]+d[1])
        seen,par=s.reach(floor,frozenset(B),frozenset(Hs),hero)
        if src not in seen: print('UNREACHABLE',L,c,b,src); sys.exit(1)
        if dst not in floor or dst in B: print('BLOCKED',L,c,dst); sys.exit(1)
        if removed: plan.append([s.path(par,src)+key[c],list(b),key[c]])
        n+=1
        B.remove(b)
        if dst in Hs: Hs.remove(dst); pos[L]=None
        else: B.add(dst); pos[L]=dst
        hero=b
print('pushes',len(plan),'holes left',sorted(Hs))
json.dump(plan,open(sys.argv[3],'w'))
