#!/bin/bash
# rest1.sh N [targetPct]: single 's' turns with HP check each; stop on HP drop, new monster letter adjacent, hunger, or target reached
cd "$(dirname "$0")/../.."
S="python3 scripts/session.py"
tgt=${2:-90}; prev=""
for i in $(seq "${1:-50}"); do
  o=$($S keys s --compact 2>&1)
  echo "$o" | grep -q "HP ALARM\|refused" && { echo "REFUSED"; break; }
  hp=$(echo "$o" | grep -o 'HP:[0-9]*([0-9]*)' | head -1); c=${hp#HP:}; c=${c%%(*}; m=${hp#*(}; m=${m%)}
  [ -n "$prev" ] && [ "$c" -lt "$prev" ] && { echo "HP DROP $c"; break; }
  echo "$o" | grep -qE 'Hungry|Weak|Faint' && { echo "HUNGER"; break; }
  n=$(echo "$o" | grep -a "^Neighbors" | head -1 | grep -oE ':[a-zA-Z&;:@]\(' | head -1)
  n=$(echo "$n" | cut -c2 | tr -d "${RIGNORE:-}"); [ -n "$n" ] && { echo "NEIGHBOR $n"; break; }
  echo "$o" | grep -q -- "--More--\|>>" && { echo "MORE"; break; }
  prev=$c
  [ $((c*100)) -ge $((m*tgt)) ] && { echo "TARGET $c/$m"; break; }
done
echo "HP $c/$m"
