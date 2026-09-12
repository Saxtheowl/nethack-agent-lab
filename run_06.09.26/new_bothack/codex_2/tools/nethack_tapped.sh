#!/bin/bash
# NetHack 3.4.3-NAO behind the recording pty tap.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export NETHACKOPTIONS="@$ROOT/upstream/bothack.nethackrc"
export TERM=xterm
export HOME="${BOTHACK_HOME:-$ROOT/artifacts/home}"
export USER="${BOTHACK_USER:-claudebot}"
export PTY_TAP_LOG="${PTY_TAP_LOG:-$ROOT/artifacts/pty_tap.log}"
mkdir -p "$HOME"
if [ -n "$NETHACK_FIXED_SEED" ] && [ -f "$ROOT/artifacts/det_rng.so" ]; then
  export LD_PRELOAD="$ROOT/artifacts/det_rng.so${LD_PRELOAD:+:$LD_PRELOAD}"
fi
exec python3 "$ROOT/tools/pty_tap.py" "$ROOT/upstream/nh343/nethack.343-nao" -u "$USER"
