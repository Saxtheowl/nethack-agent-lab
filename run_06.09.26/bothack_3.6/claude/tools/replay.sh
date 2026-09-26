#!/bin/bash
# Watch a recorded game (rungame --record) like the ttyrecs of the BotHack port.
#
#   tools/replay.sh runs/replays/g011            # local game directory
#   tools/replay.sh worker:bothack36-dev3/runs/dev/replay-8011   # on the worker
#
# The protocol trace is fetched if needed, converted once to <dir>/replay.ttyrec
# (tools/trace2ttyrec.py), then played with ttyplay ('+'/'-' speed, space pause,
# q quit).  DELAY=0.01 tools/replay.sh ... for a faster default speed.
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
src="${1:?usage: tools/replay.sh <game-dir | worker:path>}"
if [[ "$src" == worker:* ]]; then
    remote="${src#worker:}"
    local_dir="$here/runs/replays/$(basename "$remote")"
    mkdir -p "$local_dir"
    rsync -az "miniforum-worker:$remote/protocol.trace.gz" "$local_dir/"
    rsync -az "miniforum-worker:$remote/result.json" "$local_dir/" 2>/dev/null || true
    if ! ssh -o BatchMode=yes miniforum-worker "test -f $remote/result.json"; then
        echo "note: $remote is still running - replaying what is recorded so far" >&2
        rm -f "$local_dir/replay.ttyrec"
    fi
    src="$local_dir"
fi
trace="$src/protocol.trace.gz"
[ -f "$trace" ] || trace="$src/protocol.trace"
[ -f "$trace" ] || { echo "no protocol trace in $src (was it run with --record?)" >&2; exit 1; }
rec="$src/replay.ttyrec"
if [ ! -f "$rec" ] || [ "$trace" -nt "$rec" ]; then
    python3 "$here/tools/trace2ttyrec.py" "$trace" "$rec"
fi
exec ttyplay "$rec"
