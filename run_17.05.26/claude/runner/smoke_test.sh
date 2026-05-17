#!/bin/bash
# End-to-end smoke test: run a single BotHack game and verify everything works.
# Run inside the container as user `bot`.
set -e

echo "=== NetHack version check ==="
ls -la /nh343/nethack.343-nao
file /nh343/nethack.343-nao || true

echo
echo "=== BotHack uberjar check ==="
ls -la /opt/bothack/target/bothack-*-standalone.jar
ls -la /opt/bothack/jta26/jni/linux/libjtapty.so

echo
echo "=== Seed determinism check (NETHACK_SEED) ==="
# Run NetHack twice with the same seed, in non-interactive mode by sending 'q' immediately
# We just want to see whether srandom() got our seed; a quick proxy is the
# 'starting inventory' which differs by seed.
for SEED in 12345 12345 99999; do
  echo "--- SEED=$SEED ---"
  rm -f /nh343/var/save/$(id -u)* 2>/dev/null || true
  HOME=$(mktemp -d) NETHACK_SEED=$SEED NETHACKOPTIONS=/opt/bothack/bothack.nethackrc \
    timeout 5 /nh343/nethack.343-nao 2>&1 < <(printf '\n\n\nyq\n') | strings | grep -E "long sword|short sword|dagger|small shield|food ration|potion of|wand of" | head -5 || true
done

echo
echo "=== One BotHack game (seed=1000000001, max 90s) ==="
rm -rf /tmp/smoke-out
mkdir -p /tmp/smoke-out

# Patch run_one.sh's timeout for this smoke test
export NH_GAME_DIR=$(mktemp -d /tmp/nh-smoke-XXXXXX)
cp /opt/bothack/bothack.nethackrc "$NH_GAME_DIR/.nethackrc"
cd /tmp/smoke-out

UBERJAR=$(ls /opt/bothack/target/bothack-*-standalone.jar | head -1)
JNI_DIR=/opt/bothack/jta26/jni/linux

export NETHACK_SEED=1000000001
timeout --signal=KILL 90 \
  env LD_LIBRARY_PATH="$JNI_DIR" \
      java -Xms256m -Xmx1g -jar "$UBERJAR" /opt/bothack/config/shell-config.edn \
  >/tmp/smoke-out/bothack.log 2>&1 || echo "(bot returned $?)"

echo
echo "=== Smoke output ==="
ls -la /tmp/smoke-out/
echo
echo "--- ttyrec count ---"
ls /tmp/smoke-out/*.ttyrec 2>/dev/null | wc -l
echo
echo "--- bothack.log (last 30 lines) ---"
tail -30 /tmp/smoke-out/bothack.log
echo
echo "--- ttyrec inspection ---"
TTYREC=$(ls /tmp/smoke-out/*.ttyrec 2>/dev/null | head -1)
if [ -n "$TTYREC" ]; then
  echo "size: $(stat -c%s "$TTYREC") bytes"
  python3 /opt/runner/detect_ascension.py "$TTYREC"
fi
