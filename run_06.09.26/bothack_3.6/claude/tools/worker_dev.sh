#!/bin/bash
# Single games, scenarios and debug replays on the worker, in a code
# directory of their own (~/bothack36-dev) so that they can be synced at any
# time without touching a running series (~/bothack36).
#
#   tools/worker_dev.sh sync                       # push code, rebuild engine if needed
#   tools/worker_dev.sh run <name> <rungame args>  # detached game -> runs/dev/<name>
#   tools/worker_dev.sh status [name...]           # live state (all dev runs by default)
#   tools/worker_dev.sh wait <name...>             # block until they have result.json
#   tools/worker_dev.sh fetch <name...>            # -> runs/worker-dev/<name>
#   tools/worker_dev.sh ssh <command>              # run a command in the dev dir
#
# Example:
#   tools/worker_dev.sh sync
#   tools/worker_dev.sh run astral-s101 --scenario astral-altar --seed 101 --trace
#   tools/worker_dev.sh wait astral-s101 && tools/worker_dev.sh fetch astral-s101
set -euo pipefail
here="$(cd "$(dirname "$0")/.." && pwd)"
host="${WORKER_HOST:-miniforum-worker}"
dir="${WORKER_DEV_DIR:-bothack36-dev}"
SSH="ssh -o BatchMode=yes $host"
cmd="${1:-}"; shift || true

case "$cmd" in
sync)
    "$here/tools/sync_worker.sh" "$host" "$dir" >/dev/null
    # rsync keeps mtimes: rebuild when an engine source is newer than the
    # installed binary (or there is no binary yet)
    $SSH "cd $dir && mkdir -p runs/dev && \
        if [ ! -x build/install/nhdir/nethack ] || \
           [ -n \"\$(find engine/nethack-3.6.7 engine/hints engine/build.sh \
                -newer build/install/nhdir/nethack \
                \\( -name '*.[chly]' -o -name '*.des' -o -name 'linux-bot*' \
                   -o -name 'build.sh' -o -name 'Makefile*' \\) | head -1)\" ]; then \
            HEADLESS=1 JOBS=4 engine/build.sh > build.out 2>&1 \
              || { echo 'engine build failed (see ~/$dir/build.out)'; exit 1; }; \
            echo 'engine rebuilt'; \
        fi"
    echo "synced to $host:$dir"
    ;;
run)
    name="$1"; shift
    args="$(printf '%q ' "$@")"
    $SSH "cd $dir && rm -rf runs/dev/$name && mkdir -p runs/dev && \
        (setsid nohup python3 -m nhbot.rungame --out runs/dev/$name $args \
            > runs/dev/$name.out 2>&1 < /dev/null &) && echo launched $name"
    ;;
status)
    if [ $# -eq 0 ]; then
        $SSH "cd $dir && for d in runs/dev/*/; do [ -d \"\$d\" ] && python3 tools/live.py \$d | cut -c1-200; done; true"
    else
        for n in "$@"; do
            $SSH "cd $dir && python3 tools/live.py runs/dev/$n | cut -c1-200"
        done
    fi
    ;;
wait)
    checks=""
    for n in "$@"; do checks="$checks [ -f runs/dev/$n/result.json ] &&"; done
    $SSH "cd $dir && until $checks true; do sleep 20; done"
    for n in "$@"; do
        $SSH "cd $dir && python3 tools/live.py runs/dev/$n | cut -c1-200"
    done
    ;;
fetch)
    for n in "$@"; do
        mkdir -p "$here/runs/worker-dev/$n"
        rsync -az --exclude 'nhdir/save/' --exclude 'nhdir/*lock*' \
            "$host:$dir/runs/dev/$n/" "$here/runs/worker-dev/$n/"
        echo "fetched runs/worker-dev/$n"
    done
    ;;
ssh)
    $SSH "cd $dir && $*"
    ;;
*)
    sed -n 2,17p "$0"; exit 2
    ;;
esac
