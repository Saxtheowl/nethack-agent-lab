#!/bin/bash
# new_game_on_worker.sh <slot> <style> <run>: after a death, start the slot's
# next game on miniforum-worker (the PC only keeps the agent). Sets the style,
# run and journal in the worker's slot file; worker_sync brings it back here.
set -euo pipefail
N=$1; STYLE=$2; RUN=$3
R="$(cd "$(dirname "$0")/.." && pwd)"
J=memory/slot$N-run-$RUN.md; [ "$N" = 1 ] && J=memory/run-$RUN.md
S=/tmp/nhstream-4040c750ff9d.sock
SESS=nethack$N; [ "$N" = 1 ] && SESS=nethack
# the PC's finished game: close its dead pane here
tmux -S $S kill-session -t $SESS 2>/dev/null || true
echo worker > "$R/.runtime/where-$N"
rsync -a "$R/.runtime/where-$N" "$R/.runtime/public-feed-$N.json" miniforum-worker:$R/.runtime/ 2>/dev/null || true
ssh -o BatchMode=yes miniforum-worker "cd $R && rm -f .runtime/slot-$N.json && NH_HOST=worker NH_SLOT=$N python3 scripts/session.py start >/dev/null && python3 - <<PY
import json
p='.runtime/slot-$N.json'; d=json.load(open(p))
d.update(style='$STYLE', run=$RUN, journal='$J')
open(p,'w').write(json.dumps(d)); print(d['game_id'])
PY"
rsync -a miniforum-worker:$R/.runtime/slot-$N.json "$R/.runtime/"
echo "slot $N: new game on the worker, style $STYLE, run $RUN, journal $J"
