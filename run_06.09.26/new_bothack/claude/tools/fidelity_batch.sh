#!/bin/bash
# Record N games of the original with the pinned protocol, replay each into the
# port, and aggregate explicit verdicts into a manifest.
#
#   BOTHACK_SRC=… JDK8_HOME=… LEIN_DIR=… tools/fidelity_batch.sh OUT 6 1 3600
#
# PAR defaults to 1: each game is a JVM plus a NetHack, and this machine runs
# out of memory before it runs out of cores.  Recordings are skipped when a
# usable tap.log is already there, so the script is re-runnable.
#
# The aggregate that matters is the count of PASS_COMPLETE - a whole game
# reproduced first byte to last.  Every other status is reported by name, never
# folded into "not identical": a TRUNCATED recording cannot yield
# PASS_COMPLETE however faithful the port is, and counting it as a failure
# would understate fidelity exactly as counting it as a pass would overstate it.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?outdir}"; N="${2:-6}"; PAR="${3:-1}"; SECS="${4:-3600}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
BASE_SEED="${BASE_SEED:-40000}"
mkdir -p "$OUT"

echo "== recording $N games of the original, $PAR at a time, cap ${SECS}s"
i=1
while [ "$i" -le "$N" ]; do
  started=0
  for slot in $(seq 1 "$PAR"); do
    [ "$i" -gt "$N" ] && break
    seed=$((BASE_SEED + i))
    d="$OUT/seed$seed"
    if [ -s "$d/tap.log" ]; then
      echo "   seed $seed: recording already present, skipped"
    else
      echo "   seed $seed (slot $slot) $(date -Is)"
      "$ROOT/tools/record_orig.sh" "$seed" "$d" "bot$slot" "$SECS" \
          > "$OUT/rec_$seed.log" 2>&1 &
      started=$((started + 1))
    fi
    i=$((i + 1))
  done
  [ "$started" -gt 0 ] && wait
done

echo
echo "== judging each recording, then replaying it into the port"
for d in "$OUT"/seed*; do
  [ -d "$d" ] || continue
  seed="$(basename "$d")"; seed="${seed#seed}"
  if [ ! -s "$d/tap.log" ]; then
    echo "   $seed: no capture"
    continue
  fi
  # recording verdict first: GAME or TRUNCATED, plus the xlogfile correlation
  python3 "$ROOT/tools/recording_verdict.py" "$d/tap.log" "$seed" \
      "$(grep -o 'USER=[^ ]*' "$d/nh.sh" | head -1 | cut -d= -f2)" \
      "$ROOT/upstream/nh343/var/xlogfile" "$d/recording.json" \
      > "$d/recording.txt" 2>&1 || true
  "$ROOT/tools/replay_port.sh" "$d" "$d/replay" > "$d/replay.txt" 2>&1 || true
done

echo
echo "== manifest"
python3 "$ROOT/tools/fidelity_manifest.py" "$OUT" | tee "$OUT/summary.txt"
