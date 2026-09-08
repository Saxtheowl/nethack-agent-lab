#!/bin/bash
# Launch the locally built NetHack 3.4.3-NAO with BotHack's nethackrc.
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export NETHACKOPTIONS="@$ROOT/upstream/bothack.nethackrc"
export TERM=xterm
export HOME="${BOTHACK_HOME:-$ROOT/artifacts/home}"
export USER="${BOTHACK_USER:-claudebot}"
mkdir -p "$HOME"
# For reproducible comparison runs: NETHACK_FIXED_SEED pins the game's RNG
# through tools/det_rng.so (see that file - it is not wizard mode).
if [ -n "$NETHACK_FIXED_SEED" ] && [ -f "$ROOT/artifacts/det_rng.so" ]; then
  export LD_PRELOAD="$ROOT/artifacts/det_rng.so${LD_PRELOAD:+:$LD_PRELOAD}"
fi
exec "$ROOT/upstream/nh343/nethack.343-nao" -u "$USER"
