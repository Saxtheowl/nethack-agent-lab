#!/bin/bash
# auto.sh N : up to N cycles of (explore 2 rounds; fight an adjacent safe hostile). Stops on anything unusual.
cd "$(dirname "$0")/../.."
export NH_SLOT=4
S="python3 scripts/session.py"
DANGER='nymph|leprechaun|homunculus|giant bat|dwarf|hill orc|floating eye|cockatrice|chickatrice|gas spore|peaceful|shopkeeper|watchman|priest|mind flayer|soldier|green slime|\blich\b|nurse|were'
for c in $(seq ${1:-5}); do
  o=$($S screen --compact)
  hp=$(echo "$o" | grep -oE 'HP:[0-9]+\([0-9]+\)' | head -1); cur=${hp#HP:}; cur=${cur%%(*}; mx=${hp#*(}; mx=${mx%)}
  if echo "$o" | grep -E '^34 ' | grep -qE 'Hungry|Weak|Faint|Blind|Conf|Stun|Ill|Stone|Slime'; then echo "STATUS: $(echo "$o" | grep -E '^34 ')"; exit 1; fi
  (( cur*10 < mx*6 )) && { echo "LOW HP $cur/$mx"; exit 1; }
  n=$(echo "$o" | grep -oE 'Neighbors of @.*' | head -1)
  adj=$(echo "$n" | grep -oE '[1-9]:[A-Za-z@&;:'"'"'][(][0-9]+,[0-9]+[)]' | grep -vE ':[a-z]?(blank)' | head -1)
  if [[ -n "$adj" ]]; then
    d=${adj%%:*}; xy=$(echo "$adj" | grep -oE '[0-9]+,[0-9]+'); x=${xy%,*}; y=${xy#*,}
    name=$(slots/4/look $x $y | tail -1)
    echo "adjacent: $name"
    if echo "$name" | grep -q "peaceful" && ! echo "$name" | grep -qiE "shopkeeper|watch|priest"; then echo "peaceful, ignore"; else
    echo "$name" | grep -qiE "$DANGER" && { echo "DANGER/peaceful -> stop"; exit 2; }
    for k in 1 2 3 4 5; do
      r=$($S keys --compact --raw F$d); m=$(echo "$r" | grep -E '^0[67] ' | tail -1 | cut -c5-85)
      h=$(echo "$r" | grep -oE 'HP:[0-9]+' | head -1 | cut -d: -f2); echo "  $m HP$h"
      echo "$r" | grep -E '^0[5-7] ' | grep -qiE 'stole|steal|feel weak|deathly|--More|Really|slowing|You are hit by|engulf' && { echo "EVENT"; exit 3; }
      echo "$m" | grep -qE 'kill|destroy|thin air|You miss wildly' && break
      (( h*10 < mx*6 )) && { echo "LOW HP in fight"; exit 1; }
    done
    continue
    fi
  fi
  x=$(timeout 90 slots/4/xp3 2 2>&1)
  st=$(echo "$x" | grep -oE 'explore stop: .*' | tail -1); echo "xp: $st"
  echo "$st" | grep -qE 'no reachable|no frontier|nothing' && { echo "EXPLORED"; exit 4; }
done
$S screen --compact | grep -E '^34 |Neighbors'
