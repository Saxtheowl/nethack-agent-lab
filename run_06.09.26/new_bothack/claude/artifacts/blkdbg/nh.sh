#!/bin/bash
export NETHACKOPTIONS="@/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/upstream/bothack.nethackrc"
export TERM=xterm
export HOME="/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/artifacts/blkdbg/home"
export USER=bot3
export PTY_TAP_LOG="/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/artifacts/blkdbg/tap.log"
export PTY_TAP_SETTLE="0.25"
export PTY_TAP_PIECE_DELAY="0.015"
export PTY_TAP_IDLE="1"
export NETHACK_FIXED_SEED="40005"
export LD_PRELOAD="/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/artifacts/det_rng.so"
mkdir -p "$HOME"
exec python3 "/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/tools/pty_tap.py" "/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/upstream/nh343/nethack.343-nao" -u bot3
