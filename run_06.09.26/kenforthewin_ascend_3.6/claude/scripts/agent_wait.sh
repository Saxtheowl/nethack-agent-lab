#!/bin/bash
# agent_wait.sh <slot> [--stop]: wait (from the PC) until the slot's remote
# player agent ends, then print its final report (the agent's last message).
# The orchestrator runs it in the background: when it exits, the report is in
# its output. --stop ends the agent first (its game keeps running).
N=$1
R="$(cd "$(dirname "$0")/.." && pwd -P)"
S=/tmp/nhstream-$(printf %s "$R" | sha256sum | cut -c1-12).sock
# ControlMaster=no: reuse a shared connection if there is one, never leave a
# background master holding our output open
SSH="ssh -o BatchMode=yes -o ControlMaster=no -o ControlPath=/tmp/ssh-nh-%C"
LABEL=$(cat "$R/.runtime/agent-$N" 2>/dev/null) || { echo "no agent recorded for slot $N" >&2; exit 1; }
# --stop: end the agent now (the game itself just waits for keys); the killed
# pane never writes its .rc, so write it here
if [ "${2:-}" = --stop ]; then
  $SSH miniforum-worker "tmux -S $S kill-session -t agent$N 2>/dev/null; cd $R/runs/agents && [ -e $LABEL.rc ] || echo stopped > $LABEL.rc"
fi
# the agent writes <label>.rc when it ends (the tmux pane itself stays: remain-on-exit)
until $SSH miniforum-worker "test -e $R/runs/agents/$LABEL.rc"; do sleep 60; done
$SSH miniforum-worker "tmux -S $S kill-session -t agent$N" 2>/dev/null
$SSH miniforum-worker "cd $R && python3 - runs/agents/$LABEL.jsonl" <<'PY'
import json, sys
last, result, usage = None, None, None
for line in open(sys.argv[1]):
    try:
        e = json.loads(line)
    except json.JSONDecodeError:
        continue
    if e.get('type') == 'result':
        result, usage = e.get('result'), (e.get('num_turns'), e.get('duration_ms'), e.get('total_cost_usd'))
    elif e.get('type') == 'assistant':
        texts = [c.get('text') for c in e.get('message', {}).get('content', []) if c.get('type') == 'text']
        if any(texts):
            last = '\n'.join(t for t in texts if t)
print(f'=== slot agent ended (turns, ms, cost): {usage}')
print(result or last or '(no final message: see runs/agents/*.err on the worker)')
PY
