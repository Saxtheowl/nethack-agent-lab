#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" = "0" ]; then
  mkdir -p /lab/recordings /lab/wins /lab/seeds /lab/logs /lab/workspace
  chown -R botlab:botlab /lab/recordings /lab/wins /lab/seeds /lab/logs /lab/workspace
  exec su botlab -c "JAVA_HOME=/opt/java/openjdk PATH=/opt/java/openjdk/bin:\$PATH BOTLAB_TIMEOUT='${BOTLAB_TIMEOUT:-36h}' /opt/botlab_scripts/run-until-10-wins.sh '${1:-10}'"
fi

export JAVA_HOME=/opt/java/openjdk
export PATH="$JAVA_HOME/bin:$PATH"
unset CLASSPATH

target="${1:-10}"
mkdir -p /lab/wins /lab/recordings /lab/seeds /lab/logs

count_wins() {
  find /lab/wins -mindepth 1 -maxdepth 1 -type d | wc -l
}

attempt=0
while [ "$(count_wins)" -lt "$target" ]; do
  attempt=$((attempt + 1))
  run_id="attempt-${attempt}-$(date -u +%Y%m%dT%H%M%SZ)"
  echo "Starting ${run_id}; wins=$(count_wins)/${target}"
  /opt/botlab_scripts/run-bothack-once.sh "$run_id" || true
  if [ ! -d "/lab/wins/${run_id}" ]; then
    rm -rf "/lab/recordings/${run_id}"
    rm -f "/lab/seeds/${run_id}.json"
    rm -f "/lab/logs/${run_id}.stdout.log" "/lab/logs/${run_id}.stderr.log"
  fi
done

python3 /opt/replay_app/index_recordings.py --root /lab >/lab/recordings/index.json
echo "Done; wins=$(count_wins)/${target}"
