#!/bin/bash
# Feed the differential test cases to the original Clojure BotHack and record
# its answers in artifacts/oracle_answers.txt.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${BOTHACK_SRC:?set BOTHACK_SRC to the BotHack checkout}"
export JAVA_HOME="${JDK8_HOME:?set JDK8_HOME}"
export PATH="$JAVA_HOME/bin:$LEIN_DIR:$PATH"
cd "$SRC"
python3 - "$ROOT" <<'PY' > /tmp/oracle_cases.txt
import sys, os
sys.path.insert(0, sys.argv[1])
from tests.test_differential import cases
for op, arg in cases():
    print(op + "\t" + arg.replace("\n", " "))
PY
JVM_OPTS="-Dlog4j.configuration=file:$ROOT/tools/log4j-quiet.properties" \
    lein update-in :source-paths conj "\"$ROOT/tools\"" -- run -m cljcmp.oracle \
    < /tmp/oracle_cases.txt 2>/dev/null > "$ROOT/artifacts/oracle_answers.txt"
wc -l "$ROOT/artifacts/oracle_answers.txt"
