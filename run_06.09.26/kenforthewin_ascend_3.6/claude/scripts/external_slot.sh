#!/bin/bash
# external_slot.sh <slot> <Name> [style]
# Opens a game slot for an agent that is not Claude (e.g. Codex): un-retires the
# slot, starts a fresh game on miniforum-worker under the player name <Name>
# and records it for the dashboard (style defaults to the lowercase name).
# See doc/agent-externe.md. Example: scripts/external_slot.sh 4 Codex
set -euo pipefail
N=$1; NAME=$2; STYLE=${3:-$(echo "$NAME" | tr 'A-Z' 'a-z')}
R="$(cd "$(dirname "$0")/.." && pwd -P)"
cd "$R"
[[ "$NAME" =~ ^[A-Za-z][A-Za-z0-9]{0,15}$ ]] || { echo "name: letters/digits, max 16"; exit 1; }
# a new slot number (9, 10, ...) gets its folder of wrappers first
[ -x "slots/$N/k" ] || scripts/new_slot.sh "$N"
python3 - "$N" <<'PY'
import json, sys
p = '.runtime/style-plan.json'; d = json.load(open(p))
d['retired'] = [s for s in d.get('retired', []) if s != sys.argv[1]]
d.setdefault('external', {})[sys.argv[1]] = True
open(p, 'w').write(json.dumps(d, indent=1))
PY
J="memory/${STYLE}-run-1.md"
[ -f "$J" ] || printf '# %s — journal (état le plus récent en haut)\n\n## Current state\nURGENT: T1, nouvelle partie.\n\n## Lessons\n' "$NAME" > "$J"
echo worker > .runtime/where-$N
rsync -a .runtime/style-plan.json .runtime/where-$N miniforum-worker:$R/.runtime/
rsync -a "$J" miniforum-worker:$R/memory/
ssh -o BatchMode=yes miniforum-worker "cd $R && rm -f .runtime/slot-$N.json .runtime/explore-$N.json .runtime/hpguard-$N.json && NH_HOST=worker NH_SLOT=$N NH_PLAYER=$NAME python3 scripts/session.py start >/dev/null && python3 - <<PY
import json
p='.runtime/slot-$N.json'; d=json.load(open(p))
d.update(style='$STYLE', run=1, journal='$J', external=True)
open(p,'w').write(json.dumps(d)); print(d['game_id'])
PY"
rsync -a miniforum-worker:$R/.runtime/slot-$N.json .runtime/
echo "slot $N: new game for $NAME on the worker (style $STYLE, journal $J)"
