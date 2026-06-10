#!/bin/bash
set -e

# Generate SSH host keys if missing
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    ssh-keygen -A
fi

# Ensure data directories exist
mkdir -p /data/sessions /data/saves /data/claimed_wishes
chown -R nethack:nethack /data

# Ensure nethack save directory has correct permissions
chmod -R 775 /opt/nethack/nethackdir
chmod 2775 /opt/nethack/nethackdir/save 2>/dev/null || true

# Symlink save dir to persistent volume so saves survive restarts
if [ ! -L /opt/nethack/nethackdir/save ]; then
    rm -rf /opt/nethack/nethackdir/save
    ln -s /data/saves /opt/nethack/nethackdir/save
    chown -h nethack:nethack /opt/nethack/nethackdir/save
fi

# Install player nethackrc as default for the nethack user
cp /opt/nethack/nethackrc.player /home/nethack/.nethackrc
chown nethack:nethack /home/nethack/.nethackrc

# Raise NetHack's simultaneous game cap so resume attempts are not blocked
# when wish sessions are active.
if grep -q '^MAXPLAYERS=' /opt/nethack/nethackdir/sysconf; then
    sed -i 's/^MAXPLAYERS=.*/MAXPLAYERS=25/' /opt/nethack/nethackdir/sysconf
else
    echo 'MAXPLAYERS=25' >> /opt/nethack/nethackdir/sysconf
fi

# Start wish manager daemon (waits for /data/bots_enabled flag to activate)
su -c "nohup python3 /opt/nethack/bot/wish_manager.py >> /data/wish_manager.log 2>&1 &" nethack

echo "=== Super NetHack Wish Server started ==="
echo "Connect: ssh nethack@<host> -p 2222 (no password)"

# Start sshd in foreground
exec /usr/sbin/sshd -D -e
