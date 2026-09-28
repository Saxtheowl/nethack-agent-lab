import sys,re
t=sys.stdin.read(); ch=sys.argv[1]; a,b,c,d=map(int,sys.argv[2:6]); skip=set(sys.argv[6].split()) if len(sys.argv)>6 else set()
m=re.search(r'Terminal cursor[^:]*: (\d+),(\d+)',t); hx,hy=int(m[1]),int(m[2])
g=[(int(x),int(y)) for x,y in re.findall(r' '+re.escape(ch)+r'@(\d+),(\d+)',t)]
g=[p for p in g if a<=p[0]<=b and c<=p[1]<=d and '%d,%d'%p not in skip]
g.sort(key=lambda p:max(abs(p[0]-hx),abs(p[1]-hy)))
print('%d,%d'%g[0] if g else '')
