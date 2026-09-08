#!/bin/bash
# Play ONE deterministic game with each bot and compare the keystrokes they
# send, byte for byte.
#
# Everything that could differ between the two runs is pinned:
#   * NetHack's RNG          - tools/det_rng.c (LD_PRELOAD, fixed seed)
#   * the bots' own RNG      - the shared LCG (BOTHACK_SEED / --seed)
#   * handler tie order      - tools/cljcmp/handlers_det.clj for the original,
#                              registration order for the port
#   * the player name, the nethackrc, the terminal size and the binary
# so any difference in the keystroke streams is a difference in the port.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$ROOT/artifacts/live_compare}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
SECS="${2:-300}"
NHSEED="${NETHACK_FIXED_SEED:-4242}"
BSEED="${BOTHACK_SEED:-12345}"
mkdir -p "$OUT"

kill_strays () {
  # A killed JVM leaves its NetHack child running, and every run here plays as
  # the same user, so a leftover process removes the *current* game's level
  # files on its way out ("Cannot open file 1000claudebot.0").  Clear them out
  # before touching var/.
  # -x matches the process *name*, not the command line: `pgrep -f` also
  # matches whatever shell happens to have this script's name in its argv,
  # including the caller, which then gets killed (exit 144).
  local pids
  pids=$(pgrep -x nethack.343-nao || true)
  if [ -n "$pids" ]; then
    echo "   (killing leftover NetHack processes: $(echo $pids | tr '\n' ' '))"
    for p in $pids; do kill "$p" 2>/dev/null || true; done
    sleep 1
    for p in $(pgrep -x nethack.343-nao || true); do
      kill -9 "$p" 2>/dev/null || true
    done
    sleep 1
  fi
}

clean_locks () {
  kill_strays
  rm -f "$ROOT/upstream/nh343/var/"*claudebot* \
        "$ROOT/upstream/nh343/var/save/"*claudebot* 2>/dev/null || true
}

mk_launcher () {   # $1 = dir
  cat > "$1/nh.sh" <<LAUNCH
#!/bin/bash
export NETHACKOPTIONS="@$ROOT/upstream/bothack.nethackrc"
export TERM=xterm
export HOME="$1/home"
export USER=claudebot
export PTY_TAP_LOG="$1/tap.log"
export NETHACK_FIXED_SEED="$NHSEED"
# 250 ms: long enough that a whole travel command - whose output NetHack
# emits in bursts - lands in one group whatever the scheduler does.  With
# 30 ms the two bots saw the same bytes sliced into different frames.
export PTY_TAP_SETTLE="${PTY_TAP_SETTLE:-0.25}"
export PTY_TAP_PIECE_DELAY="${PTY_TAP_PIECE_DELAY:-0.015}"
export LD_PRELOAD="$ROOT/artifacts/det_rng.so"
mkdir -p "\$HOME"
exec python3 "$ROOT/tools/pty_tap.py" "$ROOT/upstream/nh343/nethack.343-nao" -u claudebot
LAUNCH
  chmod +x "$1/nh.sh"
}

echo "== port, NetHack seed $NHSEED, bot seed $BSEED, ${SECS}s"
clean_locks
mkdir -p "$OUT/port/home"
mk_launcher "$OUT/port"
cat > "$OUT/port/config.edn" <<CFG
{
 :bot "mainbot"
 :interface :shell
 :nh-command "$OUT/port/nh.sh"
 :no-exit true
}
CFG
timeout $((SECS + 60)) python3 -m pybothack.main "$OUT/port/config.edn" \
    --seed "$BSEED" --lcg --max-seconds "$SECS" --log INFO \
    --logfile "$OUT/port/run.log" > "$OUT/port/stdout.log" 2>&1 || true

echo "== original, same seeds"
clean_locks
mkdir -p "$OUT/orig/home"
mk_launcher "$OUT/orig"
cat > "$OUT/orig/config.edn" <<CFG
{
 :bot "bothack.bots.mainbot"
 :interface :shell
 :nh-command "$OUT/orig/nh.sh"
 :no-exit true
}
CFG
cat > "$OUT/orig/log4j.properties" <<LOG
log4j.rootLogger=DEBUG, file
log4j.appender.file=org.apache.log4j.RollingFileAppender
log4j.appender.file.File=$OUT/orig/bothack.log
log4j.appender.file.MaxFileSize=200MB
log4j.appender.file.MaxBackupIndex=1
log4j.appender.file.layout=org.apache.log4j.PatternLayout
log4j.appender.file.layout.ConversionPattern=%d %-5p %c{1}:%L - %m%n
LOG
( cd "${BOTHACK_SRC:?}" && \
  JAVA_HOME="${JDK8_HOME:?}" PATH="${JDK8_HOME}/bin:${LEIN_DIR}:$PATH" \
  LD_LIBRARY_PATH="${BOTHACK_SRC}/jta26/jni/linux" \
  LEIN_JVM_OPTS="-Xmx256m" \
  JVM_OPTS="-Xmx768m -Dlog4j.configuration=file:$OUT/orig/log4j.properties" \
  BOTHACK_SEED="$BSEED" \
  lein update-in :source-paths conj "\"$ROOT/tools\"" -- \
  run -m cljcmp.runner "$OUT/orig/config.edn" > "$OUT/orig/stdout.log" 2>&1 ) &
runner=$!
for _ in $(seq 1 "$SECS"); do kill -0 "$runner" 2>/dev/null || break; sleep 1; done
kill "$runner" 2>/dev/null || true
wait "$runner" 2>/dev/null || true
# `kill` only reaches the lein wrapper; the JVM it spawned survives, and a
# handful of leftover JVMs is enough to exhaust this machine's memory and have
# the OOM killer take down the run.  Kill it by name (never `pgrep -f`, which
# would also match the shell that is running this script).
pkill -x java 2>/dev/null || true
sleep 1

kill_strays
echo "== comparing"
python3 "$ROOT/tools/compare_taps.py" "$OUT/orig/tap.log" "$OUT/port/tap.log" \
    | tee "$OUT/report.txt"
