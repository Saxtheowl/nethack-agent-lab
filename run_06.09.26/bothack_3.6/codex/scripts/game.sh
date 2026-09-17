#!/bin/bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
export TERM=xterm
export NETHACKOPTIONS="@$ROOT/config/nethackrc"
exec "$ROOT/build/game/nethack" -d "$BH_GAME_DIR" -u localbot
