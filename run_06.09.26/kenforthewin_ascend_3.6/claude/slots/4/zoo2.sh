#!/bin/bash
# one action: attack monster in the doorway (50,25) else search 1 turn. prints status.
cd "$(dirname "$0")/../.."
export NH_SLOT=4
S="python3 scripts/session.py"
o=$($S screen --compact)
m=$(echo "$o" | grep -oE ' [^ ]@50,25' | head -1)
if [[ -n "$m" && "$m" != " -@50,25" && "$m" != " +@50,25" && "$m" != " ·@50,25" ]]; then
  out=$($S keys --compact --raw F4)
else
  out=$($S keys --compact --raw s)
fi
echo "$out" | grep -E '^0[5-7] ' | cut -c5-85
echo "$out" | grep -E '^34 ' | cut -c5-80
echo "door:$m"; echo "$out" | grep -oE 'Neighbors.*'
