#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

NLE_COMMIT="2319f2989f0035685017e9ea13c83b2546fe477c"
if [[ ! -d vendor/nle/.git ]]; then
    mkdir -p vendor
    git clone https://github.com/NetHack-LE/nle.git vendor/nle
    git -C vendor/nle checkout "$NLE_COMMIT"
fi

if git -C vendor/nle apply --reverse --check "$ROOT/patches/nle-367-minetown.patch" >/dev/null 2>&1; then
    : # Patch already present.
else
    git -C vendor/nle apply --check "$ROOT/patches/nle-367-minetown.patch"
    git -C vendor/nle apply "$ROOT/patches/nle-367-minetown.patch"
fi

mkdir -p .deps/debs .deps/root
if [[ ! -x .deps/root/usr/bin/flex || ! -x .deps/root/usr/bin/bison || ! -x .deps/root/usr/bin/m4 ]]; then
    (
        cd .deps/debs
        apt-get download flex bison m4
        for deb in ./*.deb; do
            dpkg-deb -x "$deb" ../root
        done
    )
fi

source scripts/env.sh
uv venv --python python3.12 --allow-existing .venv
uv pip install --python .venv/bin/python --reinstall -e vendor/nle
uv pip install --python .venv/bin/python -e . pytest

.venv/bin/python - <<'PY'
from nle import nethack
assert nethack.BLSTATS_SHAPE == (27,)
assert nethack.INTERNAL_SHAPE == (10,)
print("NLE prêt: NetHack 3.6.7, canal interne d'évaluation actif")
PY

.venv/bin/pytest -q tests/test_env.py
echo "Installation terminée. Lancez: .venv/bin/mt-run --episodes 4 --workers 4"
