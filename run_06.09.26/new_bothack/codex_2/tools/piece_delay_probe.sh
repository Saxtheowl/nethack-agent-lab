#!/bin/bash
# Is a smaller PTY_TAP_PIECE_DELAY still safe?
#
#   BOTHACK_SRC=… JDK8_HOME=… LEIN_DIR=… \
#     tools/piece_delay_probe.sh OUT SEED "0.05 0.02 0.01" [SECS]
#
# The delay is the dominant cost of a recording campaign - 78 % of one measured
# recording's wall clock was sleeping in it - so it is worth knowing how low it
# can go.  What it buys is *not* a reproducible game: a capture is
# self-contained and the replay feeds the port exactly the pieces recorded.  It
# buys **one piece per JVM read**, which is what makes the recorded piece
# boundaries equal to the frames the original reasoned about.  Too small, and
# two pieces land in one read: the original saw one redraw where the recording
# holds two, and the replay then shows the port a frame the original never had.
#
# So the verdict is the *replay* verdict, not an agreement between two runs.
# PASS_COMPLETE at a delay means that delay is safe; a divergence means the
# reader coalesced and the delay is too fast.
#
# Run it under the load the campaign will actually use: coalescing is a
# scheduling property, and a delay that survives on an idle box can fail with
# several slots on one worker.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?outdir}"; SEED="${2:?seed}"; DELAYS="${3:-0.05 0.02}"; SECS="${4:-1800}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
mkdir -p "$OUT"

echo "== piece-delay probe, seed $SEED, cap ${SECS}s, delays: $DELAYS"
nproc | sed 's/^/   cores: /'
uptime | sed 's/^/   load: /'

for d in $DELAYS; do
  tag="delay_$d"
  dir="$OUT/$tag"
  if [ ! -s "$dir/tap.log" ]; then
    echo
    echo "-- recording at PTY_TAP_PIECE_DELAY=$d  $(date -Is)"
    start=$(date +%s)
    PTY_TAP_PIECE_DELAY="$d" \
      "$ROOT/tools/record_orig.sh" "$SEED" "$dir" "probe" "$SECS" \
      > "$OUT/rec_$tag.log" 2>&1
    echo $(( $(date +%s) - start )) > "$dir/wall_seconds"
    echo "   wall clock: $(cat "$dir/wall_seconds")s"
  else
    echo "-- $tag already recorded, skipped"
  fi
  python3 "$ROOT/tools/recording_verdict.py" "$dir/tap.log" "$SEED" probe \
      "$ROOT/upstream/nh343/var/xlogfile" "$dir/recording.json" \
      > "$dir/recording.txt" 2>&1 || true
  head -1 "$dir/recording.txt" | sed 's/^/   /'
  echo "-- replaying into the port"
  "$ROOT/tools/replay_port.sh" "$dir" "$dir/replay" 2>&1 | sed -n '1,3p;$p' \
      | sed 's/^/   /'
done

echo
echo "== summary (the replay verdict is what decides)"
printf '   %-12s %-10s %-10s %-16s %s\n' delay wall_s keystrokes replay note
for d in $DELAYS; do
  dir="$OUT/delay_$d"
  keys=$(python3 - "$dir/recording.json" <<'PY'
import json
import sys
try:
    print(json.load(open(sys.argv[1])).get('keystrokes', '-'))
except Exception:
    print('-')
PY
)
  status=$(python3 - "$dir/replay/verdict.json" <<'PY'
import json
import sys
try:
    print(json.load(open(sys.argv[1])).get('status', '-'))
except Exception:
    print('-')
PY
)
  wall=$(cat "$dir/wall_seconds" 2>/dev/null)
  note=""
  case "$status" in
    PASS_COMPLETE|PASS_CAPTURE) note="safe at this delay" ;;
    DIVERGENCE) note="TOO FAST: pieces coalesced, or a real port bug" ;;
    PREFIX_ONLY) note="capture cut short; inconclusive, raise SECS" ;;
  esac
  printf '   %-12s %-10s %-10s %-16s %s\n' "$d" "${wall:-?}" "$keys" "$status" "$note"
done
