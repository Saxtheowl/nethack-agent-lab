#!/bin/bash
# slots/4/dip.sh : ONE dip of item a into the fountain under me; prints the result.
cd "$(dirname "$0")/../.."
export NH_SLOT=4
S="python3 scripts/session.py"
$S keys --raw '#dip' --settle .4 >/dev/null
$S keys --named Enter --settle .5 >/dev/null
$S screen | grep -q 'What do you want to dip' || { echo "no dip prompt"; $S keys --named Escape >/dev/null; exit 1; }
$S keys --raw a --settle .5 >/dev/null
$S screen | grep -q 'into the fountain' || { echo "no fountain prompt"; $S keys --named Escape >/dev/null; exit 1; }
$S keys --raw y --settle 1 >/dev/null
for i in 1 2 3; do $S screen | grep -q -- '--More--\|>>' && $S keys --named Enter --settle .4 >/dev/null; done
$S screen --compact | grep -E '^0[4-7] |^34|^Map'
