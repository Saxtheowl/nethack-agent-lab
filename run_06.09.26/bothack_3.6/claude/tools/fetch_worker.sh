#!/bin/bash
# Pull game results back from the worker (level files are not copied).
#   tools/fetch_worker.sh <runs-subpath> [host] [remote_dir]
set -euo pipefail
sub="$1"
host="${2:-miniforum-worker}"
src="${3:-bothack36}"
here="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$here/runs/worker/$sub"
rsync -az --exclude 'nhdir/save/' --exclude 'nhdir/*lock*' \
  "$host:$src/runs/$sub/" "$here/runs/worker/$sub/"
echo "fetched into runs/worker/$sub"
