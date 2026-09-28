#!/bin/bash
# Kills player helper processes (cwd under slots/) that use more than 2.5 GB
# RSS, so one runaway solver cannot starve the other games. Logs to runs/.
root="$(cd "$(dirname "$0")/.." && pwd -P)"
while true; do
  for pid in $(pgrep -f python3); do
    cwd=$(readlink /proc/$pid/cwd 2>/dev/null) || continue
    [[ "$cwd" == "$root/slots/"* ]] || continue
    rss=$(awk '/VmRSS/{print $2}' /proc/$pid/status 2>/dev/null)
    [ -n "$rss" ] && [ "$rss" -gt 2500000 ] && {
      echo "$(date -Is) killed $pid rss=${rss}kB cwd=$cwd cmd=$(tr '\0' ' ' < /proc/$pid/cmdline | cut -c1-120)" >> "$root/runs/watchdog.log"
      kill "$pid"; }
  done
  sleep 10
done
