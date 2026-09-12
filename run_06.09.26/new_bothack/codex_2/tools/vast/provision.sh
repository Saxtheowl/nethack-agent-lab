#!/bin/bash
# Provision one machine for *recording* games of the original BotHack.
#
# The expensive half of the fidelity loop is recording: a JVM plus a NetHack per
# game, bounded by wall clock.  Replaying a recording into the port needs no
# NetHack and no JVM, so it stays wherever the port lives.  A recorder needs:
# a JDK 8 (Clojure 1.6 and dynapath do not run on 9+), Leiningen, a build of
# NetHack 3.4.3 + the NAO patchset, and this repository.
#
#   tools/vast/provision.sh            # from the repo root
#
# Everything lands under $NHWORK (default ~/nhwork), which must survive a
# reboot: /tmp does not, and losing the toolchain there costs a re-download and
# a full `lein deps`.
#
# Works as root or as an ordinary user: the apt step is skipped when it cannot
# run, and the script then checks the tools are present rather than assuming.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WORK="${NHWORK:-$HOME/nhwork}"
mkdir -p "$WORK"

log () { printf '== %s  %s\n' "$(date -Is)" "$*"; }
die () { printf '!! %s\n' "$*" >&2; exit 1; }

# --- system packages -------------------------------------------------------
if [ "$(id -u)" = 0 ] && command -v apt-get >/dev/null; then
  log "apt dependencies"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq --no-install-recommends \
      build-essential flex bison libncurses-dev git curl ca-certificates \
      python3 xz-utils
else
  log "not root (or no apt): skipping package install, checking instead"
  for t in gcc git curl python3 tar; do
    command -v "$t" >/dev/null || die "missing $t - install it or run as root"
  done
fi

