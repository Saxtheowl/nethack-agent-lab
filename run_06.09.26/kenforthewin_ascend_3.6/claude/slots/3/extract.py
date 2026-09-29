import subprocess, sys
x0,y0,x1,y1=map(int,sys.argv[1:5]); outf=sys.argv[5]
out=subprocess.run(['python3','../../scripts/session.py','screen','--compact'],capture_output=True,text=True).stdout
rows={}
for l in out.splitlines():
    if l[:2].isdigit() and l[2]==' ':
        rows[int(l[:2])]=l[3:]
res=[]
for y in range(y0,y1+1):
    r=rows.get(y,'')
    seg=r[x0:x1+1].ljust(x1-x0+1)
    t=''
    for ch in seg:
        if ch in '│─┌┐└┘├┤┬┴┼+': t+='#'
        elif ch=='0': t+='0'
        elif ch=='^': t+='^'
        elif ch=='@': t+='@'
        elif ch==' ': t+=' '
        else: t+='.'
    res.append(t)
open(outf,'w').write('\n'.join(res))
for i,l in enumerate(res): print(y0+i, l)
