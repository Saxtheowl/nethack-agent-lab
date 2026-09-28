#!/bin/bash
# xloop.sh N [IGNORE_LETTERS]: up to N xa.sh rounds; stop on monsters not in IGNORE, HP low/loss, hunger, level change, no frontier.
cd "$(dirname "$0")"
ig="${2:-Ai}"
for i in $(seq "${1:-8}"); do
  o=$(./xa.sh 2>&1)
  echo "$o" | grep -aE 'round|^34' | cut -c1-160
  m=$(echo "$o" | grep -aoE 'monsters.*' | sed "s/[$ig]@[0-9,]*//g" | grep -E '[A-Za-z&;:]@')
  [ -n "$m" ] && { echo "$m"; break; }
  echo "$o" | grep -aqE 'HP low|no reachable|STOP|HP loss|level changed|round 1:  $|hunger|ALARM|nymph' && break
done
