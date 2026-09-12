#!/bin/bash
# Full comparison pipeline:
#   1. record a real game of the ORIGINAL bot (pty tap)
#   2. replay that recording into the ORIGINAL (captures its keystrokes)
#   3. replay it into the PORT and compare keystrokes + actions
#
#   BOTHACK_SRC=... JDK8_HOME=... LEIN_DIR=... ./tools/compare_pipeline.sh OUT 300
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/artifacts/compare_$(date +%s)}"
# the sub-scripts cd into the Clojure project, so OUT must be absolute
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
SECS="${2:-300}"
mkdir -p "$OUT"

echo "== 1/3 recording a game of the original ($SECS s)"
SECONDS_LIMIT="$SECS" OUT="$OUT/record" BOTHACK_SEED="${BOTHACK_SEED:-12345}" \
    "$ROOT/tools/run_orig.sh"

echo "== 2/3 replaying it into the original"
TAP="$OUT/record/pty_tap.log" OUT="$OUT/orig_replay" \
    SECONDS_LIMIT="$((SECS * 3))" BOTHACK_SEED="${BOTHACK_SEED:-12345}" \
    "$ROOT/tools/run_orig_replay.sh"

echo "== 3/3 replaying it into the port"
python3 "$ROOT/tools/replay_compare.py" "$OUT/record/pty_tap.log" \
    --seed "${BOTHACK_SEED:-12345}" \
    --expected-keys "$OUT/orig_replay/orig_keys.bin" \
    --actions-out "$OUT/port_actions.txt" \
    --keys-out "$OUT/port_keys.bin" \
    --report "$OUT/report.txt" || true
sed -n '/Performing action/,$p' /dev/null   # noop
grep -n "Performing action" "$OUT/orig_replay/bothack.log" > /dev/null || true
python3 "$ROOT/tools/compare_actions.py" "$OUT/orig_replay/bothack.log" \
    "$OUT/port_actions.txt" --max-diffs 5 | tee -a "$OUT/report.txt"
echo
cat "$OUT/report.txt"
