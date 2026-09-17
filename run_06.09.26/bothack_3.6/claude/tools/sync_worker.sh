#!/bin/bash
# Push the code to the worker (no runs, no build outputs).
#   tools/sync_worker.sh [host] [remote_dir]
set -euo pipefail
host="${1:-miniforum-worker}"
dest="${2:-bothack36}"
here="$(cd "$(dirname "$0")/.." && pwd)"
rsync -az --delete \
  --exclude 'runs/' --exclude 'build/' --exclude 'scratch/' \
  --exclude '__pycache__/' --exclude '*.o' --exclude '.pytest_cache/' \
  --exclude 'engine/nethack-3.6.7/src/nethack' \
  --exclude 'engine/nethack-3.6.7/util/makedefs' \
  --exclude 'engine/nethack-3.6.7/util/lev_comp' \
  --exclude 'engine/nethack-3.6.7/util/dgn_comp' \
  --exclude 'engine/nethack-3.6.7/util/dlb' \
  --exclude 'engine/nethack-3.6.7/dat/*.lev' \
  --exclude 'vendor/nethack-3.6.7.tar.gz' \
  "$here/" "$host:$dest/"
echo "synced to $host:$dest"
