#!/bin/bash
# restfight.sh TARGET_HP [rounds]: n20s rests; fights adjacent hostile letters (adjfight); stops at target, HP<50%, hunger, stolen.
cd "$(dirname "$0")"
for r in $(seq "${2:-10}"); do
  out=$(./kk n20s 1 2>&1)
  hp=$(echo "$out" | grep -o 'HP:[0-9]*' | head -1 | cut -d: -f2)
  echo "$out" | grep -aE "^\[|STOP" | tail -2
  echo "$out" | grep -q "hunger" && { echo "STOP hunger"; break; }
  echo "$out" | grep -qi "stole" && { echo "STOP stole"; break; }
  if echo "$out" | grep -q "STOP: adjacent\|STOP: HP loss"; then ./adjfight.py 'abcdfghiklmnopqrstuvwxyzABCDEGHIJKLMNOPQRSTUVWXYZ&;:' 8 | grep -v ^Map; fi
  s=$(cd ../.. && NH_SLOT=4 python3 scripts/session.py screen --compact)
  hp=$(echo "$s" | grep -o 'HP:[0-9]*(' | tr -dc 0-9); mx=$(echo "$s" | grep -o 'HP:[0-9]*([0-9]*' | sed 's/.*(//')
  [[ $((hp*2)) -lt $mx ]] && { echo "STOP HP<50%"; break; }
  [[ $hp -ge $1 ]] && { echo "target reached HP:$hp"; break; }
done
