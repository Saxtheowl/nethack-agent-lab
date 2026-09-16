#!/usr/bin/env bash

for f in \
/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/claude/docs/{RESULTS,LIMITATIONS,TESTS,PORT,MATCHING_100_PLAN,HANDOFF,VAST,RUNNING,NETHACK}.md \
/home/roro/work/projects/super_nethack/run_06.09.26/new_bothack/codex_2/docs/{RESULTS,LIMITATIONS,TESTS,PORT,MATCHING_100_PLAN,HANDOFF,VAST,RUNNING,NETHACK,PORTAGE_LANGUAGE_ANALYSIS}.md
do
  printf '\n\n==================== %s ====================\n\n' "$f"
  cat "$f"
done | xclip -selection clipboard
