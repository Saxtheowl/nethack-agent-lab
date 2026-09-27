#!/bin/bash
# rest_elb.sh N TARGET : search 5 turns at a time up to N times; stop on HP loss, bad status, attack messages, or HP>=TARGET
cd "$(dirname "$0")/../.."
export NH_SLOT=4
prev=$(python3 scripts/session.py screen --compact | grep -o 'HP:[0-9]*' | head -1 | cut -d: -f2)
for i in $(seq $1); do
  o=$(python3 scripts/session.py keys --compact --raw n10s); h=$(echo "$o" | grep -o 'HP:[0-9]*' | head -1 | cut -d: -f2)
  st=$(echo "$o" | grep -E '^34 ')
  if [[ -z "$h" || $h -lt $prev ]] || echo "$st" | grep -qE "Stone|Weak|Hungry|Blind|Conf|Stun|Ill" || echo "$o" | grep -E '^0[6-7] ' | grep -qiE "stole|slowing|hits|bites|touch|--More|>>"; then echo "$o" | grep -E "^0[4-7] |^34 |Neighbors"; echo STOP; exit 1; fi
  prev=$h; [[ $h -ge $2 ]] && break
done
echo "HP $h $(echo "$st" | grep -o 'T:[0-9]*')"
