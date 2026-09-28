#!/bin/bash
# slots/4/elb.sh : engrave Elbereth in the dust (fingers), replacing any engraving; then read it back.
cd "$(dirname "$0")/../.."
export NH_SLOT=4
S="python3 scripts/session.py"
$S keys --raw E- --settle .5 >/dev/null
last() { $S screen --compact | grep -E '^0[1-9] ' | tail -1; }
sleep .5
last | grep -q 'add to the current' && $S keys --raw n --settle .5 >/dev/null
last | grep -q 'write in the dust here' || { echo "unexpected prompt: $(last)"; exit 1; }
$S keys --raw Elbereth >/dev/null; $S keys --named Enter --settle 1 >/dev/null
for i in 1 2 3; do $S screen | grep -q '>>\|--More--' && $S keys --named Enter --settle .3 >/dev/null; done
$S keys : --settle .5 >/dev/null
if $S screen | grep -q 'You read: "Elbereth"'; then echo "ELBERETH OK"; else echo "ELBERETH NOT CONFIRMED"; fi
$S keys --named Escape --settle .2 >/dev/null
$S screen --compact | grep -E '^0[5-7] |^34'
