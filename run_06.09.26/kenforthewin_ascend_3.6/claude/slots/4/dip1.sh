#!/bin/bash
# one dip of item a into fountain; prints resulting message lines
cd "$(dirname "$0")/../.."
S="python3 scripts/session.py"
$S keys --raw '#dip' >/dev/null; $S keys --named Enter >/dev/null
$S keys --raw a >/dev/null
$S screen --compact | grep -q "into the fountain" || { echo "NO FOUNTAIN PROMPT"; $S keys --named Escape >/dev/null; exit 1; }
$S keys --raw y --compact | grep -E "^0[5-7]|^34"
