#!/bin/bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export NETHACKOPTIONS="@$ROOT/upstream/bothack.nethackrc"
export TERM=xterm
export HOME="${BOTHACK_HOME:-$ROOT/artifacts/home_orig}"
export USER="${BOTHACK_USER:-origbot}"
mkdir -p "$HOME"
exec "$ROOT/upstream/nh343/nethack.343-nao" -u "$USER"
