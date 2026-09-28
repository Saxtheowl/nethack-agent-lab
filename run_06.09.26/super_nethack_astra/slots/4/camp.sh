#!/bin/bash
# camp.sh N : wait (n20s) up to N times at current spot; stop on any visible monster letter, kk STOP, hunger, HP<80%.
cd "$(dirname "$0")"
for r in $(seq "${1:-10}"); do
  out=$(./kk n20s 1 2>&1)
  echo "$out" | grep -aE "^\[" | tail -1
  echo "$out" | grep -q "STOP" && { echo "$out" | grep STOP; break; }
  s=$(./v 2>&1)
  echo "$s" | grep -E '^34' | grep -qE 'Hungry|Weak|Faint' && { echo "STOP hunger"; break; }
  hp=$(echo "$s" | grep -o 'HP:[0-9]*(' | tr -dc 0-9); mx=$(echo "$s" | grep -o 'HP:[0-9]*([0-9]*' | sed 's/.*(//')
  [[ $((hp*10)) -lt $((mx*8)) ]] && { echo "STOP HP<80%"; break; }
  mon=$(echo "$s" | grep -E '^Map' | grep -oE ' [A-Za-z&;:]@[0-9]+,[0-9]+' | tr -d ' ' | tr '\n' ' ')
  [[ -n "$mon" ]] && { echo "STOP monsters: $mon"; break; }
done
echo "$s" | grep -E '^34'
