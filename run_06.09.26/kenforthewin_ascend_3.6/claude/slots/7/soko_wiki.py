#!/usr/bin/env python3
"""soko_wiki.py STATEFILE START_INDEX : execute wiki solution groups via slots/7/spush, tracking boulder positions.
State file is JSON {labels:{L:[x,y]}, moves:[[L,'dd'],...], off:[ox,oy], done:n}."""
import json, sys, subprocess
sf=sys.argv[1]; st=json.load(open(sf))
D={'l':(-1,0),'r':(1,0),'u':(0,-1),'d':(0,1)}
ox,oy=st['off']
limit=int(sys.argv[2]) if len(sys.argv)>2 else 999
k=0
while st['done']<len(st['moves']) and k<limit:
    lab,seq=st['moves'][st['done']]
    x,y=st['labels'][lab]; dirs=seq.replace('*','').replace(' ','')
    while True:
        r=subprocess.run(['slots/7/spush',str(x+ox),str(y+oy),dirs],capture_output=True,text=True)
        if 'continues after filling' in r.stdout and seq.endswith('*') and len(dirs)>1:
            dirs=dirs[:-1]; continue
        break
    print(lab,seq,'->',r.stdout.strip().split('\n')[-1][:120])
    if r.returncode!=0 or 'NO PLAN' in r.stdout or 'LOSS' in r.stdout or 'PROMPT' in r.stdout:
        print('HALT', r.stdout[-400:]); break
    for c in dirs: x+=D[c][0]; y+=D[c][1]
    extra=0
    while seq.endswith('*') and 'plugs' not in r.stdout and extra<3:
        r=subprocess.run(['slots/7/spush',str(x+ox),str(y+oy),'r'],capture_output=True,text=True)
        print('  extra r ->', r.stdout.strip().split('\n')[-1][:100]); x+=1; extra+=1
        if 'NO PLAN' in r.stdout or 'LOSS' in r.stdout: print('HALT'); sys.exit(1)
    st['labels'][lab]=[x,y]; st['done']+=1; k+=1
    json.dump(st,open(sf,'w'))
print('done', st['done'], '/', len(st['moves']))
