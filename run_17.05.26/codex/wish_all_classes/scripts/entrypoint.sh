#!/bin/bash
set -e

# Generate SSH host keys if missing
if [ ! -f /etc/ssh/ssh_host_rsa_key ]; then
    ssh-keygen -A
fi

# Ensure data directories exist
mkdir -p /data/sessions /data/saves /data/claimed_wishes /data/game_hackdirs
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

# Build one HACKDIR per role. Saves still share /data/saves.
for role in Archeologist Barbarian Caveman Healer Knight Monk Priest Ranger Rogue Samurai Tourist Valkyrie Wizard; do
    role_dir="/data/hackdirs/$role"
    if [ ! -d "$role_dir" ]; then
        mkdir -p "$role_dir"
        cp -a /opt/nethack/nethackdir/. "$role_dir/"
    fi
    cp -p /opt/nethack/nethackdir/nethack "$role_dir/nethack"
    rm -rf "$role_dir/save"
    ln -s /data/saves "$role_dir/save"
    if grep -q '^MAXPLAYERS=' "$role_dir/sysconf"; then
        sed -i 's/^MAXPLAYERS=.*/MAXPLAYERS=60/' "$role_dir/sysconf"
    else
        echo 'MAXPLAYERS=60' >> "$role_dir/sysconf"
    fi
    chown -R nethack:nethack "$role_dir"
    chown -h nethack:nethack "$role_dir/save"
done

# Install player nethackrc as default for the nethack user
cp /opt/nethack/nethackrc.player /home/nethack/.nethackrc
chown nethack:nethack /home/nethack/.nethackrc

# Raise the default HACKDIR cap. This image patches NetHack's old hard limit
# from 25 to 60 so all role pools can be active at once.
if grep -q '^MAXPLAYERS=' /opt/nethack/nethackdir/sysconf; then
    sed -i 's/^MAXPLAYERS=.*/MAXPLAYERS=60/' /opt/nethack/nethackdir/sysconf
else
    echo 'MAXPLAYERS=60' >> /opt/nethack/nethackdir/sysconf
fi

# Keep all role pools warm by default.
touch /data/bots_enabled
chown nethack:nethack /data/bots_enabled

# Start wish manager daemon.
su -c "nohup python3 /opt/nethack/bot/wish_manager.py >> /data/wish_manager.log 2>&1 &" nethack

echo "=== Super NetHack Wish Server started ==="
echo "Connect: ssh nethack@<host> -p 2223 (no password)"

# Start sshd in foreground
exec /usr/sbin/sshd -D -e
