#!/bin/bash
# new_slot.sh <N>: create the folder slots/N/ of a new game slot (any number):
# the standard command wrappers (v, k, t, look, inv, say, w, ...) copied from
# slots/1 with NH_SLOT set to N, here and on miniforum-worker. The recorder,
# the dashboard and the sync pick the slot up by themselves (they list
# slots/*/). Called by external_slot.sh; harmless if the slot already exists.
set -euo pipefail
N=$1
[[ "$N" =~ ^[1-9][0-9]*$ ]] || { echo "slot: a number" >&2; exit 1; }
R="$(cd "$(dirname "$0")/.." && pwd -P)"
cd "$R"
mkdir -p "slots/$N"
for f in slots/1/*; do
  # a wrapper: a few lines, exports NH_SLOT=1 and execs a shared script
  [ -f "$f" ] && [ "$(wc -l < "$f")" -le 4 ] && grep -q '^export NH_SLOT=1$' "$f" \
    && grep -q 'scripts/slot\(run\|w\)' "$f" || continue
  t="slots/$N/$(basename "$f")"
  [ -e "$t" ] || { sed "s/^export NH_SLOT=1$/export NH_SLOT=$N/" "$f" > "$t"; chmod +x "$t"; }
done
rsync -a "slots/$N/" "miniforum-worker:$R/slots/$N/"
echo "slots/$N ready: $(ls "slots/$N" | tr '\n' ' ')"
