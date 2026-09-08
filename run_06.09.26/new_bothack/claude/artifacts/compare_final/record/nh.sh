#!/bin/bash
export NETHACKOPTIONS="@/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/upstream/bothack.nethackrc"
export TERM=xterm
export HOME="/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/artifacts/compare_final/record/home"
export USER="origbot"
export PTY_TAP_LOG="/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/artifacts/compare_final/record/pty_tap.log"
exec python3 "/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/tools/pty_tap.py" "/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/upstream/nh343/nethack.343-nao" -u "origbot"
