#!/bin/bash
# xa.sh [xp args]: one xp round (timeout 55s) then fight adjacent hostile letters. Prints short status.
cd "$(dirname "$0")"
timeout 55 ./xp 1 "$@" 2>&1 | grep -aE "round|^07|HP:"
./adjfight.py "${AF_GLYPHS:-abcdfghikmopqrstuvwxyzABCDEGHIJKLMNOPQRSTUVWXYZ&;:}" 10 | grep -av "no adjacent"
