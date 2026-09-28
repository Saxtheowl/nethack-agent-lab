import sys
ox,oy=27,13; HOLEROW=14; FIRST=35
m="""--------------------------
|@......^^^^^^^^^^^^^^^^.|
|.......----------------.|
-------.------         |.|
 |...........|         |.|
 |.A.B.C.D.E.|         |.|
--------.----|         |.|
|...F.G..H.I.|         |.|
|...J........|         |.|
-----.--------   ------|.|
 |..K.L.M...|  --|.....|.|
 |.....N....|  |.+.....|.|
 |.O.P...Q.--  |-|.....|.|
-------.----   |.+.....+.|
|..R.....|     |-|.....|--
|........|     |.+.....|
|...------     --|.....|
-----            -------""".split('\n')
pos={}
for r,l in enumerate(m):
    for c,ch in enumerate(l):
        if ch.isupper() and ch not in 'X': pos[ch]=(ox+c,oy+r)
steps=open('steps4.txt').read().strip().split('\n')
D={'l':(-1,0),'r':(1,0),'u':(0,-1),'d':(0,1)}
k=0
occ=set(pos.values())
for i,line in enumerate(steps):
    b,mv=line[0],line[2:].replace(' ','')
    x,y=pos[b]; star=mv.endswith('*'); mv=mv.rstrip('*')
    xx,yy=x,y
    for c in mv: xx+=D[c][0]; yy+=D[c][1]
    if star:
        assert yy==HOLEROW,(b,xx,yy)
        extra=(FIRST+k)-xx; assert extra>=0,(b,xx,k)
        mv+='r'*extra; k+=1
    print(i+1,b,x,y,mv)
    pos[b]=(xx,yy) if not star else None
print('holes',k,file=sys.stderr)
