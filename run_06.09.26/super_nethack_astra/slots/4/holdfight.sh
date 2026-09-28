#!/bin/bash
# holdfight.sh N GLYPHS: N times: fight adjacent GLYPHS, else search 1 turn. Stop HP<55%.
cd "$(dirname "$0")"
for i in $(seq "$1"); do
  r=$(./adjfight.py "$2" 6)
  echo "$r" | grep -aE "^\[|STOP|skip" | tail -3
  echo "$r" | grep -q "STOP" && break
  if echo "$r" | grep -q "no adjacent target"; then
    s=$(cd ../.. && NH_SLOT=4 python3 scripts/session.py keys --compact --raw s)
    hp=$(echo "$s" | grep -ao 'HP:[0-9]*(' | tr -dc 0-9); mx=$(echo "$s" | grep -ao 'HP:[0-9]*([0-9]*' | sed 's/.*(//')
    [[ $((hp*100)) -lt $((mx*55)) ]] && { echo "STOP HP $hp"; break; }
    echo "$s" | grep -aqE "Weak|Fainting|stole" && { echo "STOP hunger/stole"; break; }
  fi
done
cd ../.. && NH_SLOT=4 python3 scripts/session.py screen --compact | grep -aE "HP:|^Map"
