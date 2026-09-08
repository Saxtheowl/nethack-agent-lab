#!/bin/bash
# Record ONE full game of the original with everything pinned, so the port can
# be replayed against it as often as we like.
#
#   SEED  - NetHack's RNG seed (tools/det_rng.c)
#   OUT   - output directory (gets tap.log, bothack.log, ...)
#   NAME  - NetHack user name; give parallel runs different names so their
#           lock/level files in var/ do not collide
#   SECS  - wall-clock cap; the game normally ends before it (death)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SEED="${1:?seed}"; OUT="${2:?outdir}"; NAME="${3:-claudebot}"; SECS="${4:-2400}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
mkdir -p "$OUT/home"
rm -f "$ROOT/upstream/nh343/var/"*"$NAME"* \
      "$ROOT/upstream/nh343/var/save/"*"$NAME"* 2>/dev/null || true

cat > "$OUT/nh.sh" <<LAUNCH
#!/bin/bash
export NETHACKOPTIONS="@$ROOT/upstream/bothack.nethackrc"
export TERM=xterm
export HOME="$OUT/home"
export USER=$NAME
export PTY_TAP_LOG="$OUT/tap.log"
export PTY_TAP_SETTLE="${PTY_TAP_SETTLE:-0.25}"
export PTY_TAP_PIECE_DELAY="${PTY_TAP_PIECE_DELAY:-0.05}"
export PTY_TAP_IDLE="${PTY_TAP_IDLE:-1}"
export NETHACK_FIXED_SEED="$SEED"
export LD_PRELOAD="$ROOT/artifacts/det_rng.so"
mkdir -p "\$HOME"
exec python3 "$ROOT/tools/pty_tap.py" "$ROOT/upstream/nh343/nethack.343-nao" -u $NAME
LAUNCH
chmod +x "$OUT/nh.sh"
cat > "$OUT/config.edn" <<CFG
{
 :bot "bothack.bots.mainbot"
 :interface :shell
 :nh-command "$OUT/nh.sh"
 :no-exit true
}
CFG
cat > "$OUT/log4j.properties" <<LOG
log4j.rootLogger=DEBUG, file
log4j.appender.file=org.apache.log4j.RollingFileAppender
log4j.appender.file.File=$OUT/bothack.log
log4j.appender.file.MaxFileSize=400MB
log4j.appender.file.MaxBackupIndex=1
log4j.appender.file.layout=org.apache.log4j.PatternLayout
log4j.appender.file.layout.ConversionPattern=%d %-5p %c{1}:%L - %m%n
LOG

( cd "${BOTHACK_SRC:?}" && \
  JAVA_HOME="${JDK8_HOME:?}" PATH="${JDK8_HOME}/bin:${LEIN_DIR}:$PATH" \
  LD_LIBRARY_PATH="${BOTHACK_SRC}/jta26/jni/linux" \
  LEIN_JVM_OPTS="-Xmx256m" \
  JVM_OPTS="-Xmx768m -Dlog4j.configuration=file:$OUT/log4j.properties" \
  BOTHACK_SEED="${BOTHACK_SEED:-12345}" \
  lein update-in :source-paths conj "\"$ROOT/tools\"" -- \
  run -m cljcmp.runner "$OUT/config.edn" > "$OUT/stdout.log" 2>&1 ) &
runner=$!
for _ in $(seq 1 "$SECS"); do kill -0 "$runner" 2>/dev/null || break; sleep 1; done
kill "$runner" 2>/dev/null || true
wait "$runner" 2>/dev/null || true
# the JVM outlives the lein wrapper; a few leftovers exhaust this machine
for p in $(pgrep -x java || true); do
  grep -qa "$OUT" "/proc/$p/cmdline" 2>/dev/null && kill "$p" 2>/dev/null || true
done
sleep 1
echo "$(python3 - "$OUT/tap.log" <<'PY'
import struct, sys
d=open(sys.argv[1],'rb').read(); i=0; ins=0; outb=0; n=0
while i+5<=len(d):
    k=d[i:i+1]; L=struct.unpack('<I',d[i+1:i+5])[0]
    if k==b'I': ins+=L
    else: outb+=L; n+=1
    i+=5+L
print("keystrokes=%d output=%d chunks=%d" % (ins, outb, n))
PY
)"
