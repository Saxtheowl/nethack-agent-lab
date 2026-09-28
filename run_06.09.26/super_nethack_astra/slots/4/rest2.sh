#!/bin/bash
# rest2.sh TARGET [rounds] [radius]: n20s rests; stop if a monster letter within radius (default 7), kk STOP, hunger, target HP reached.
cd "$(dirname "$0")"
for r in $(seq "${2:-15}"); do
  o=$(./kk n20s 1 2>&1)
  echo "$o" | grep -E '^\[|STOP' | tail -1 | cut -c1-80
  echo "$o" | grep -q STOP && break
  s=$(./v 2>&1)
  echo "$s" | grep -E '^34' | grep -qE 'Hungry|Weak|Faint' && { echo "STOP hunger"; break; }
  near=$(python3 - "$s" "${3:-7}" <<'PY'
import re,sys
s=sys.argv[1]; R=int(sys.argv[2])
m=re.search(r'^Map features.*$',s,re.M).group(0)
h=re.search(r' @@(\d+),(\d+)',m)
if not h: print('?'); sys.exit()
hx,hy=int(h[1]),int(h[2])
out=[f'{g}@{x},{y}' for g,x,y in re.findall(r' ([A-Za-z&;:])@(\d+),(\d+)',m) if max(abs(int(x)-hx),abs(int(y)-hy))<=R]
print(' '.join(out))
PY
)
  [[ -n "$near" ]] && { echo "STOP near: $near"; break; }
  hp=$(echo "$s" | grep -o 'HP:[0-9]*' | head -1 | cut -d: -f2)
  [[ $hp -ge $1 ]] && { echo "target reached HP:$hp"; break; }
done
./v 2>&1 | grep -E '^34'
