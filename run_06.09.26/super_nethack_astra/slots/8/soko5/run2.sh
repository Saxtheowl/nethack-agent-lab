#!/bin/bash
# run2.sh FROM TO [planfile]: execute plan steps in chunks of 5 pushes; verify boulder position after each chunk.
cd "$(dirname "$0")"
A=$1; Z=$2; P=${3:-plan2.txt}
while read n b x y mv; do
  [ $n -lt $A ] && continue; [ $n -gt $Z ] && break
  while [ -n "$mv" ]; do
    ch=${mv:0:5}; mv=${mv:5}
    out=$(cd ../../.. && python3 slots/8/sokoban8.py $x $y $ch --execute --max-steps 60 2>&1)
    for ((i=0;i<${#ch};i++)); do case ${ch:i:1} in l) x=$((x-1));; r) x=$((x+1));; u) y=$((y-1));; d) y=$((y+1));; esac; done
    scr=$(cd ../../.. && NH_SLOT=8 python3 scripts/session.py screen --compact)
    hp=$(echo "$scr" | grep -o 'HP:[0-9]*([0-9]*)' | head -1)
    if [ -n "$mv" ] || ! [ $y = 25 -a $x -ge 39 ]; then
      echo "$scr" | grep "^Map" | grep -q " 0@$x,$y" || { echo "FAIL step $n $b: expected boulder at $x,$y after $ch ($hp)"; echo "$out" | grep -E "Error|STOP|^07" | tail -3; echo "$scr" | grep -E "^0[67]|^Map|^Neigh"; exit 1; }
    fi
  done
  echo "done step $n $b $hp"
done < $P
