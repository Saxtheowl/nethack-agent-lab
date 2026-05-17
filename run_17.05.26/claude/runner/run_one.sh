#!/bin/bash
# Run a single BotHack game. Captures ttyrec + stdout/stderr + seed metadata.
#
# Args:
#   $1  game id (e.g. 0001)
#   $2  seed (integer, used as NETHACK_SEED → srandom)
#   $3  output directory (will be created)
#
# On success, writes:
#   <out>/meta.json       — seed, started_at, finished_at, exit_code
#   <out>/bothack.log     — BotHack stdout+stderr
#   <out>/game.ttyrec     — terminal recording (single file)
#
# Detection of win is done by loop.py after this returns.
set -uo pipefail

GAME_ID="${1:?game id}"
SEED="${2:?seed}"
OUT_DIR="${3:?output dir}"

mkdir -p "$OUT_DIR"
NH_GAME_DIR="$(mktemp -d /tmp/nh-game-XXXXXX)"

# Copy the bot rcfile to the game's HOME so NetHack finds it.
cp /opt/bothack/bothack.nethackrc "$NH_GAME_DIR/.nethackrc"

# Per-game playground freshness is handled by nh-launcher.sh (it knows
# WORKER_ID and resets the right /nh343-wN/{save,perm}).

cat > "$OUT_DIR/meta.json.partial" <<EOF
{
  "game_id": "$GAME_ID",
  "seed": $SEED,
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "nh_version": "3.4.3-nao",
  "bot": "bothack.bots.mainbot"
}
EOF

# Find Bothack uberjar (build phase produces one in /opt/bothack/target/)
UBERJAR="$(ls /opt/bothack/target/bothack-*-standalone.jar 2>/dev/null | head -n1)"
if [ -z "$UBERJAR" ]; then
  echo "ERROR: bothack uberjar not found" >&2
  exit 2
fi

JNI_DIR=/opt/bothack/jta26/jni/linux
CONFIG=/opt/bothack/config/shell-config.edn

# BotHack writes its ttyrec into CWD as "<timestamp>.ttyrec". We cd into the
# output dir so it lands where we want.
cd "$OUT_DIR"

export NH_GAME_DIR
export NETHACK_SEED="$SEED"
# HandlerPTY patch makes execve inherit our env — but we need a usable TERM
# (docker exec without -t sets TERM=dumb, which trips NetHack's "Terminal
# must backspace" check). Force xterm unconditionally — BotHack drives the
# game through its own pty emulation, so the actual terminal type is moot.
export TERM=xterm
: "${USER:=bot}"; export USER
: "${LOGNAME:=$USER}"; export LOGNAME

# Wall-clock cap. Failed runs end quickly (death is fast); only winning games
# run long. BotHack plays at ~10-15 turns/sec, ascending takes 50-100k turns,
# so a real win is ~1.5-3h. We cap at 3h to release the loop from a runaway.
# Override with $GAME_TIMEOUT_SEC for smoke-tests.
timeout --signal=KILL "${GAME_TIMEOUT_SEC:-10800}" \
  env LD_LIBRARY_PATH="$JNI_DIR" \
      java -Xms512m -Xmx2g -jar "$UBERJAR" "$CONFIG" \
  >"$OUT_DIR/bothack.log" 2>&1
EXIT_CODE=$?

# Move the ttyrec produced by BotHack to a stable name
shopt -s nullglob
TTYRECS=( "$OUT_DIR"/*.ttyrec )
if [ "${#TTYRECS[@]}" -gt 0 ]; then
  mv "${TTYRECS[-1]}" "$OUT_DIR/game.ttyrec"
fi

# Augment meta — use the venv python that has pyte installed.
/opt/venv/bin/python3 - "$OUT_DIR" "$EXIT_CODE" <<'PY'
import json, os, sys, datetime
out_dir = sys.argv[1]
exit_code = int(sys.argv[2])
meta_path = os.path.join(out_dir, "meta.json.partial")
with open(meta_path) as f:
    meta = json.load(f)
meta["finished_at"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
meta["exit_code"] = exit_code
ttyrec = os.path.join(out_dir, "game.ttyrec")
meta["ttyrec_bytes"] = os.path.getsize(ttyrec) if os.path.exists(ttyrec) else 0
with open(os.path.join(out_dir, "meta.json"), "w") as f:
    json.dump(meta, f, indent=2)
os.remove(meta_path)
PY

# Cleanup workdir (keep the ttyrec in OUT_DIR)
rm -rf "$NH_GAME_DIR" 2>/dev/null || true

exit $EXIT_CODE
