import sys, json
import soko_solve2 as s
# usage: wiki2plan_gen.py LABELLED_MAP SEQFILE OUT.json
lines=open(sys.argv[1]).read().rstrip('\n').split('\n')
lab={}
for y,r in enumerate(lines):
    for x,c in enumerate(r):
        if c.isalpha() and c.isupper(): lab[c]=(x,y)
txt='\n'.join(''.join('0' if (c.isalpha() and c.isupper()) else c for c in r) for r in lines)
seq=[l.split()[0]+' '+''.join(l.split()[1:]) for l in open(sys.argv[2]).read().strip().split('\n')]
floor,B,Hs,hero,goal=s.parse(txt)
B=set(B); Hs=set(Hs); pos=dict(lab)
dirs={'u':(0,-1),'d':(0,1),'l':(-1,0),'r':(1,0)}
key={'u':'8','d':'2','l':'4','r':'6'}
plan=[]
for line in seq:
    L,mv=line.split()
    star=mv.endswith('*'); mv=mv.replace('*','')
    if star: mv=mv+mv[-1]*25
    for c in mv:
        b=pos[L]
        if b is None: break
        d=dirs[c]
        src=(b[0]-d[0],b[1]-d[1]); dst=(b[0]+d[0],b[1]+d[1])
        seen,par=s.reach(floor,frozenset(B),frozenset(Hs),hero)
        if src not in seen: print('UNREACHABLE',L,c,b,src); sys.exit(1)
        if dst not in floor or dst in B: print('BLOCKED',L,c,dst); sys.exit(1)
        plan.append([s.path(par,src)+key[c],list(b),key[c]])
        B.remove(b)
        if dst in Hs: Hs.remove(dst); pos[L]=None; print("hole",L,dst)
        else: B.add(dst); pos[L]=dst
        hero=b
    if star and pos[L] is not None: print('STAR NOT IN HOLE',L,pos[L]); sys.exit(1)
print('pushes',len(plan),'holes left',len(Hs))
json.dump(plan,open(sys.argv[3],'w'))
