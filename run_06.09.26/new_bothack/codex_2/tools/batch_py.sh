#!/bin/bash
# Run N games of the Python port (no wizard mode, no human intervention).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
N="${1:-5}"; LIMIT="${2:-900}"; TAG="${3:-py}"
mkdir -p "$ROOT/artifacts/games/$TAG"
for i in $(seq 1 "$N"); do
  d="$ROOT/artifacts/games/$TAG/game$i"
  mkdir -p "$d"
  rm -f "$ROOT/upstream/nh343/var/"*claudebot* \
        "$ROOT/upstream/nh343/var/save/"*claudebot* 2>/dev/null
  echo "=== $TAG game $i (limit ${LIMIT}s) $(date -Is)"
  BOTHACK_HOME="$d/home" BOTHACK_USER=claudebot \
  timeout $((LIMIT + 60)) python3 -m pybothack.main "$ROOT/config/shell-config.edn" \
      --seed "$((1000 + i))" --max-seconds "$LIMIT" --log INFO \
      --logfile "$d/run.log" --ttyrec "$d/game.ttyrec" > "$d/stdout.log" 2>&1
  tail -1 "$d/run.log" | sed 's/^/    /'
done
