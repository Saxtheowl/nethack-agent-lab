#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" = "0" ]; then
  mkdir -p /lab/recordings /lab/wins /lab/seeds /lab/logs /lab/workspace
  chown -R botlab:botlab /lab/recordings /lab/wins /lab/seeds /lab/logs /lab/workspace
  exec su botlab -c "JAVA_HOME=/opt/java/openjdk PATH=/opt/java/openjdk/bin:\$PATH BOTLAB_TIMEOUT='${BOTLAB_TIMEOUT:-36h}' /opt/botlab_scripts/run-bothack-once.sh '${1:-}'"
fi

export JAVA_HOME=/opt/java/openjdk
export PATH="$JAVA_HOME/bin:$PATH"
unset CLASSPATH

run_id="${1:-$(date -u +%Y%m%dT%H%M%SZ)}"
run_dir="/lab/recordings/${run_id}"
mkdir -p "$run_dir"

cd /opt/bothack
rm -f ./*.ttyrec ./*.log ./*.log.*
rm -rf /opt/nh343/nh343/var/save/*
rm -f /opt/nh343/nh343/var/*smartbot3* /opt/nh343/nh343/var/*Smartbot3*

seed="${BOTLAB_NETHACK_SEED:-$(od -An -N4 -tu4 /dev/urandom | tr -d ' ')}"
export NETHACK_SEED="$seed"
seed_file="/lab/seeds/${run_id}.json"
cat > "$seed_file" <<JSON
{
  "run_id": "${run_id}",
  "started_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "nethack": "3.4.3",
  "seed": ${seed},
  "seed_env": "NETHACK_SEED",
  "engine": "BotHack mainbot",
  "seed_note": "This run uses patched NetHack 3.4.3 setrandom() with NETHACK_SEED, inherited by BotHack HandlerPTY."
}
JSON

set +e
timeout "${BOTLAB_TIMEOUT:-36h}" bash -lc 'lein compile && LD_LIBRARY_PATH=jta26/jni/linux lein run config/lab-shell-config.edn' \
  >"/lab/logs/${run_id}.stdout.log" 2>"/lab/logs/${run_id}.stderr.log"
status=$?
set -e

shopt -s nullglob
for file in ./*.ttyrec ./*.log ./*.log.*; do
  mv "$file" "$run_dir/"
done

record="/opt/nh343/nh343/var/record"
xlog="/opt/nh343/nh343/var/logfile"
cp -f "$record" "$run_dir/record" 2>/dev/null || true
cp -f "$xlog" "$run_dir/logfile" 2>/dev/null || true

if grep -qi 'ascended' "$run_dir"/record "$run_dir"/logfile 2>/dev/null; then
  mkdir -p "/lab/wins/${run_id}"
  cp -a "$run_dir"/. "/lab/wins/${run_id}/"
  cp -f "$seed_file" "/lab/wins/${run_id}/seed.json"
fi

python3 /opt/replay_app/index_recordings.py --root /lab >/lab/recordings/index.json
exit "$status"
