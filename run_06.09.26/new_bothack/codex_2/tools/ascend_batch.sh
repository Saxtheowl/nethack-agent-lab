#!/bin/bash
# Play real games with the port, in parallel, until each one ends by itself.
#
#   tools/ascend_batch.sh OUT N [PAR] [MAX_SECONDS]
#
# This is the test the mission actually asks for: no wizard mode, no human
# intervention, run until the game ends.  It is also the cheapest test we have -
# the port needs NetHack and Python, no JVM, ~100 MB per game, and it plays at
# about 15.7 game turns per second (measured), so a whole game is tens of
# minutes rather than the two hours a *recording* of the original takes.  The
# piece delay that makes recordings deterministic does not apply here: nothing
# is being recorded for replay, so the bot runs at full speed.
#
# Isolation, and why each part is needed:
#   * one NetHack user name per slot - lock and level files in var/ are named
#     after it, and two games sharing a name delete each other's levels;
#   * one HOME per slot, so ttyrecs and dumplogs do not collide;
#   * never kill by binary name: on a shared machine that kills other slots.
#
# MAX_SECONDS defaults to 0, meaning *no* cap: let the game end on its own.
# Give a cap only when you want a bounded sample rather than an outcome.
#
# Uses config/play-config.edn, which does *not* set `:no-exit` - that flag turns
# off quit-when-idle / quit-when-looping / quit-when-stuck (in the original too),
# so a game that deadlocks never ends.  Override with PLAY_CONFIG if needed.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?outdir}"; N="${2:?count}"; PAR="${3:-4}"; MAXS="${4:-0}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
mkdir -p "$OUT"
VAR="$ROOT/upstream/nh343/var"

echo "== $N game(s) of the port, $PAR at a time, cap=${MAXS:-none}s"
echo "   port commit $(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo ?)"
nproc | sed 's/^/   cores: /'

play () {                       # $1 = game index, $2 = slot
  local i="$1" slot="$2"
  local d="$OUT/game$i" name="pybot$slot"
  mkdir -p "$d/home"
  rm -f "$VAR"/*"$name"* "$VAR"/save/*"$name"* 2>/dev/null
  local args=(--seed "$((1000 + i))" --log "${LOGLEVEL:-INFO}"
              --logfile "$d/run.log" --ttyrec "$d/game.ttyrec")
  [ "$MAXS" -gt 0 ] && args+=(--max-seconds "$MAXS")
  # WATCHDOG=60 dumps a stack trace to stdout.log whenever a single decision
  # takes longer than that.  The "slow decision" warning in the log cannot help
  # here: it fires *after* an action is chosen, so a bot that never chooses one
  # again never logs anything at all.
  [ -n "${WATCHDOG:-}" ] && args+=(--watchdog "$WATCHDOG")
  # LOGLEVEL=DEBUG logs every scraper state transition, which is the only way to
  # see *why* a stalled game stopped: the INFO log shows the last action and
  # then silence.  Costs hundreds of MB per game.
  local start; start=$(date +%s)
  BOTHACK_HOME="$d/home" BOTHACK_USER="$name" \
    python3 -m pybothack.main "$ROOT/config/${PLAY_CONFIG:-play-config.edn}" "${args[@]}" \
    > "$d/stdout.log" 2>&1
  echo $(( $(date +%s) - start )) > "$d/wall_seconds"
  echo "$name" > "$d/player"
  # only ever kill our own leftovers
  for p in $(pgrep -x nethack.343-nao || true); do
    tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | grep -q -- "-u $name" \
      && kill "$p" 2>/dev/null
  done
  printf '   game %-3s %-8s %s\n' "$i" "$name" \
      "$(tail -1 "$d/run.log" 2>/dev/null | sed 's/.*final state: //')"
}

i=1
while [ "$i" -le "$N" ]; do
  started=0
  for slot in $(seq 1 "$PAR"); do
    [ "$i" -gt "$N" ] && break
    if [ -s "$OUT/game$i/run.log" ] && [ -s "$OUT/game$i/wall_seconds" ]; then
      echo "   game $i already played, skipped"
    else
      play "$i" "$slot" &
      started=$((started + 1))
    fi
    i=$((i + 1))
  done
  [ "$started" -gt 0 ] && wait
done

echo
python3 "$ROOT/tools/ascend_summary.py" "$OUT"
