import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from soko import parse, reach, D
lines=open(sys.argv[1]).read().split('\n')
ox,oy=int(sys.argv[2]),int(sys.argv[3])
w,f,b,h,p=parse(lines,ox,oy)
b=set(b); h=set(h)
for spec in sys.argv[4:]:
    x,y,d,n=spec.split(','); x,y,n=int(x),int(y),int(n); dx,dy=D[d]
    stand=(x-dx,y-dy)
    R=reach(p,f,b,h)
    if stand not in R: print('UNREACHABLE stand',stand,'for',spec); break
    p=stand; bp=(x,y); ok=True
    for i in range(n):
        if bp not in b: print('no boulder at',bp,spec); ok=False; break
        dest=(bp[0]+dx,bp[1]+dy)
        if dest not in f or dest in b: print('BLOCKED',spec,'step',i,dest); ok=False; break
        b.discard(bp)
        if dest in h: h.discard(dest)
        else: b.add(dest)
        p=bp; bp=dest
    if not ok: break
R=reach(p,f,b,h)
for r,line in enumerate(lines):
    s=''
    for c,ch in enumerate(line):
        q=(c+ox,r+oy)
        if q==p: s+='@'
        elif q in b: s+='0'
        elif q in h: s+='^'
        elif q in f: s+=('.' if q in R else ',')
        else: s+='#'
    print(r+oy, s)
print('holes left',len(h),'boulders',len(b))
