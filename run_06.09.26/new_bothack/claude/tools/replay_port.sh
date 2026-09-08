#!/bin/bash
# Replay a recorded original game into the port and return an explicit verdict.
#
# No NetHack and no JVM: this is the cheap, repeatable half, so it can be
# re-run after every fix without re-recording.  The exit code is the verdict's
# (0 only for PASS_COMPLETE / PASS_CAPTURE); results go to a fresh directory so
# a stale report can never be mistaken for this run's.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="${1:?recording dir}"
case "$DIR" in /*) ;; *) DIR="$PWD/$DIR" ;; esac
OUT="${2:-$DIR/replay_$(date +%Y%m%d_%H%M%S)_$$}"
mkdir -p "$OUT"

python3 "$ROOT/tools/replay_compare.py" "$DIR/tap.log" \
    --seed "${BOTHACK_SEED:-12345}" \
    --actions-out "$OUT/port_actions.txt" \
    --keys-out "$OUT/port_keys.bin" \
    --verdict-out "$OUT/verdict.json" \
    --report "$OUT/report.txt" > "$OUT/stdout.txt" 2>&1
status=$?
if [ -s "$OUT/report.txt" ]; then
  sed -n '1,8p' "$OUT/report.txt"
else
  echo "status: HARNESS_ERROR (no report produced)"
  tail -5 "$OUT/stdout.txt" 2>/dev/null
fi
echo "   -> $OUT"
exit $status
