#!/bin/bash
# digeast.sh DIR N : dig with pick-axe in DIR then step, N times; stops on monster/HP loss/non-dig message.
cd "$(dirname "$0")/../.."; export NH_SLOT=4; S="python3 scripts/session.py"
d=$1
for i in $(seq $2); do
  o=$($S keys --compact --raw ao 2>&1)
  echo "$o" | grep -aq "In what direction" || { echo "no dir prompt"; echo "$o" | grep -a "^07"; break; }
  o=$($S keys --compact --raw $d 2>&1)
  echo "$o" | grep -a "^07" | cut -c1-80
  o=$($S keys --compact --raw $d 2>&1)
  echo "$o" | grep -a "^Neigh" | cut -c1-120
  echo "$o" | grep -aqE "hits|bites|More" && { echo STOP; break; }
done
