#!/usr/bin/env bash
# Déploie le projet sur une instance Vast AI et lance un batch compté.
# Usage: scripts/vast_run.sh <ssh_host> <ssh_port> <episodes> <workers> <run_name>
set -euo pipefail

HOST="${1:?ssh host}"
PORT="${2:?ssh port}"
EPISODES="${3:-100}"
WORKERS="${4:-20}"
RUN_NAME="${5:-vast-validation-001}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH=(ssh -o StrictHostKeyChecking=no -p "$PORT" "root@$HOST")

echo "== rsync du projet =="
rsync -az -e "ssh -o StrictHostKeyChecking=no -p $PORT" \
    --exclude '.venv' --exclude '.deps' --exclude 'runs' --exclude '*.log' \
    --exclude '__pycache__' --exclude '*.egg-info' --exclude '.pytest_cache' \
    --exclude 'vendor/nle/.git' --exclude 'vendor/nle/build' \
    "$ROOT/" "root@$HOST:/workspace/mt2/" --rsync-path="mkdir -p /workspace/mt2 && rsync"

echo "== setup distant =="
"${SSH[@]}" bash -s <<'REMOTE'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
if ! command -v cmake >/dev/null || ! command -v flex >/dev/null || ! command -v bison >/dev/null; then
    apt-get update -qq
    apt-get install -y -qq --no-install-recommends \
        build-essential cmake flex bison m4 git bzip2 libbz2-dev zlib1g-dev \
        python3-dev python3-venv > /dev/null
fi
cd /workspace/mt2
if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv .venv
    .venv/bin/pip install -q --upgrade pip
fi
if ! .venv/bin/python -c "import nle" 2>/dev/null; then
    .venv/bin/pip install -q -e vendor/nle
fi
.venv/bin/pip install -q -e .
.venv/bin/python - <<'PY'
from nle import nethack
assert nethack.INTERNAL_SHAPE == (10,)
print("NLE distant prêt (canal in_town actif)")
PY
REMOTE

echo "== lancement du batch $RUN_NAME ($EPISODES épisodes, $WORKERS workers) =="
"${SSH[@]}" "cd /workspace/mt2 && nohup .venv/bin/mt-run --episodes $EPISODES --workers $WORKERS --max-steps 8000 --run-dir runs/$RUN_NAME > runs/$RUN_NAME.log 2>&1 & echo lancé"
echo "Suivi: ssh -p $PORT root@$HOST 'tail -f /workspace/mt2/runs/$RUN_NAME.log'"
