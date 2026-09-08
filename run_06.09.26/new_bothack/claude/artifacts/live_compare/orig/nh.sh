#!/bin/bash
export NETHACKOPTIONS="@/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/upstream/bothack.nethackrc"
export TERM=xterm
export HOME="/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/artifacts/live_compare/orig/home"
export USER=claudebot
export PTY_TAP_LOG="/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/artifacts/live_compare/orig/tap.log"
export NETHACK_FIXED_SEED="4242"
export PTY_TAP_SETTLE="0.03"
export LD_PRELOAD="/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/artifacts/det_rng.so"
mkdir -p "$HOME"
exec python3 "/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/tools/pty_tap.py" "/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/upstream/nh343/nethack.343-nao" -u claudebot
