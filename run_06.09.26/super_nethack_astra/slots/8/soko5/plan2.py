pos={'A':(29,18),'B':(35,18),'C':(36,19),'D':(29,20),'E':(31,20),'F':(36,20),'G':(29,21),'H':(32,21),'I':(33,22),'J':(30,23),'K':(34,23),'L':(32,24),'M':(37,24),'N':(34,25),'O':(37,25),'P':(30,26)}
steps="""B dd
C l
P rrru
O rr*
N d
M l
F u
B ll
K d
M rdrr r*
N llll lrrr rrrr uu
K dd
N rdrr rr*
L dd
P r
K rruu rdrr rrr*
P drru urdr rrrr rr*
L lllr rrrr rruu rdrr rrrr*
I drdd drru urdr rrrr rrr*
J rrrr dddr ruur drrr rrrr rr*
A u
G r
D u
E r
B dddr dddr ruur drrr rrrr rrr*
E rddd rddd rruu rdrr rrrr rrrr r*
H rrdd dddr ruur drrr rrrr rrrr r*
G rrrr dddd drru urdr rrrr rrrr rrrr*"""
D={'l':(-1,0),'r':(1,0),'u':(0,-1),'d':(0,1)}
k=0
for i,line in enumerate(steps.split('\n')):
    b,mv=line[0],line[2:].replace(' ','')
    x,y=pos[b]; star=mv.endswith('*'); mv=mv.rstrip('*')
    if star:
        # after the explicit moves, boulder on row 25 pushed right until hole 39+k
        xx,yy=x,y
        for c in mv: xx+=D[c][0]; yy+=D[c][1]
        assert yy==25,(b,xx,yy)
        mv+= 'r'*((39+k)-xx); k+=1
    print(i+1,b,x,y,mv)
    for c in mv: x+=D[c][0]; y+=D[c][1]
    pos[b]=(x,y) if not star else None
print('holes',k)
