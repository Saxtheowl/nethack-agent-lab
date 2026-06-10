#!/usr/bin/env bash
set -euo pipefail

export TERM="${TERM:-xterm}"
export HOME=/home/botlab

seed_file=/opt/nh343/nh343/var/botlab.seed
if [ -r "$seed_file" ]; then
  export NETHACK_SEED="$(tr -dc '0-9' <"$seed_file")"
fi

# Optional compatibility guard for moon startup messages. Disabled by default so
# normal runs stay as close as possible to the author's local/server setup.
if [ "${BOTLAB_USE_FAKETIME:-0}" = "1" ] && [ -r /usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1 ]; then
  export LD_PRELOAD=/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1
  export FAKETIME="${BOTLAB_NETHACK_DATE:-2026-05-20 12:00:00}"
fi

cd /opt/nh343/nh343
exec /opt/nh343/nh343/nethack.343-nao
