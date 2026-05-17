#!/usr/bin/env bash
set -uo pipefail

target="${1:-10}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

while true; do
  count="$(find wins -mindepth 1 -maxdepth 1 -type d -printf '.' | wc -c)"
  attempts="$(find recordings -maxdepth 1 -type d -name 'worker-*' -printf '.' | wc -c)"
  printf '%s wins=%s attempts=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$count" "$attempts"
  docker ps --filter name=bothack-worker --format '{{.Names}} {{.Status}}' || true
  du -sh logs recordings wins seeds 2>/dev/null | tr '\n' ' ' || true
  echo

  if [ "$count" -ge "$target" ]; then
    docker rm -f bothack-worker-1 bothack-worker-2 bothack-worker-3 bothack-worker-4 >/dev/null 2>&1 || true
    docker exec super-nethack-bothack-lab python3 /opt/replay_app/index_recordings.py --root /lab >/dev/null || true
    printf 'completed at %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    break
  fi

  sleep 60
done
