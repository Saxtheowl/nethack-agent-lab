#!/bin/bash
# Record games of the original on one worker, isolated so several can run at
# once without spoiling each other.
#
#   tools/vast/worker.sh OUT FIRST_SEED N SECS [PAR]
#
# Isolation, and why each part is needed:
#   * one NetHack user name per slot - the lock and level files in var/ are
#     named after it, and two games sharing a name delete each other's levels
#     (that collision destroyed a local run before it was found);
#   * one clean var/ per *campaign*, snapshotted before the first game.  var/ is
#     compiled into the binary (VAR_PLAYGROUND), so slots on one worker share
#     it; what keeps them from colliding is the per-slot name, and what keeps
#     the campaign reproducible is starting from a known-empty var/.  Bones,
#     logfile and record are shared state - a campaign that starts from someone
#     else's var/ is not a clean measurement;
#   * never kill by binary name.  `pkill nethack.343-nao` on a shared worker
#     kills other slots' games; each slot only ever kills its own pid.
#
# Concurrency does *not* invalidate a recording: a capture is a self-contained
# reference, and replaying it needs no NetHack and no JVM.  What concurrency
# costs is cross-campaign comparability - a loaded machine stops agreeing with
# its own earlier runs (docs/TESTS.md).  So: run games in parallel to buy
# coverage, and never compare two campaigns' captures with each other.
set -u
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="${1:?outdir}"; FIRST="${2:?first seed}"; N="${3:?count}"
SECS="${4:-7200}"; PAR="${5:-2}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
mkdir -p "$OUT"

: "${BOTHACK_SRC:?set BOTHACK_SRC}"
: "${JDK8_HOME:?set JDK8_HOME}"
: "${LEIN_DIR:?set LEIN_DIR}"

echo "== worker $(hostname) recording $N game(s) from seed $FIRST, $PAR at a time, cap ${SECS}s"
echo "   port commit $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
nproc; free -m | head -2

# one clean var/ for the campaign, with its initial state recorded next to the
# captures so a later reader knows what the games started from
VAR="$ROOT/upstream/nh343/var"
if [ ! -s "$OUT/var_initial.txt" ]; then
  rm -f "$VAR"/1000* "$VAR"/*vast* "$VAR"/bon* "$VAR"/save/* 2>/dev/null || true
  : > "$VAR/logfile"; : > "$VAR/record"; : > "$VAR/xlogfile"
  ( cd "$VAR" && ls -la && echo '--- md5' && md5sum * 2>/dev/null ) \
      > "$OUT/var_initial.txt"
  echo "   var/ cleaned; initial state in $OUT/var_initial.txt"
fi

i=0
while [ "$i" -lt "$N" ]; do
  started=0
  for slot in $(seq 1 "$PAR"); do
    [ "$i" -ge "$N" ] && break
    seed=$((FIRST + i))
    d="$OUT/seed$seed"
    if [ -s "$d/tap.log" ]; then
      echo "   seed $seed already recorded, skipped"
    else
      echo "   seed $seed slot $slot $(date -Is)"
      ( "$ROOT/tools/record_orig.sh" "$seed" "$d" "vast$slot" "$SECS" \
        > "$OUT/rec_$seed.log" 2>&1
        python3 "$ROOT/tools/recording_verdict.py" "$d/tap.log" "$seed" \
            "vast$slot" "$VAR/xlogfile" "$d/recording.json" \
            > "$d/recording.txt" 2>&1 || true ) &
      started=$((started + 1))
    fi
    i=$((i + 1))
  done
  [ "$started" -gt 0 ] && wait
done

echo
echo "== recordings"
for d in "$OUT"/seed*; do
  [ -d "$d" ] || continue
  printf '   %-12s %s\n' "$(basename "$d")" \
      "$(head -1 "$d/recording.txt" 2>/dev/null || echo 'no verdict')"
done
