#!/bin/bash
# rest1s.sh TARGET_HP [max_turns] [radius]: search one turn at a time; stop on HP loss, monster within radius, hunger/status, stole, target.
cd "$(dirname "$0")"
prev=999
for i in $(seq "${2:-60}"); do
  s=$(./session keys --compact s 2>&1)
  echo "$s" | grep -q 'ALARM\|refused' && { echo "STOP refused"; break; }
  echo "$s" | grep -qi 'stole\|steal' && { echo "STOP stole"; break; }
  echo "$s" | grep -E '^34' | grep -qE 'Hungry|Weak|Faint|Stone|Slime|Ill|Conf|Stun|Blind' && { echo "STOP status"; break; }
  hp=$(echo "$s" | grep -E '^34' | grep -o 'HP:[0-9]*' | cut -d: -f2)
  [ -n "$hp" ] && [ "$hp" -lt "$prev" ] && [ "$prev" != 999 ] && { echo "STOP hp loss $hp"; break; }
  prev=${hp:-$prev}
  near=$(python3 - "$s" "${3:-6}" <<'PY'
import re,sys
s=sys.argv[1]; R=int(sys.argv[2])
m=re.search(r'^Map features.*$',s,re.M)
if not m: print('?'); sys.exit()
m=m.group(0)
h=re.search(r' @@(\d+),(\d+)',m)
if not h: print('?'); sys.exit()
hx,hy=int(h[1]),int(h[2])
print(' '.join(f'{g}@{x},{y}' for g,x,y in re.findall(r" ([A-Za-z&;:'@])@(\d+),(\d+)",m) if (g!='@' or (int(x),int(y))!=(hx,hy)) and max(abs(int(x)-hx),abs(int(y)-hy))<=R))
PY
)
  [ -n "$near" ] && { echo "STOP near: $near"; break; }
  [ -n "$hp" ] && [ "$hp" -ge "$1" ] && { echo "target HP:$hp"; break; }
done
./session screen --compact 2>&1 | grep -E '^34'
