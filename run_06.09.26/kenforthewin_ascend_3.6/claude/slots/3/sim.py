import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from soko import parse, reach, D
lines=open(sys.argv[1]).read().split('\n')
w,f,b,h,p=parse(lines,int(sys.argv[2]),int(sys.argv[3]))
b=set(b); h=set(h)
for spec in sys.argv[4:]:
    x,y,d,n=spec.split(','); x,y,n=int(x),int(y),int(n); dx,dy=D[d]
    stand=(x-dx,y-dy)
    R=reach(p,f,b,h)
    if stand not in R: print('UNREACHABLE stand',stand,'for',spec); sys.exit(1)
    p=stand; bp=(x,y)
    for i in range(n):
        if bp not in b: print('no boulder at',bp,spec); sys.exit(1)
        dest=(bp[0]+dx,bp[1]+dy)
        if dest not in f or dest in b: print('BLOCKED',spec,'step',i,dest); sys.exit(1)
        b.discard(bp)
        if dest in h: h.discard(dest); 
        else: b.add(dest)
        p=bp; bp=dest
    print('ok',spec,'holes left',len(h))
print('final holes',sorted(h))
