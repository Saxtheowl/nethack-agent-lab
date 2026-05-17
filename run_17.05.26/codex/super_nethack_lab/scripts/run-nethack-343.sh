#!/usr/bin/env bash
set -euo pipefail

export TERM="${TERM:-xterm-256color}"
export HOME=/home/botlab

# Keep NetHack away from full/new moon startup messages that confuse BotHack's
# initial scraper. This affects only the NetHack child process.
if [ -r /usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1 ]; then
  export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1
  export FAKETIME="${BOTLAB_NETHACK_DATE:-2026-05-20 12:00:00}"
fi

cd /opt/nh343/nh343
exec /opt/nh343/nh343/nethack.343-nao
