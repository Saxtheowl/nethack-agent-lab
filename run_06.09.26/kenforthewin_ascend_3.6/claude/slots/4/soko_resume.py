#!/usr/bin/env python3
"""soko_resume.py LABMAP OX OY PLAN IDX OUT : rebuild board from screen, recompute walk for step IDX, write OUT = plan[IDX:] with fixed step."""
import sys, json, re, subprocess
import soko_solve2 as s
lab, OX, OY, planf, idx, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], int(sys.argv[5]), sys.argv[6]
lines=open(lab).read().rstrip('\n').split('\n')
txt='\n'.join(''.join('.' if (c.isalpha() and c.isupper()) or c in '0@^' else c for c in r) for r in lines)
floor=set((x,y) for y,r in enumerate(lines) for x,c in enumerate(r) if c in '.0^@<>' or c.isupper())
o=subprocess.run(['python3','scripts/session.py','screen','--compact'],capture_output=True,text=True,cwd='/home/roro/work/projects/super_nethack/run_06.09.26/kenforthewin_ascend_3.6/claude',env={'NH_SLOT':'4','PATH':'/usr/bin:/bin'}).stdout
m=re.search(r'^Map features.*$',o,re.M).group(0)
B=set((int(a)-OX,int(b)-OY) for a,b in re.findall(r' 0@(\d+),(\d+)',m))
Hs=set((int(a)-OX,int(b)-OY) for a,b in re.findall(r' \^@(\d+),(\d+)',m))
c=re.search(r'Terminal cursor[^:]*: (\d+),(\d+)',o); hero=(int(c[1])-OX,int(c[2])-OY)
plan=json.load(open(planf)); st=plan[idx]; b=tuple(st[1]); d=st[2]
off={'8':(0,-1),'2':(0,1),'4':(-1,0),'6':(1,0)}[d]
src=(b[0]-off[0],b[1]-off[1])
print('hero',hero,'boulder',b,'in B',b in B,'src',src)
seen,par=s.reach(floor,frozenset(B),frozenset(Hs),hero)
if src not in seen: print('UNREACHABLE'); sys.exit(1)
st[0]=s.path(par,src)+d
json.dump(plan[idx:],open(out,'w')); print('ok',st, len(plan)-idx,'steps')
