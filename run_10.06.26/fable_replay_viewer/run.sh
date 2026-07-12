#!/usr/bin/env bash
# Lance le Fable Replay Viewer. Installe pyte dans un venv local si besoin.
set -euo pipefail
cd "$(dirname "$0")"

VENV=".venv"
if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip pyte
fi

exec "$VENV/bin/python" server.py "$@"
