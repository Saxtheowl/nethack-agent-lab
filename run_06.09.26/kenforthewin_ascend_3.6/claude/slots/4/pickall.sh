#!/bin/bash
# pickall.sh X,Y ... : travel to each square and pick up all non-corpse, non-rock items (menu parsed)
cd "$(dirname "$0")/../.."
S="python3 scripts/session.py"
for p in "$@"; do
  x=${p%,*}; y=${p#*,}
  o=$(scripts/t $x $y 2>&1)
  echo "$o" | grep -q "^Neighbors of @($x,$y)" || { echo "not reached $p"; continue; }
  $S keys --raw , --settle .6 >/dev/null
  scr=$($S screen)
  if echo "$scr" | grep -q "Pick up what"; then
    keys=$(echo "$scr" | python3 -c "
import sys,re
k=''
for l in sys.stdin:
    for m in re.finditer(r'│ ?([a-zA-Z\$])\) (.*?)(?=│|$)', l):
        t=m.group(2)
        if re.search(r'corpse|rock|boulder|statue|gray stone|loadstone', t): continue
        k+=m.group(1)
print(k)")
    $S keys --raw "$keys" >/dev/null; $S keys --named Enter --settle .8 >/dev/null
  fi
  for i in 1 2 3; do $S screen | grep -q '>>\|--More--' && $S keys --named Enter >/dev/null; done
  echo "$p: $($S screen --compact | grep -E '^0[5-7]' | tail -2 | cut -c5-85 | tr '\n' ' ')"
done
