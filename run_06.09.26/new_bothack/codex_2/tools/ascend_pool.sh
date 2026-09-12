#!/bin/bash
# Play real games until one ascends, keeping every slot busy.
#
#   tools/ascend_pool.sh OUT SLOTS [NAME_PREFIX]
#
# Why not tools/ascend_batch.sh: that one runs in waves and waits for the whole
# wave, so a single farming game - which can run three hours - leaves the other
# slots idle for hours.  Measured: one game held five of six slots idle.  This
# starts a new game the moment a slot frees, which is what the goal needs, since
# an ascension is a rare event and rare events want volume.
#
# Stops on the first `death=ascended` in NetHack's own xlogfile - written by the
# game, not by the bot or by this harness.
#
# NAME_PREFIX gives each pool its own NetHack user names, so two pools can share
# a machine without deleting each other's level files in var/.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?outdir}"; SLOTS="${2:-6}"; PREFIX="${3:-pool}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
mkdir -p "$OUT"
VAR="$ROOT/upstream/nh343/var"
XLOG="$VAR/xlogfile"

echo "== pool: $SLOTS slots, names ${PREFIX}1..${PREFIX}$SLOTS, no cap"
echo "   port commit $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo ?)"
SEED_BASE="${SEED_BASE:-20000}"
echo "   seed base $SEED_BASE"

play () {                        # $1 = game index, $2 = slot
  local i="$1" slot="$2"
  local d="$OUT/game$i" name="$PREFIX$slot"
  mkdir -p "$d/home"
  rm -f "$VAR"/*"$name"* "$VAR"/save/*"$name"* 2>/dev/null
  local start; start=$(date +%s)
  BOTHACK_HOME="$d/home" BOTHACK_USER="$name" \
    python3 -m pybothack.main "$ROOT/config/play-config.edn" \
      --seed "$((SEED_BASE + i))" --log INFO \
      ${WATCHDOG:+--watchdog "$WATCHDOG"} \
      --logfile "$d/run.log" --ttyrec "$d/game.ttyrec" \
      > "$d/stdout.log" 2>&1
  echo $(( $(date +%s) - start )) > "$d/wall_seconds"
  echo "$name" > "$d/player"
  for p in $(pgrep -x nethack.343-nao || true); do
    tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | grep -q -- "-u $name" \
      && kill "$p" 2>/dev/null
  done
  printf '   game %-4s %-9s %s\n' "$i" "$name" \
      "$(tail -1 "$d/run.log" 2>/dev/null | sed 's/.*final state: //')"
}

declare -A busy=()
next=1
while true; do
  # start games until every slot is busy
  for slot in $(seq 1 "$SLOTS"); do
    pid="${busy[$slot]:-}"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      continue
    fi
    play "$next" "$slot" &
    busy[$slot]=$!
    next=$((next + 1))
    sleep 1
  done
  sleep 20
  if grep -q "death=ascended" "$XLOG" 2>/dev/null; then
    echo "== ASCENSION  $(date -Is)"
    grep "death=ascended" "$XLOG" | tail -3
    break
  fi
  # a periodic tally so progress is visible without reading every log
  done_n=$(ls -d "$OUT"/game*/wall_seconds 2>/dev/null | wc -l)
  if [ $((done_n % 10)) -eq 0 ] && [ "$done_n" -gt 0 ] && \
     [ ! -f "$OUT/.tally$done_n" ]; then
    : > "$OUT/.tally$done_n"
    python3 "$ROOT/tools/ascend_summary.py" "$OUT" 2>/dev/null | tail -4 \
        | sed 's/^/   /'
  fi
done
