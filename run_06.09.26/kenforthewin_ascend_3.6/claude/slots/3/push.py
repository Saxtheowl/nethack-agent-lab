#!/usr/bin/env python3
# push.py "bx,by,dir,n" ... : for each, travel to stand square, then push n times (verify hero moves each push).
import re, subprocess, sys, os
os.environ['NH_SLOT']='3'
ROOT='/home/roro/work/projects/super_nethack/run_06.09.26/kenforthewin_ascend_3.6/claude'
def S(*a): return subprocess.run(['python3',ROOT+'/scripts/session.py',*a],capture_output=True,text=True,cwd=ROOT).stdout
def T(x,y): return subprocess.run([ROOT+'/slots/3/t',str(x),str(y)],capture_output=True,text=True,cwd=ROOT).stdout
D={'u':(0,-1,'8'),'d':(0,1,'2'),'l':(-1,0,'4'),'r':(1,0,'6')}
def hero():
    out=S('screen','--compact')
    h=re.search(r' @@(\d+),(\d+)',out)
    return (int(h[1]),int(h[2])) if h else None, out
for spec in sys.argv[1:]:
    bx,by,d,n=spec.split(','); bx,by,n=int(bx),int(by),int(n)
    dx,dy,key=D[d]
    stand=(bx-dx,by-dy)
    for attempt in range(3):
        if hero()[0]==stand: break
        T(*stand)
    h,out=hero()
    if h!=stand: print('FAIL reach',stand,'at',h); sys.exit(1)
    for i in range(n):
        before=h
        r=S('keys',key,'--settle','.5')
        h,out=hero()
        msgs=[l for l in out.splitlines() if re.match(r'^0[5-7] ',l)]
        if h!=(before[0]+dx,before[1]+dy):
            print('FAIL push',spec,'step',i,'hero',h); print('\n'.join(msgs)); sys.exit(1)
    print('ok',spec,'hero',h)
