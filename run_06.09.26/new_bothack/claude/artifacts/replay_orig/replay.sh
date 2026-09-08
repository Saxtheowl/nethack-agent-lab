#!/bin/bash
export REPLAY_TAP="/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/artifacts/orig_seed1/pty_tap.log"
export REPLAY_KEYS="/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/artifacts/replay_orig/orig_keys.bin"
export REPLAY_DELAY="0.002"
export REPLAY_STATUS="/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/artifacts/replay_orig/replay_status.txt"
exec python3 "/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/tools/replay_server.py"
