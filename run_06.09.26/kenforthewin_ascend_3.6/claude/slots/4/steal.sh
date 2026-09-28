#!/bin/bash
# slots/4/steal.sh N [XMAX] : wait N turns (one 's' per turn) outside a shop while the pet carries items out.
# Per-turn checks: stop on HP loss, hunger, non-pet monster (except peaceful shopkeeper @ inside x>XMAX),
# a prompt, or an object glyph appearing at x<=XMAX (outside the shop) = pet dropped loot.
cd "$(dirname "$0")/../.."
export NH_SLOT=4
XMAX=${2:-68}
hp0=""
for i in $(seq "${1:-20}"); do
  python3 scripts/session.py keys s --settle .3 >/dev/null 2>&1
  scr=$(python3 scripts/session.py screen --compact)
  res=$(python3 - "$scr" "$XMAX" "${3:-}" ${WEAKONLY:+x} <<'PY'
import re,sys
s=sys.argv[1]; xmax=int(sys.argv[2])
m=re.search(r'^Map features.*$',s,re.M).group(0)
pl=re.search(r'^PETS.*$',s,re.M); pets=set(re.findall(r'(\d+,\d+)',pl.group(0))) if pl else set()
c=re.search(r'Terminal cursor[^:]*: (\d+),(\d+)',s); hero=f'{c[1]},{c[2]}' if c else ''
bad=[]
for g,x,y in re.findall(r' (\S)@(\d+),(\d+)',m):
    p=f'{x},{y}'
    if p in pets or p==hero or g in sys.argv[3]: continue
    if g=='@' and int(x)>xmax: continue
    if g.isalpha() or g in "&';:~@": bad.append(f'monster {g}@{p}')
    elif g in '[)!?/="(*%' and int(x)<=xmax and int(y)>=20: bad.append(f'loot {g}@{p}')
hp=re.search(r'HP:(\d+)\((\d+)\)',s)
print(hp[1] if hp else 0)
if re.search(r"Weak|Faint" if len(sys.argv)>4 else r"Hungry|Weak|Faint",s): bad.append("hunger")
msgs=[l for l in s.splitlines() if re.match(r'0[1-9] ',l)]
last=msgs[-1] if msgs else ''
if re.search(r'--More--|\[yn|stole',last) or 'stole' in s: bad.append('prompt')
print(';'.join(bad))
PY
)
  hp=$(echo "$res" | head -1); why=$(echo "$res" | sed -n 2p)
  [ -z "$hp0" ] && hp0=$hp
  [ "$hp" -lt $((hp0 - ${4:-0})) ] && why="HP loss $hp0->$hp $why"
  hp0=$hp
  if [ -n "$why" ]; then echo "turn $i STOP: $why"; break; fi
done
echo "$scr" | grep -E '^0[5-7] |^34|^Map|^PETS'
