import sys
lab=open(sys.argv[1]).read().splitlines(); ox,oy=int(sys.argv[3]),int(sys.argv[4])
seq=[l.split(None,1) for l in open(sys.argv[2]).read().splitlines() if l.strip()]
pos={}
for y,row in enumerate(lab):
    for x,c in enumerate(row):
        if c.isupper(): pos[c]=(x+ox,y+oy)
D={'l':(-1,0),'r':(1,0),'u':(0,-1),'d':(0,1)}
for i,(b,m) in enumerate(seq):
    m=m.replace(' ','').replace('*','')
    x,y=pos[b]; print(i,b,x,y,m)
    for c in m: x+=D[c][0]; y+=D[c][1]
    pos[b]=(x,y)
