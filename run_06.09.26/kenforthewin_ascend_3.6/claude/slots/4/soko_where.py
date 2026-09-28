import sys, json, re, subprocess
# soko_where.py LABMAP OX OY FULLPLAN : find index in full plan whose pre-state matches current screen boulders
lab, OX, OY, planf = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
lines=open(lab).read().rstrip('\n').split('\n')
B=set((x,y) for y,r in enumerate(lines) for x,c in enumerate(r) if c.isupper() or c=='0')
Hs=set((x,y) for y,r in enumerate(lines) for x,c in enumerate(r) if c=='^')
o=subprocess.run(['python3','scripts/session.py','screen','--compact'],capture_output=True,text=True,cwd='/home/roro/work/projects/super_nethack/run_06.09.26/kenforthewin_ascend_3.6/claude',env={'NH_SLOT':'4','PATH':'/usr/bin:/bin'}).stdout
m=re.search(r'^Map features.*$',o,re.M).group(0)
S=set((int(a)-OX,int(b)-OY) for a,b in re.findall(r' 0@(\d+),(\d+)',m))
off={'8':(0,-1),'2':(0,1),'4':(-1,0),'6':(1,0)}
plan=json.load(open(planf))
for i,st in enumerate(plan):
    if B==S: print('MATCH index',i); sys.exit(0)
    b=tuple(st[1]); d=off[st[2]]; B.remove(b); n=(b[0]+d[0],b[1]+d[1])
    if n in Hs: Hs.remove(n)
    else: B.add(n)
print('MATCH end' if B==S else 'NO MATCH')
