import sys, json
import soko_solve2 as s
txt=open(sys.argv[1]).read().rstrip('\n')
lab=dict(A=(2,3),B=(8,3),C=(9,4),D=(2,5),E=(4,5),F=(9,5),G=(2,6),H=(5,6),I=(6,7),J=(3,8),K=(7,8),L=(5,9),M=(10,9),N=(7,10),O=(10,10),P=(3,11))
seq="""B dd
C l
P rrru
O rr*
N d
M l
F u
B ll
K d
M rdrrr*
N lllllrrrrrrruu
K dd
N rdrrrr*
L dd
P r
K rruurdrrrrr*
P drruurdrrrrrrr*
L lllrrrrrrruurdrrrrrr*
I drdddrruurdrrrrrrrr*
J rrrrdddrruurdrrrrrrrrr*
A u
G r
D u
E r
B dddrdddrruurdrrrrrrrrrr*
E rdddrdddrruurdrrrrrrrrrrr*
H rrdddddrruurdrrrrrrrrrrrr*
G rrrrdddddrruurdrrrrrrrrrrrrr*"""
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
        if c=="r" and b[1]==10 and b[0]>=11 and ((b[0]+1,10) not in floor): print("lane end?",L); sys.exit(1)
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
