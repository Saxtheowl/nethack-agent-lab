#!/usr/bin/env bash
set -euo pipefail

password="${BOTLAB_SSH_PASSWORD:-botlab}"
echo "botlab:${password}" | chpasswd

if ! grep -q '^PermitRootLogin no' /etc/ssh/sshd_config; then
  printf '\nPermitRootLogin no\nPasswordAuthentication yes\n' >> /etc/ssh/sshd_config
fi

/usr/sbin/sshd
exec python3 /opt/replay_app/server.py --host 0.0.0.0 --port 8080 --root /lab
