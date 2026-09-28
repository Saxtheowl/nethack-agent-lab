import sys
from collections import deque
m=[l.rstrip('\n') for l in open('valley3.map')][:20]
W=max(len(l) for l in m); m=[l.ljust(W) for l in m]
sx,sy,tx,ty=map(int,sys.argv[1:5])
ok=lambda x,y: 0<=y<len(m) and 0<=x<W and m[y][x] in '.SB'
prev={(sx,sy):None}; q=deque([(sx,sy)])
while q:
    x,y=q.popleft()
    if (x,y)==(tx,ty): break
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            n=(x+dx,y+dy)
            if n not in prev and ok(*n):
                if dx and dy and (m[y][x]=='S' or m[n[1]][n[0]]=='S'): continue
                prev[n]=(x,y); q.append(n)
p=[]; c=(tx,ty)
while c: p.append(c); c=prev.get(c)
p=p[::-1]
# waypoints every ~8 steps, in screen coords (+3,+11)
print(' '.join(f'{x+3},{y+11}' for i,(x,y) in enumerate(p) if i%8==0 or i==len(p)-1))
print('S doors on path:',[ (x+3,y+11) for x,y in p if m[y][x]=='S'])
