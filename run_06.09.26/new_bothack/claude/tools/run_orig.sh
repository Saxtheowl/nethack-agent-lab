#!/bin/bash
# Run the ORIGINAL Clojure BotHack against the local NetHack 3.4.3-NAO, with
# the deterministic RNG of the comparison harness and the recording pty tap.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${BOTHACK_SRC:?set BOTHACK_SRC}"
export JAVA_HOME="${JDK8_HOME:?set JDK8_HOME}"
export PATH="$JAVA_HOME/bin:$LEIN_DIR:$PATH"
export LD_LIBRARY_PATH="$SRC/jta26/jni/linux"
export BOTHACK_SEED="${BOTHACK_SEED:-12345}"
OUT="${OUT:-$ROOT/artifacts/orig}"
mkdir -p "$OUT"
export PTY_TAP_LOG="$OUT/pty_tap.log"
# JTA's HandlerPTY execve()s with its own environment, so bake the paths into
# a per-run launcher instead of relying on inherited env vars.
cat > "$OUT/nh.sh" <<NH
#!/bin/bash
export NETHACKOPTIONS="@$ROOT/upstream/bothack.nethackrc"
export TERM=xterm
export HOME="$OUT/home"
export USER="${BOTHACK_USER:-origbot}"
export PTY_TAP_LOG="$OUT/pty_tap.log"
exec python3 "$ROOT/tools/pty_tap.py" "$ROOT/upstream/nh343/nethack.343-nao" -u "${BOTHACK_USER:-origbot}"
NH
chmod +x "$OUT/nh.sh"
export BOTHACK_HOME="$OUT/home"
export BOTHACK_USER="${BOTHACK_USER:-origbot}"
rm -rf "$BOTHACK_HOME"; mkdir -p "$BOTHACK_HOME"
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
log4j.appender.file.MaxFileSize=200MB
log4j.appender.file.MaxBackupIndex=2
log4j.appender.file.layout=org.apache.log4j.PatternLayout
log4j.appender.file.layout.ConversionPattern=%d %-5p %c{1}:%L - %m%n
LOG
cd "$SRC"     # lein needs the project directory
export JVM_OPTS="-Dlog4j.configuration=file:$OUT/log4j.properties"
timeout "${SECONDS_LIMIT:-120}" lein \
    update-in :source-paths conj "\"$ROOT/tools\"" -- \
    run -m cljcmp.runner "$OUT/config.edn" > "$OUT/stdout.log" 2>&1 || true
echo "tap log: $(stat -c%s "$PTY_TAP_LOG") bytes"
grep -c "writing to terminal" "$OUT/bothack.log" 2>/dev/null || true
