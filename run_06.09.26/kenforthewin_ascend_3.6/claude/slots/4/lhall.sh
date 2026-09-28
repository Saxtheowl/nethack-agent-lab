#!/bin/bash
# lhall.sh N : fight adjacent l (and others) else wait one turn; stop on HP<60% or theft of non-gold or n adjacent
cd "$(dirname "$0")/../.."
S="python3 scripts/session.py"
for i in $(seq "${1:-30}"); do
  f=$(cd slots/4 && ./adjfight.py 'abcdfghijklmopqrstuvwxyzABCDEGHIJKLMNOPQRSTUVWXYZ&;:' 6 2>&1)
  echo "$f" | grep -a "^\[" | tail -1 | cut -c1-90
  echo "$f" | grep -q "STOP" && { echo "$f" | grep STOP; break; }
  if echo "$f" | grep -q "no adjacent target"; then
    o=$($S keys s --compact 2>&1)
    echo "$o" | grep -q "ALARM\|refused" && { echo REFUSED; break; }
    hp=$(echo "$o" | grep -o 'HP:[0-9]*([0-9]*)' | head -1); c=${hp#HP:}; c=${c%%(*}; m=${hp#*(}; m=${m%)}
    [ $((c*10)) -lt $((m*6)) ] && { echo "HP low $c"; break; }
    echo "$o" | grep -a "^Map" | grep -q " l@" || { echo "no l in view"; }
  fi
done
$S screen --compact | grep -E "^34|^Map"
