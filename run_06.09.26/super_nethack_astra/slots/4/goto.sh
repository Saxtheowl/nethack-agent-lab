#!/bin/bash
# goto.sh X Y [n]: travel to X,Y fighting adjacent hostiles on the way (up to n rounds)
cd "$(dirname "$0")"
for i in $(seq "${3:-6}"); do
  pre=$(cd ../.. && python3 scripts/session.py screen --compact | grep -E "^0[1-7]")
  o=$(../../scripts/t "$1" "$2" 2>&1)
  new=$(diff <(echo "$pre") <(echo "$o" | grep -E "^0[1-7]") | grep "^>" )
  echo "$new" | grep -qi "steal\|stole\|seduc\|charm" && { echo "THEFT!"; echo "$o" | grep -E "^0[5-7]"; exit 1; }
  echo "$o" | grep -a "^Map" | grep -q " [nl]@" && { echo "NYMPH/LEPRECHAUN IN VIEW"; echo "$o" | grep -a "^Map"; exit 1; }
  echo "$o" | grep -q "^Neighbors of @($1,$2)" && { echo "ARRIVED $1,$2"; exit 0; }
  f=$(./adjfight.py 'abcdfghijkmopqrstuvwxyzABCDEGHIJKLMNOPQRSTUVWXYZ&;:' 10 2>&1)
  echo "$f" | grep -a "^\[" | tail -2 | cut -c1-90
  echo "$f" | grep -q "STOP" && { echo "$f" | grep STOP; exit 1; }
done
echo "NOT ARRIVED"; echo "$o" | grep -E "^0[5-7]|Neigh" | tail -3
