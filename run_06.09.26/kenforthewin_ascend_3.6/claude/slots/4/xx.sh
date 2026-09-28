#!/bin/bash
# xx.sh N : up to N xa rounds; continue only after routine rounds (budget / HP-loss-with-fight-kill)
cd "$(dirname "$0")"
for i in $(seq "${1:-2}"); do
  out=$(./xa.sh 2>&1)
  echo "$out" | tail -4
  r=$(echo "$out" | grep -a "^round")
  echo "$r" | grep -q "HP low\|hunger\|nymph\|stairs\|frontier\|locked\|door\|trap\|STOP" && break
  echo "$out" | grep -q "STOP\|More" && break
  # monsters listed but not killed -> stop
  if echo "$r" | grep -q monsters; then echo "$out" | grep -q "kill\|destroy" || break; fi
  hp=$(echo "$out" | grep -ao 'HP:[0-9]*([0-9]*)' | tail -1); c=${hp#HP:}; c=${c%%(*}; m=${hp#*(}; m=${m%)}
  [ -n "$c" ] && [ $((c*10)) -lt $((m*7)) ] && { echo "HP<70% stop"; break; }
done
