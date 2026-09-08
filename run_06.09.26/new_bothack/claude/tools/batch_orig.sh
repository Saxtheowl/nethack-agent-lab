#!/bin/bash
# Run N games of the ORIGINAL Clojure BotHack against the same NetHack build.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${BOTHACK_SRC:?}"; export JAVA_HOME="${JDK8_HOME:?}"
export PATH="$JAVA_HOME/bin:$LEIN_DIR:$PATH"
export LD_LIBRARY_PATH="$SRC/jta26/jni/linux"
N="${1:-5}"; LIMIT="${2:-900}"; TAG="${3:-orig}"
for i in $(seq 1 "$N"); do
  d="$ROOT/artifacts/games/$TAG/game$i"
  mkdir -p "$d/home"
  # remove leftover locks/saves of a previous (possibly killed) game
  rm -f "$ROOT/upstream/nh343/var/"*origbot* \
        "$ROOT/upstream/nh343/var/save/"*origbot* 2>/dev/null
  cat > "$d/nh.sh" <<NH
#!/bin/bash
export NETHACKOPTIONS="@$ROOT/upstream/bothack.nethackrc"
export TERM=xterm
export HOME="$d/home"
export USER=origbot
if [ -n "\$NETHACK_FIXED_SEED" ] && [ -f "$ROOT/artifacts/det_rng.so" ]; then
  export LD_PRELOAD="$ROOT/artifacts/det_rng.so"
fi
exec "$ROOT/upstream/nh343/nethack.343-nao" -u origbot
NH
  chmod +x "$d/nh.sh"
  cat > "$d/config.edn" <<CFG
{
 :bot "bothack.bots.mainbot"
 :interface :shell
 :nh-command "$d/nh.sh"
 :no-exit true
}
CFG
  cat > "$d/log4j.properties" <<LOG
log4j.rootLogger=DEBUG, file
log4j.appender.file=org.apache.log4j.RollingFileAppender
log4j.appender.file.File=$d/bothack.log
log4j.appender.file.MaxFileSize=100MB
log4j.appender.file.MaxBackupIndex=1
log4j.appender.file.layout=org.apache.log4j.PatternLayout
log4j.appender.file.layout.ConversionPattern=%d %-5p %c{1}:%L - %m%n
LOG
  echo "=== $TAG game $i (limit ${LIMIT}s) $(date -Is)"
  ( cd "$SRC" && JVM_OPTS="-Dlog4j.configuration=file:$d/log4j.properties" \
    BOTHACK_SEED="$((1000 + i))" \
    lein update-in :source-paths conj "\"$ROOT/tools\"" -- \
    run -m cljcmp.runner "$d/config.edn" > "$d/stdout.log" 2>&1 ) &
  runner=$!
  # `timeout` only signals the lein wrapper, so kill the JVM of this game
  for _ in $(seq 1 "$LIMIT"); do
    kill -0 "$runner" 2>/dev/null || break
    sleep 1
  done
  kill "$runner" 2>/dev/null || true
  pkill -f "cljcmp.runner $d/config.edn" 2>/dev/null || true
  wait "$runner" 2>/dev/null || true
done
