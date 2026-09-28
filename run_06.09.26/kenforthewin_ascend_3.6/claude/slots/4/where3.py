import json,re,subprocess,sys
# where3.py PLAN OX OY : start boulders = SIM set; find idx whose pre-state equals screen boulders (ignoring (24,1))
start=[(2, 6), (2, 8), (3, 6), (3, 8), (3, 9), (3, 10), (4, 10), (5, 6), (5, 10), (6, 12), (7, 7), (10, 8), (10, 10), (11, 5), (11, 6), (11, 9), (12, 6), (12, 7)]
plan=json.load(open(sys.argv[1])); OX,OY=int(sys.argv[2]),int(sys.argv[3])
holes=set((x,1) for x in range(6,23))
o=subprocess.run(['python3','scripts/session.py','screen','--compact'],capture_output=True,text=True,cwd='../..').stdout
m=re.search(r'^Map features.*$',o,re.M).group(0)
S=set((int(a)-OX,int(b)-OY) for a,b in re.findall(r' 0@(\d+),(\d+)',m))-{(24,1)}
B=set(start); off={'8':(0,-1),'2':(0,1),'4':(-1,0),'6':(1,0)}
for i,st in enumerate(plan):
    if B==S: print('MATCH',i); sys.exit()
    b=tuple(st[1]); d=off[st[2]]; B.remove(b); n=(b[0]+d[0],b[1]+d[1])
    if n in holes: holes.remove(n)
    else: B.add(n)
print('NOMATCH' if B!=S else 'MATCH %d'%len(plan))
