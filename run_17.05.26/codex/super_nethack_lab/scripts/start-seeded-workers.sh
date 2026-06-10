#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

workers="${1:-4}"
target="${2:-10}"
timeout_value="${BOTLAB_TIMEOUT:-36h}"

for n in $(seq 1 "$workers"); do
  docker rm -f "bothack-worker-$n" >/dev/null 2>&1 || true
  docker run -d --name "bothack-worker-$n" \
    -v "$PWD/recordings:/lab/recordings" \
    -v "$PWD/wins:/lab/wins" \
    -v "$PWD/seeds:/lab/seeds" \
    -v "$PWD/logs:/lab/logs" \
    -v "$PWD/workspace:/lab/workspace" \
    -e BOTLAB_TIMEOUT="$timeout_value" \
    super-nethack-bothack-lab:local \
    bash -lc 'i=0; while [ "$(find /lab/wins -mindepth 1 -maxdepth 1 -type d | wc -l)" -lt '"$target"' ]; do i=$((i+1)); started=$(date +%s); run_id="worker-'"$n"'-seeded-${i}-$(date -u +%Y%m%dT%H%M%SZ)"; /opt/botlab_scripts/run-bothack-once.sh "$run_id" || true; rm -f "/lab/logs/${run_id}.stdout.log" "/lab/logs/${run_id}.stderr.log"; if [ ! -d "/lab/wins/$run_id" ]; then rm -rf "/lab/recordings/$run_id"; rm -f "/lab/seeds/${run_id}.json"; fi; elapsed=$(( $(date +%s) - started )); [ "$elapsed" -ge 15 ] || sleep 30; done; python3 /opt/replay_app/index_recordings.py --root /lab >/lab/recordings/index.json'
done

docker ps --filter 'name=bothack-worker-' --format '{{.Names}} {{.Status}} {{.Image}}'
