#!/bin/bash
# Play real games in batches until one of them ascends.
#
#   tools/ascend_forever.sh OUT PAR [GAMES_PER_BATCH]
#
# The mission's own test is an ascension without wizard mode or human
# intervention, and it is a rare event: the original's README records that it
# first won only after pudding farming was implemented, and gives no rate.  So
# the only honest approach is volume - keep playing and let the xlogfile say
# when it happens.
#
# Stops on the first `death=ascended` in NetHack's own xlogfile, which is
# written by the game rather than by the bot or by this harness.  Also writes a
# running tally so progress is visible without reading every game log.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?outdir}"; PAR="${2:-6}"; N="${3:-12}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
mkdir -p "$OUT"
XLOG="$ROOT/upstream/nh343/var/xlogfile"

batch=0
while true; do
  batch=$((batch + 1))
  d="$OUT/batch$batch"
  echo "== batch $batch  $(date -Is)"
  WATCHDOG="${WATCHDOG:-120}" "$ROOT/tools/ascend_batch.sh" "$d" "$N" "$PAR" 0 \
      > "$OUT/batch$batch.log" 2>&1
  python3 "$ROOT/tools/ascend_summary.py" "$d" 2>/dev/null | tail -5 \
      | sed 's/^/   /'
  # the tally, across every batch so far
  python3 - "$OUT" <<'PY' | sed 's/^/   /'
import glob
import json
import os
import sys
best = (0, None)
deep = (0, None)
games = 0
asc = 0
for f in sorted(glob.glob(os.path.join(sys.argv[1], 'batch*', 'summary.json'))):
    for g in json.load(open(f)):
        games += 1
        if g.get('ascended'):
            asc += 1
        if (g.get('score') or 0) > best[0]:
            best = (g['score'], g['game'])
        try:
            lvl = int(str(g.get('dlvl', '')).split(':')[-1])
        except ValueError:
            lvl = 0
        if lvl > deep[0]:
            deep = (lvl, g['game'])
print('TALLY games=%d ascensions=%d best_score=%d(%s) deepest=Dlvl%d(%s)'
      % (games, asc, best[0], best[1], deep[0], deep[1]))
PY
  if grep -q "death=ascended" "$XLOG" 2>/dev/null; then
    echo "== ASCENSION FOUND  $(date -Is)"
    grep "death=ascended" "$XLOG" | tail -3
    break
  fi
done
