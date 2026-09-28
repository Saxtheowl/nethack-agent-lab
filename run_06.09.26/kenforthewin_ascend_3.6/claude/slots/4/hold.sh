#!/bin/bash
# hold.sh N MINHP : fight any adjacent monster letter (except F molds unless FIGHTF), else search; stop HP<MINHP
cd "$(dirname "$0")/../.."
S="python3 scripts/session.py"
for i in $(seq "${1:-20}"); do
  o=$($S screen --compact)
  hp=$(echo "$o" | grep -o 'HP:[0-9]*' | head -1); hp=${hp#HP:}
  [ "$hp" -lt "${2:-35}" ] && { echo "HP $hp < min"; break; }
  me=$(echo "$o" | grep -o 'Terminal cursor[^:]*: [0-9]*,[0-9]*' | grep -o '[0-9]*,[0-9]*$')
  n=$(echo "$o" | grep -a "^Neighbors of @($me)" | grep -oE "[1-9]:[a-zA-Z@&;:'I]\(" | grep -v "${SKIP:-XXXX}" | head -1)
  if [ -n "$n" ]; then r=$($S keys --compact --raw "F${n:0:1}" 2>&1); echo "F${n:0:1} $(echo "$r" | grep '^07' | cut -c5-70)"
    echo "$r" | grep -q "Really attack" && { $S keys --raw n >/dev/null; echo PEACEFUL; break; }
    echo "$r" | grep -q "ALARM" && { echo ALARM; break; }
  else r=$($S keys --compact s 2>&1); echo "$r" | grep -q ALARM && { echo ALARM; break; }; fi
  $S screen | grep -q '>>' && $S keys --named Enter >/dev/null
done
$S screen --compact | grep -E '^34'