# --- JDK 8 -----------------------------------------------------------------
# Clojure 1.6 and dynapath do not run on 9+.  Prefer a system JDK 8; otherwise
# fetch a Temurin build, because most images ship a newer JDK only.
find_jdk8 () {
  for d in /usr/lib/jvm/java-8-openjdk-* /usr/lib/jvm/*1.8* "$WORK"/jdk8; do
    [ -x "$d/bin/java" ] || continue
    if "$d/bin/java" -version 2>&1 | grep -q '"1\.8'; then
      echo "$d"
      return 0
    fi
  done
  return 1
}
if JDK8="$(find_jdk8)"; then
  log "JDK 8 already present: $JDK8"
else
  log "fetching a JDK 8 (Temurin)"
  arch="$(uname -m)"
  case "$arch" in
    x86_64) jarch=x64 ;;
    aarch64|arm64) jarch=aarch64 ;;
    *) die "no JDK 8 and no Temurin build for $arch" ;;
  esac
  url="https://api.adoptium.net/v3/binary/latest/8/ga/linux/$jarch/jdk/hotspot/normal/eclipse"
  tmp="$WORK/jdk8.tar.gz"
  curl -fsSL -o "$tmp" "$url" || die "JDK 8 download failed"
  rm -rf "$WORK/jdk8" && mkdir -p "$WORK/jdk8"
  tar -C "$WORK/jdk8" --strip-components=1 -xzf "$tmp"
  rm -f "$tmp"
  JDK8="$WORK/jdk8"
  "$JDK8/bin/java" -version 2>&1 | head -1 | sed 's/^/   /'
fi

# --- Leiningen -------------------------------------------------------------
if [ ! -x "$WORK/lein" ]; then
  log "leiningen"
  curl -fsSL -o "$WORK/lein" \
    https://raw.githubusercontent.com/technomancy/leiningen/stable/bin/lein
  chmod +x "$WORK/lein"
fi

# --- BotHack at the pinned commit -----------------------------------------
BOTHACK_COMMIT="${BOTHACK_COMMIT:-70226b3c8ed12d29c64068aec0acc0ca71d57adf}"
if [ ! -d "$WORK/bothack-src/.git" ]; then
  log "cloning BotHack"
  git clone -q https://github.com/krajj7/BotHack "$WORK/bothack-src"
fi
git -C "$WORK/bothack-src" fetch -q origin || true
git -C "$WORK/bothack-src" checkout -q "$BOTHACK_COMMIT"
log "BotHack at $(git -C "$WORK/bothack-src" rev-parse --short HEAD)"
# The checkout must match the pinned commit exactly.  Build products are
# expected (libjtapty.so, target/, *.class) and are ignored here; what must
# never differ is a *tracked source file*.
if [ -n "$(git -C "$WORK/bothack-src" status --porcelain --untracked-files=no)" ]; then
  git -C "$WORK/bothack-src" status --porcelain --untracked-files=no >&2
  die "the BotHack checkout has modified tracked files - it must never be edited"
fi

# --- NetHack 3.4.3 + NAO ---------------------------------------------------
if [ ! -x "$ROOT/upstream/nh343/nethack.343-nao" ]; then
  log "building NetHack 3.4.3 + NAO"
  [ -d "$WORK/nh343-nao/.git" ] || \
    git clone -q https://github.com/neoascetic/nh343-nao "$WORK/nh343-nao"
  "$ROOT/tools/build_nethack343_nao.sh" "$WORK/nh343-nao"
else
  log "NetHack already built: $ROOT/upstream/nh343/nethack.343-nao"
fi

# --- deterministic RNG shim ------------------------------------------------
if [ ! -f "$ROOT/artifacts/det_rng.so" ]; then
  log "building the deterministic RNG shim"
  mkdir -p "$ROOT/artifacts"
  gcc -shared -fPIC -o "$ROOT/artifacts/det_rng.so" "$ROOT/tools/det_rng.c" -ldl
fi

# --- warm the Clojure dependency cache -------------------------------------
# so the first recording does not pay for a few hundred MB of downloads while
# the wall clock is running
log "lein deps (first run downloads a lot)"
( cd "$WORK/bothack-src" && \
  JAVA_HOME="$JDK8" PATH="$JDK8/bin:$WORK:$PATH" \
  LEIN_JVM_OPTS=-Xmx256m "$WORK/lein" deps >/dev/null ) \
  || die "lein deps failed"

# --- the native JTA pty library -------------------------------------------
# BotHack requires `bothack.jta` at namespace load even for `:interface :shell`,
# and that needs libjtapty.so, which the repository does **not** ship - only its
# Makefile.  Without it every run dies with
# `UnsatisfiedLinkError: no jtapty in java.library.path` before the first
# keystroke.  Found by running this script on a machine whose /tmp had been
# wiped; the previous toolchain had the library built by hand and nothing
# recorded that it was needed.
#
# The Makefile's JNI include path points at a 2001-era JDK and `javah` was
# removed in JDK 10+, so both are overridden with this JDK 8.
JTA="$WORK/bothack-src/jta26"
if [ ! -f "$JTA/jni/linux/libjtapty.so" ]; then
  log "building libjtapty.so"
  ( cd "$JTA" && "$JDK8/bin/javac" -d . de/mud/jta/plugin/HandlerPTY.java )
  make -C "$JTA/jni/linux" \
      JAVAH="$JDK8/bin/javah" \
      JNI_INCLUDE="-I$JDK8/include -I$JDK8/include/linux" >/dev/null \
    || die "libjtapty.so build failed"
fi
[ -f "$JTA/jni/linux/libjtapty.so" ] || die "libjtapty.so missing after build"
log "libjtapty.so present"

# --- compile the Java sources ---------------------------------------------
# BotHack has 88 Java files (the FOV, the bot API).  `lein deps` does not build
# them, and the *first* `lein run` fails outright while it compiles - found by
# running this script for real on a machine whose /tmp had just been wiped.
# Doing it here means the first recording starts a game instead of a compiler.
log "javac warm-up"
( cd "$WORK/bothack-src" && \
  JAVA_HOME="$JDK8" PATH="$JDK8/bin:$WORK:$PATH" \
  LEIN_JVM_OPTS=-Xmx256m "$WORK/lein" javac >/dev/null 2>&1 ) || true
if [ ! -d "$WORK/bothack-src/target/classes/bothack" ]; then
  log "  (lein javac produced nothing; the first `lein run` will compile)"
fi

log "ready.  Export these before recording:"
cat <<ENV
   export BOTHACK_SRC=$WORK/bothack-src
   export JDK8_HOME=$JDK8
   export LEIN_DIR=$WORK
ENV
