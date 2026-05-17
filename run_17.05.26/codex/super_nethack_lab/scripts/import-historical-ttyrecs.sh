#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" = "0" ]; then
  mkdir -p /lab/recordings /lab/wins /lab/seeds /lab/logs /lab/workspace
  chown -R botlab:botlab /lab/recordings /lab/wins /lab/seeds /lab/logs /lab/workspace
  exec su - botlab -c /opt/botlab_scripts/import-historical-ttyrecs.sh
fi

mkdir -p /lab/recordings/historical /lab/wins
cp -f /opt/bothack/ttyrec/*.ttyrec.xz /lab/recordings/historical/

rm -rf /lab/wins/first-bot-asc-ever-valk
rm -rf /lab/wins/samurai-bot-asc
rm -f /lab/recordings/historical/samurai-bot-asc.ttyrec.xz

python3 /opt/replay_app/index_recordings.py --root /lab >/lab/recordings/index.json
echo "Imported BotHack historical ttyrecs into /lab/recordings/historical and known wins into /lab/wins."
