#!/bin/bash
# Pack a worker's recordings for transfer, keeping only what a replay needs.
#
#   tools/vast/collect.sh OUT [ARCHIVE]
#
# A replay needs the capture and the recording verdict.  The original's DEBUG
# log is 20+ MB per game and is only needed when a divergence has to be named
# (tools/compare_decisions.py), so it is compressed separately and can be left
# behind if bandwidth is the binding constraint.
set -eu
OUT="${1:?outdir}"
ARCHIVE="${2:-$OUT/taps.tar.zst}"
cd "$OUT"

comp=zstd
command -v zstd >/dev/null || comp=gzip
ext=zst; [ "$comp" = gzip ] && ext=gz
ARCHIVE="${ARCHIVE%.zst}.$ext"

tar -cf - seed*/tap.log seed*/recording.json seed*/nh.sh 2>/dev/null \
  | $comp -c > "$ARCHIVE"
echo "captures  -> $ARCHIVE ($(du -h "$ARCHIVE" | cut -f1))"

if ls seed*/bothack.log >/dev/null 2>&1; then
  tar -cf - seed*/bothack.log | $comp -c > "${ARCHIVE%.$ext}-logs.$ext"
  echo "orig logs -> ${ARCHIVE%.$ext}-logs.$ext ($(du -h "${ARCHIVE%.$ext}-logs.$ext" | cut -f1))"
fi
