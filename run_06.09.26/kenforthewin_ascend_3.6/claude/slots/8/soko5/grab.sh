#!/bin/bash
# print map rows as ASCII with screen x ruler (run via slots/8/w soko5/grab.sh)
cd "$(dirname "$0")/../../.."
NH_SLOT=8 python3 scripts/session.py screen | python3 -c '
import sys
L=sys.stdin.read().split("\n")
walls=set("│─┌┐└┘├┤┬┴┼")
for i,l in enumerate(L):
    if l[:2].strip().isdigit() and 10<=int(l[:2])<=31:
        body=l[3:] if len(l)>3 else ""
        out="".join("#" if c in walls else "." if c=="·" else c for c in body)
        print(l[:2], out)
'
