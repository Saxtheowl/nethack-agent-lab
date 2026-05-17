#!/bin/sh
# Wrapper that BotHack invokes as :nh-command.
# Sets a per-game playground (unique save dir, unique HOME), forwards
# NETHACK_SEED for deterministic RNG, and NETHACKDIR per worker so
# concurrent games don't fight over /nh343/var/perm (fcntl lock).
#
# Inherited from the parent process (loop.py):
#   NH_GAME_DIR        — unique workdir for this game (HOME, ttyrec dest)
#   NETHACK_SEED       — integer to seed srandom() (read by our patch)
#   WORKER_ID          — 1..N, picks /nh343-wN as NETHACKDIR
#   NETHACKOPTIONS     — path to the .nethackrc to use
set -eu

: "${NH_GAME_DIR:=/tmp/nh-game}"
: "${WORKER_ID:=0}"
mkdir -p "$NH_GAME_DIR"

export HOME="$NH_GAME_DIR"
: "${NETHACKOPTIONS:=/opt/bothack/bothack.nethackrc}"
export NETHACKOPTIONS

# Per-worker isolated playground.
# WORKER_ID=0 means "use the default /nh343 (serial mode, shared var/)".
# Each game starts fresh: nuke save dir and TRUNCATE (not delete) perm —
# NetHack opens perm with O_RDWR (no O_CREAT) and loops forever on
# fcntl(-1, F_SETLK, ...) if the file doesn't exist.
if [ "$WORKER_ID" != "0" ]; then
    export NETHACKDIR="/nh343-w${WORKER_ID}"
    rm -f "$NETHACKDIR"/save/* 2>/dev/null || true
    : > "$NETHACKDIR/perm" 2>/dev/null || true
else
    rm -f /nh343/var/save/* 2>/dev/null || true
    : > /nh343/var/perm 2>/dev/null || true
fi

cd "$NH_GAME_DIR"
exec /nh343/nethack.343-nao "$@"
