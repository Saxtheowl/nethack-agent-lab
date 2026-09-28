import sys, json
import soko_solve2 as s
txt=open(sys.argv[1]).read().rstrip('\n')
lab=dict(K=(5,7),D=(8,4),I=(6,10),G=(10,3),H=(11,3))
seq="""K ddlllrrrrrrrrrrrrrrr*"""
floor,B,Hs,hero,goal=s.parse(txt)
B=set(B); Hs=set(Hs); pos=dict(lab)
dirs={'u':(0,-1),'d':(0,1),'l':(-1,0),'r':(1,0)}
key={'u':'8','d':'2','l':'4','r':'6'}
plan=[]
for line in seq.split('\n'):
    L,mv=line.split()
    star=mv.endswith('*'); mv=mv.replace('*','')
    if star: mv=mv+'r'*12
    for c in mv:
        if c=='*': continue
        b=pos[L]; d=dirs[c]
        if b is None: break
        if False and c=="r" and b[1]==10 and b[0]>=11 and ((b[0]+1,10) not in floor): print("lane end?",L); sys.exit(1)
        src=(b[0]-d[0],b[1]-d[1]); dst=(b[0]+d[0],b[1]+d[1])
        seen,par=s.reach(floor,frozenset(B),frozenset(Hs),hero)
        if src not in seen: print('UNREACHABLE',L,c,b,src); sys.exit(1)
        if dst not in floor or dst in B: print('BLOCKED',L,c,dst); sys.exit(1)
        plan.append([s.path(par,src)+key[c],list(b),key[c]])
        B.remove(b)
        if dst in Hs: Hs.remove(dst); pos[L]=None; print("hole",L,dst)
        else: B.add(dst); pos[L]=dst
        hero=b
print('pushes',len(plan),'holes left',len(Hs))
seen,par=s.reach(floor,frozenset(B),frozenset(Hs),hero)
print('goal reachable', goal in seen)
json.dump(plan,open(sys.argv[2],'w'))
