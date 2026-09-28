#!/bin/bash
# gold.sh : visit visible $ in box x1-x2,y1-y2 and pick up gold. Stops on HP loss or adjacent hostile (non-F).
cd "$(dirname "$0")/../.."
export NH_SLOT=4
S="python3 scripts/session.py"
SKIP=""
for n in $(seq 25); do
  o=$($S screen --compact)
  hp=$(echo "$o" | grep -o 'HP:[0-9]*' | head -1 | cut -d: -f2)
  pos=$(echo "$o" | python3 slots/4/nearest.py '$' $1 $2 $3 $4 "$SKIP")
  [[ -z "$pos" ]] && { echo "no more gold"; break; }
  x=${pos%,*}; y=${pos#*,}
  r=$(slots/4/go $x $y)
  c=$($S screen --compact | grep -oE 'Terminal cursor[^:]*: [0-9]+,[0-9]+' | grep -oE '[0-9]+,[0-9]+$')
  [[ "$c" != "$x,$y" ]] && { echo "go stopped at $c (target $x,$y)"; SKIP="$SKIP $x,$y"; continue; }
  p=$($S keys --compact --raw ',')
  if echo "$p" | grep -q 'Pick up what'; then $S keys --raw '$' >/dev/null; p=$($S keys --compact --named Enter); fi
  echo "$p" | grep -E '^07 ' | cut -c5-80
  h=$(echo "$p" | grep -o 'HP:[0-9]*' | head -1 | cut -d: -f2)
  [[ -n "$h" && $h -lt $hp ]] && { echo "HP loss"; break; }
done
