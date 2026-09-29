#!/bin/bash
# run3.sh FROM TO [planfile]: per push: travel to the push square (game travel), press the direction, verify.
cd "$(dirname "$0")/../../.."
export NH_SLOT=8
A=$1; Z=$2; P=slots/8/soko7/${3:-plan1.txt}
S="python3 scripts/session.py"
pos() { $S screen --compact | grep -o 'cursor (x,y; usually hero when no menu): [0-9]*,[0-9]*' | grep -o '[0-9]*,[0-9]*$'; }
while read n b x y mv; do
  [ $n -lt $A ] && continue; [ $n -gt $Z ] && break
  for ((i=0;i<${#mv};i++)); do
    c=${mv:i:1}
    case $c in l) dx=-1;dy=0;k=4;; r) dx=1;dy=0;k=6;; u) dx=0;dy=-1;k=8;; d) dx=0;dy=1;k=2;; esac
    px=$((x-dx)); py=$((y-dy))
    for t in 1 2 3 4; do
      [ "$(pos)" = "$px,$py" ] && break
      $S travel $px $py >/dev/null 2>&1; $S keys --named Escape >/dev/null 2>&1
    done
    [ "$(pos)" = "$px,$py" ] || { echo "FAIL step $n $b: cannot reach $px,$py (at $(pos))"; exit 1; }
    o=$($S keys --compact --why "soko push $b" $k 2>&1); $S keys --named Escape >/dev/null 2>&1
    nx=$((x+dx)); ny=$((y+dy))
    if [ "$(pos)" != "$x,$y" ]; then echo "FAIL step $n $b push $c at $x,$y: hero at $(pos)"; echo "$o" | grep -E "^0[67]|HP:|efus"; exit 1; fi
    x=$nx; y=$ny
    hp=$(echo "$o" | grep -o 'HP:[0-9]*([0-9]*)' | head -1)
    cur=${hp#HP:}; cur=${cur%%(*}; mx=${hp#*(}; mx=${mx%)}
    [ -n "$cur" ] && [ $((cur*3)) -lt $((mx*2)) ] && { echo "STOP HP $hp"; exit 2; }
  done
  echo "done step $n $b $hp"
done < $P
