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
#
# Each game starts fresh. We must clear:
#   • save/*  — actual saved games (.gz)
#   • <uid><plname>.[0-9]* — per-level state files in the dir root. When a
#     previous game was KILLED (not saved cleanly), NetHack detects these
#     and prompts "There is already a game in progress under your name.
#     [y]Destroy / [r]Recover / [n]Cancel" — BotHack doesn't expect that
#     prompt and stalls forever on it.
#   • bon*.gz — bones files left by dead characters. Less critical (our
#     rcfile sets OPTIONS=!bones), but the per-worker dir might still
#     accumulate them.
# perm must be TRUNCATED (not deleted) — NetHack opens it with O_RDWR
# (no O_CREAT) and otherwise loops on fcntl(-1, F_SETLK, ...).
if [ "$WORKER_ID" != "0" ]; then
    export NETHACKDIR="/nh343-w${WORKER_ID}"
    DIR="$NETHACKDIR"
else
    DIR="/nh343/var"
fi
rm -f "$DIR"/save/* 2>/dev/null || true
rm -f "$DIR"/0BotHack.[0-9]* "$DIR"/0BotHack 2>/dev/null || true
rm -f "$DIR"/bon[A-Za-z0-9]*.gz 2>/dev/null || true
: > "$DIR/perm" 2>/dev/null || true

cd "$NH_GAME_DIR"
exec /nh343/nethack.343-nao "$@"
