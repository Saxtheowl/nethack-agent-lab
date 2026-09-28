#!/bin/bash
# trollfarm.sh N: wait with s up to N turns next to a troll corpse; when an adjacent T appears, F-attack it (one blow per call, re-read). Stops on HP<60%, other monster within 3, hunger Weak, alarm.
cd "$(dirname "$0")"
for i in $(seq "${1:-60}"); do
  s=$(./v 2>&1)
  r=$(python3 - "$s" <<'PY'
import re,sys
s=sys.argv[1]
m=re.search(r'^Map features.*$',s,re.M).group(0)
h=re.search(r' @@(\d+),(\d+)',m); hx,hy=int(h[1]),int(h[2])
D={(-1,-1):'7',(0,-1):'8',(1,-1):'9',(-1,0):'4',(1,0):'6',(-1,1):'1',(0,1):'2',(1,1):'3'}
hp=re.search(r'HP:(\d+)\((\d+)\)',s)
if int(hp[1])*10<int(hp[2])*6: print('STOP hp'); sys.exit()
for g,x,y in re.findall(r' ([A-Za-z&;:])@(\d+),(\d+)',m):
    dx,dy=int(x)-hx,int(y)-hy
    if g=='T' and (dx,dy) in D: print('F'+D[(dx,dy)]); sys.exit()
    if g not in 'Ai' and max(abs(dx),abs(dy))<=3: print('STOP other '+g); sys.exit()
print('s')
PY
)
  case "$r" in
    STOP*) echo "$r"; break;;
    F*) o=$(./k --raw "$r" 2>&1); echo "$(echo "$o" | grep -E '^07' | cut -c5-90) $(echo "$o" | grep -oE 'HP:[0-9]+\([0-9]+\)|Xp:[0-9/]+' | tr '\n' ' ')"; echo "$o" | grep -q ALARM && { echo ALARM; break; };;
    s) o=$(./k --raw s 2>&1); echo "$o" | grep -q ALARM && { echo ALARM; break; }; echo "$o" | grep -E '^34' | grep -qE 'Weak|Faint' && { echo WEAK; break; };;
  esac
done
./v 2>&1 | grep -E '^34'
