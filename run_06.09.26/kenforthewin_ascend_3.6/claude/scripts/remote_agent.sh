#!/bin/bash
# remote_agent.sh <slot> <label> <prompt-file> <journal>: start a player agent
# for a slot as its own headless Claude Code on miniforum-worker, next to the
# game (the orchestrator stays on the PC; user decision 2026-09-29, "option 2").
#
# STRICT PERMISSIONS (dontAsk: anything not listed is refused, never asked):
#   - Bash: only its own slot's tools, slots/N/* (v, k, t, look, inv, w, ...)
#   - Read/Grep/Glob: the project tree only (never ~/.ssh, ~/.claude)
#   - Write/Edit: its journal, memory/astra-style.md (lessons), slots/N/**
#   - no web, no sub-agents, no other command
# NH_HOST=worker makes the slots/N/* tools run right there (no ssh).
#   Transcript: runs/agents/<label>.jsonl (stream-json), exit code .rc
#   Wait for the end report:  scripts/agent_wait.sh <slot>   (--stop to end it)
set -euo pipefail
N=$1; LABEL=$2; PROMPT=$3; JOURNAL=$4
R="$(cd "$(dirname "$0")/.." && pwd -P)"
S=/tmp/nhstream-$(printf %s "$R" | sha256sum | cut -c1-12).sock
SSH="ssh -o BatchMode=yes -o ControlMaster=no -o ControlPath=/tmp/ssh-nh-%C"
A=runs/agents
mkdir -p "$R/$A"
python3 - "$N" "$JOURNAL" > "$R/$A/$LABEL.settings.json" <<'PY'
import json, sys
n, journal = sys.argv[1], sys.argv[2]
print(json.dumps({'permissions': {
    'defaultMode': 'dontAsk',
    'allow': [f'Bash(slots/{n}/*)', 'Read(./**)', 'Grep', 'Glob', 'TodoWrite',
              f'Edit({journal})', f'Write({journal})', 'Edit(memory/astra-style.md)',
              f'Edit(slots/{n}/**)', f'Write(slots/{n}/**)'],
    'deny': ['WebFetch', 'WebSearch', 'Agent', 'Read(~/.ssh/**)', 'Read(~/.claude/**)',
             'Read(~/.config/**)', 'Read(//etc/**)'],
}}, indent=1))
PY
$SSH miniforum-worker "mkdir -p $R/$A"
OLD=$(cat "$R/.runtime/agent-$N" 2>/dev/null || true)
if $SSH miniforum-worker "tmux -S $S has-session -t agent$N 2>/dev/null"; then
  if [ -n "$OLD" ] && $SSH miniforum-worker "test -e $R/$A/$OLD.rc"; then
    $SSH miniforum-worker "tmux -S $S kill-session -t agent$N"  # finished agent, pane kept by remain-on-exit
  else
    echo "agent$N is already running on the worker" >&2; exit 1
  fi
fi
rsync -a -e "$SSH" "$PROMPT" "miniforum-worker:$R/$A/$LABEL.prompt"
rsync -a -e "$SSH" "$R/$A/$LABEL.settings.json" "miniforum-worker:$R/$A/"
$SSH miniforum-worker "tmux -S $S new-session -d -s agent$N -x 200 -y 50 \
  \"cd $R && NH_HOST=worker NH_SLOT=$N ~/.local/bin/claude -p --settings $A/$LABEL.settings.json \
  --permission-mode dontAsk --output-format stream-json --verbose \
  < $A/$LABEL.prompt > $A/$LABEL.jsonl 2> $A/$LABEL.err; echo \\\$? > $A/$LABEL.rc\""
echo "$LABEL" > "$R/.runtime/agent-$N"
echo "agent$N started on the worker: $A/$LABEL.jsonl"
