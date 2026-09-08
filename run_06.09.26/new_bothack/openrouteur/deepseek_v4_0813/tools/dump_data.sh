#!/bin/bash
# Extract BotHack's data structures verbatim from the original Clojure project.
# Requires JDK8 + leiningen. Output: bothack/_data.json
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export JAVA_HOME="${JDK8_HOME:-$ROOT/.local/jdk8}"
export PATH="$JAVA_HOME/bin:$ROOT/tools:$PATH"
export JVM_OPTS="-Xmx2g -Dlog4j.configuration=$ROOT/tools/log4j-quiet.properties"
cd "$ROOT/upstream/BotHack"
lein update-in :source-paths conj "\"$ROOT/tools\"" -- run -m cljdump.dumpdata \
  2>/dev/null > "$ROOT/bothack/_data.json"
echo "wrote $ROOT/bothack/_data.json ($(wc -c < "$ROOT/bothack/_data.json") bytes)"