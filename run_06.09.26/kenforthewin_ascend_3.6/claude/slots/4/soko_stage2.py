import soko_solve2 as s, json, sys
def render(floor,B,Hs,hero,goal,W,H,walls_txt):
    rows=[list(r.ljust(W)) for r in walls_txt.split('\n')]
    for (x,y) in floor:
        rows[y][x]='.'
    for (x,y) in Hs: rows[y][x]='^'
    for (x,y) in B: rows[y][x]='0'
    if goal: rows[goal[1]][goal[0]]='<'
    rows[hero[1]][hero[0]]='@'
    return '\n'.join(''.join(r).rstrip() for r in rows)
txt=open(sys.argv[1]).read().rstrip('\n')
total=int(sys.argv[2]); step=int(sys.argv[3]) if len(sys.argv)>3 else 1
floor,B,Hs,hero,goal=s.parse(txt)
W=max(len(r) for r in txt.split('\n')); H=len(txt.split('\n'))
import os
plan=json.load(open(sys.argv[4])) if os.path.exists(sys.argv[4]) and len(sys.argv)>5 else []
filled=int(sys.argv[5]) if len(sys.argv)>5 else 0
cur=txt
while filled<total:
    need=min(step,total-filled)
    r=s.solve(cur,need,maxn=300000,w=2)
    if r is None:
        print('stuck after',filled); break
    # simulate
    floor,B,Hs,hero,goal=s.parse(cur)
    B=set(B); Hs=set(Hs)
    for keys,b,d in r:
        b=tuple(b); dd={'8':(0,-1),'2':(0,1),'4':(-1,0),'6':(1,0)}[d]
        dst=(b[0]+dd[0],b[1]+dd[1]); B.remove(b)
        if dst in Hs: Hs.remove(dst)
        else: B.add(dst)
        hero=b
    plan+=r; filled+=need
    cur=render(floor,B,Hs,hero,goal,W,H,txt.replace('0','.').replace('^','.').replace('@','.').replace('<','.'))
    print('filled',filled,'pushes',len(plan)); sys.stdout.flush()
    json.dump(plan,open(sys.argv[4],'w')); open(sys.argv[4]+'.map','w').write(cur)
json.dump(plan,open(sys.argv[4] if len(sys.argv)>4 else 'plan_stage.json','w'))
open('stage_final.map','w').write(cur)
print(cur)
