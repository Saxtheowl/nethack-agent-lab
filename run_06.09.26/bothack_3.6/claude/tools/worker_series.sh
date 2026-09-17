#!/bin/bash
# Sync the code and start a detached series on the worker.
#   tools/worker_series.sh <series-args...>      (e.g. --name x --games 20 ...)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
host="${WORKER_HOST:-miniforum-worker}"
# never change the code under a running series (new games would mix versions)
if ssh -o BatchMode=yes "$host" 'pgrep -f "[n]hbot.series" >/dev/null'; then
    echo "a series is still running on $host; not syncing" >&2
    exit 1
fi
"$here/sync_worker.sh" "$host" >/dev/null
ssh -o BatchMode=yes "$host" 'cd bothack36 && HEADLESS=1 JOBS=8 engine/build.sh > build.out 2>&1' \
    || { echo "engine build failed on $host (see ~/bothack36/build.out)" >&2; exit 1; }
name=""
prev=""
for a in "$@"; do [[ "$prev" == "--name" ]] && name="$a"; prev="$a"; done
args="$(printf '%q ' "$@")"
ssh -o BatchMode=yes "$host" "cd bothack36 && mkdir -p runs && (setsid nohup python3 -m nhbot.series $args > runs/$name.out 2>&1 < /dev/null &); echo launched $name"
