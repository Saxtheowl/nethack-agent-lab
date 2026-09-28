import sys
ox,oy=31,15; HOLEROW=24; FIRST=39
m=""" --------------------
|........|...|.....|
|.AB..-CD|.-.|.....|
|..|.E.F.|GH.|.....|
|-.|..-..|.-.|..<..|
|...--.......|.....|
|...|.I.-...-|.....|
|.J.|K.|...--|.....|
|-L.|..-----------+|
|..M....^^^^^^^^^^.|
|...|.@-------------""".split('\n')[1:]
pos={}
for r,l in enumerate(m):
    for c,ch in enumerate(l):
        if ch.isupper(): pos[ch]=(ox+c,oy+r+1)
steps="""M lrrr rrr*
J r
L drrr rrrr*
J ddrr rrrr r*
A dddd dddr rrrr rrrr*
B lddd dddd rrrr rrrr rr*
E u
D dd
F lllu
E d
F lldd dddd drrr rrrr rrrr*
E lull dddd dddr rrrr rrrr rrr*
C dlll ulld dddd ddrr rrrr rrrr rrr*
I dddr rrrr rrrr r*
K ddll lrrr rrrr rrrr rrrr*"""
D={'l':(-1,0),'r':(1,0),'u':(0,-1),'d':(0,1)}
k=0
for i,line in enumerate(steps.split('\n')):
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
