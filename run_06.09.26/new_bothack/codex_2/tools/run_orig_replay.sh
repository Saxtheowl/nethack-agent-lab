#!/bin/bash
# Replay a recorded stream into the ORIGINAL BotHack and capture its keystrokes.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${BOTHACK_SRC:?}"; export JAVA_HOME="${JDK8_HOME:?}"
export PATH="$JAVA_HOME/bin:$LEIN_DIR:$PATH"
export LD_LIBRARY_PATH="$SRC/jta26/jni/linux"
TAP="${TAP:?set TAP to a pty_tap log}"
OUT="${OUT:?}"; mkdir -p "$OUT"
cat > "$OUT/replay.sh" <<RS
#!/bin/bash
export REPLAY_TAP="$TAP"
export REPLAY_KEYS="$OUT/orig_keys.bin"
export REPLAY_DELAY="${REPLAY_DELAY:-0.002}"
export REPLAY_STATUS="$OUT/replay_status.txt"
exec python3 "$ROOT/tools/replay_server.py"
RS
chmod +x "$OUT/replay.sh"
cat > "$OUT/config.edn" <<CFG
{
 :bot "bothack.bots.mainbot"
 :interface :shell
 :nh-command "$OUT/replay.sh"
 :no-exit true
}
CFG
cat > "$OUT/log4j.properties" <<LOG
log4j.rootLogger=DEBUG, file
log4j.appender.file=org.apache.log4j.RollingFileAppender
log4j.appender.file.File=$OUT/bothack.log
log4j.appender.file.MaxFileSize=200MB
log4j.appender.file.MaxBackupIndex=2
log4j.appender.file.layout=org.apache.log4j.PatternLayout
log4j.appender.file.layout.ConversionPattern=%d %-5p %c{1}:%L - %m%n
LOG
cd "$SRC"
export JVM_OPTS="-Dlog4j.configuration=file:$OUT/log4j.properties"
export BOTHACK_SEED="${BOTHACK_SEED:-12345}"
timeout "${SECONDS_LIMIT:-300}" lein \
    update-in :source-paths conj "\"$ROOT/tools\"" -- \
    run -m cljcmp.runner "$OUT/config.edn" > "$OUT/stdout.log" 2>&1 || true
echo "captured $(stat -c%s "$OUT/orig_keys.bin" 2>/dev/null || echo 0) keystroke bytes"
