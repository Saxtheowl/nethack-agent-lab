#!/bin/bash
# Container entrypoint:
#   1. starts sshd (port 22 internally → 2223 externally)
#   2. starts the replay web server on :8080
#   3. tails forever
set -e

mkdir -p /data/games /data/logs

# permissions: the 'bot' user runs the games and owns /data
chown -R bot:bot /data || true

# Start sshd
service ssh start || /usr/sbin/sshd -D &
SSHD_PID=$!

# Start replay server as 'bot' (read-only access is enough; uses /data/games)
su - bot -c 'cd /opt/replay && /opt/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8080 --log-level info' \
    > /data/logs/replay.log 2>&1 &
REPLAY_PID=$!

echo "==============================================="
echo "  BotHack container ready"
echo "  SSH (port 22 → host 2225):       ssh -p 2225 bot@<host>"
echo "  Replay UI (port 8080 → 8085):    http://<host>:8085/"
echo "  Start a run loop (as bot):       /opt/runner/loop.py --target 10"
echo "==============================================="

# Keep PID 1 alive
wait
