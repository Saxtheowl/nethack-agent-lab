#!/bin/bash
# soko_loop.sh LAB MAP OX OY PLAN IDX [rounds]
cd "$(dirname "$0")"
LAB=$1; MAP=$2; OX=$3; OY=$4; PLAN=$5; IDX=$6
for r in $(seq "${7:-6}"); do
  w=$(NH_SLOT=4 python3 where3.py $PLAN $OX $OY | grep -o "[0-9]*$"); [ -n "$w" ] && IDX=$w; echo "at $IDX"
  python3 soko_resume.py $LAB $OX $OY $PLAN $IDX _r.json | tail -1 || { echo "RESUME FAIL at $IDX"; exit 1; }
  out=$(python3 soko_exec.py $MAP $OX $OY 0 _r.json 2>&1)
  n=$(echo "$out" | grep -o "^push [0-9]*" | tail -1 | grep -o "[0-9]*"); n=${n:-0}
  IDX=$((IDX+n)); echo "round $r: +$n -> idx $IDX"
  echo "$out" | grep -q "^DONE" && { echo ALLDONE; exit 0; }
  echo "$out" | tail -2 | cut -c1-100
  f=$(NH_SLOT=4 SKIP=F ./hold.sh 6 55 2>&1); echo "$f" | tail -3 | cut -c1-90
  echo "$f" | grep -q "min\|ALARM\|PEACEFUL" && { echo "STOP idx $IDX"; exit 2; }
done
echo "IDX $IDX"
