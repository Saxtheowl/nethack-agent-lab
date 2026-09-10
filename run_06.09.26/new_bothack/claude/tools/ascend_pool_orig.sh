#!/bin/bash
# Play real games with the ORIGINAL Clojure BotHack, same shape as
# tools/ascend_pool.sh, so the two bots' real-game results are comparable.
#
#   BOTHACK_SRC=… JDK8_HOME=… LEIN_DIR=… tools/ascend_pool_orig.sh OUT SLOTS PREFIX
#
# Deliberately mirrors ascend_pool.sh: same NetHack build, same nethackrc, no
# wizard mode, no fixed seed, no PTY tap, and a config WITHOUT :no-exit so the
# original's own quit-when-idle / -looping / -stuck handlers stay enabled -
# exactly the conditions the port plays under.  BotHack itself is not modified;
# only Leiningen's source path gains the harness namespace, as everywhere else.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${BOTHACK_SRC:?set BOTHACK_SRC}"
export JAVA_HOME="${JDK8_HOME:?set JDK8_HOME}"
export PATH="$JAVA_HOME/bin:${LEIN_DIR:?set LEIN_DIR}:$PATH"
export LD_LIBRARY_PATH="$SRC/jta26/jni/linux"
OUT="${1:?outdir}"; SLOTS="${2:-2}"; PREFIX="${3:-orig}"
case "$OUT" in /*) ;; *) OUT="$PWD/$OUT" ;; esac
mkdir -p "$OUT"
VAR="$ROOT/upstream/nh343/var"
XLOG="$VAR/xlogfile"

echo "== orig pool: $SLOTS slots, names ${PREFIX}1..${PREFIX}$SLOTS"

play () {
  local i="$1" slot="$2"
  local d="$OUT/game$i" name="$PREFIX$slot"
  mkdir -p "$d/home"
  rm -f "$VAR"/*"$name"* "$VAR"/save/*"$name"* 2>/dev/null
  # JTA's HandlerPTY execve()s with its own environment, so bake the paths in.
  cat > "$d/nh.sh" <<NH
#!/bin/bash
export NETHACKOPTIONS="@$ROOT/upstream/bothack.nethackrc"
export TERM=xterm
export HOME="$d/home"
export USER="$name"
exec "$ROOT/upstream/nh343/nethack.343-nao" -u "$name"
NH
  chmod +x "$d/nh.sh"
  cat > "$d/config.edn" <<CFG
{
 :bot "bothack.bots.mainbot"
 :interface :shell
 :nh-command "$d/nh.sh"
}
CFG
  cat > "$d/log4j.properties" <<LOG
log4j.rootLogger=DEBUG, file
log4j.appender.file=org.apache.log4j.RollingFileAppender
log4j.appender.file.File=$d/bothack.log
log4j.appender.file.MaxFileSize=60MB
log4j.appender.file.MaxBackupIndex=1
log4j.appender.file.layout=org.apache.log4j.PatternLayout
log4j.appender.file.layout.ConversionPattern=%d %-5p %c{1}:%L - %m%n
LOG
  local start; start=$(date +%s)
  ( cd "$SRC" && \
    JVM_OPTS="-Dlog4j.configuration=file:$d/log4j.properties" \
    BOTHACK_HOME="$d/home" BOTHACK_USER="$name" \
    lein run -m bothack.main "$d/config.edn" ) > "$d/stdout.log" 2>&1
  echo $(( $(date +%s) - start )) > "$d/wall_seconds"
  echo "$name" > "$d/player"
  for p in $(pgrep -x nethack.343-nao || true); do
    tr '\0' ' ' < "/proc/$p/cmdline" 2>/dev/null | grep -q -- "-u $name" \
      && kill "$p" 2>/dev/null
  done
  printf '   orig game %-4s %-9s %ss\n' "$i" "$name" "$(cat "$d/wall_seconds")"
}

declare -A busy=()
next=1
while true; do
  for slot in $(seq 1 "$SLOTS"); do
    pid="${busy[$slot]:-}"
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then continue; fi
    play "$next" "$slot" &
    busy[$slot]=$!
    next=$((next + 1))
    sleep 2
  done
  sleep 20
  if grep -q "death=ascended" "$XLOG" 2>/dev/null; then
    echo "== ASCENSION  $(date -Is)"; grep "death=ascended" "$XLOG" | tail -3; break
  fi
done
