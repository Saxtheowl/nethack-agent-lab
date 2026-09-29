#!/bin/bash
# worker_sync.sh: keeps the PC and miniforum-worker in step while the tools
# (recorder, dashboard, slot games) move to the worker. Runs on the PC in
# tmux session `sync`. Every 5 s: PC -> worker for slots still played here
# (their game folders, slot/feed files) + the PC's load figures, and memory/
# both ways (the player agents write their journals on the worker, the
# orchestrator edits lessons here): the newer file wins (rsync -u).
# Every 60 s: worker -> PC for slots living on the worker and the agents'
# own helpers in slots/ (for git history).
R="$(cd "$(dirname "$0")/.." && pwd -P)"
cd "$R"
SSH="ssh -o BatchMode=yes -o ControlMaster=auto -o ControlPath=/tmp/ssh-nh-sync-%C -o ControlPersist=900"
W=miniforum-worker
gid() { python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('game_id',''))" "$1" 2>/dev/null; }
n=0
while true; do
  python3 - > .runtime/pc-stats.json.tmp <<'PY'
import json, os, shutil
m = dict(l.split(':', 1) for l in open('/proc/meminfo') if ':' in l)
kb = lambda k: int(m[k].split()[0]) * 1024
du = shutil.disk_usage('.')
import subprocess
git = lambda *a: subprocess.run(['git', *a], capture_output=True, text=True).stdout.strip()
last = git('log', '-1', '--format=%ct|%s').split('|', 1)
g = {'unpushed': int(git('rev-list', '--count', 'origin/main..main') or 0), 'last_push': int(git('log', '-1', '--format=%ct', 'origin/main') or 0),
     'last_commit': {'t': int(last[0] or 0), 'msg': last[1] if len(last) > 1 else ''}}
print(json.dumps({'git': g, 'cores': os.cpu_count(), 'load': list(os.getloadavg()), 'mem_total': kb('MemTotal'),
                  'mem_avail': kb('MemAvailable'), 'disk_total': du.total, 'disk_used': du.used, 'disk_free': du.free}))
PY
  mv .runtime/pc-stats.json.tmp .runtime/pc-stats.json
  push=(.runtime/pc-stats.json .runtime/style-plan.json config/styles.json)
  pull=()
  for s in 1 2 3 4 5 6 7 8; do
    if [ "$(cat .runtime/where-$s 2>/dev/null)" = worker ]; then
      pull+=(.runtime/slot-$s.json .runtime/public-feed-$s.json)
      g=$(gid .runtime/slot-$s.json); [ -n "$g" ] && pull+=("runs/games/$g")
    else
      push+=(.runtime/slot-$s.json .runtime/public-feed-$s.json)
      g=$(gid .runtime/slot-$s.json); [ -n "$g" ] && push+=("runs/games/$g")
    fi
  done
  rsync -aR -e "$SSH" --exclude analytics.json "${push[@]}" "$W:$R/" 2>/dev/null
  rsync -au -e "$SSH" memory/ "$W:$R/memory/" 2>/dev/null
  rsync -au -e "$SSH" "$W:$R/memory/" memory/ 2>/dev/null
  if [ $((n % 12)) = 0 ] && [ ${#pull[@]} -gt 0 ]; then
    for p in "${pull[@]}"; do rsync -aR -e "$SSH" "$W:$R/./$p" . 2>/dev/null; done
    rsync -au -e "$SSH" --exclude __pycache__ "$W:$R/slots/" slots/ 2>/dev/null
    rsync -a -e "$SSH" "$W:$R/runs/wish_scum/" runs/wish_scum/ 2>/dev/null
  fi
  n=$((n + 1))
  sleep 5
done
