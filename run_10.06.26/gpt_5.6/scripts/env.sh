#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$ROOT/.deps/root/usr/bin:$ROOT/.venv/bin:$PATH"
export BISON_PKGDATADIR="$ROOT/.deps/root/usr/share/bison"
export M4="$ROOT/.deps/root/usr/bin/m4"
