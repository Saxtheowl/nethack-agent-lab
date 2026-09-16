#!/bin/bash
# Rejouer une partie ascensionnée dans le terminal.
#
#   tools/watch_ascension.sh            # liste les ascensions disponibles
#   tools/watch_ascension.sh 1          # rejoue la premiere
#   tools/watch_ascension.sh 1 -s 20    # 20x plus vite (ttyplay -s)
#
# Les parties durent 7 h en temps reel : sans acceleration, la relecture
# dure autant.  -s 200 ramene ca a ~2 minutes, -s 20 a ~20 minutes.
# Pendant la lecture : espace = pause, f = avance, 1/2 = vitesse normale.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="$ROOT/artifacts/ASCENSION"
mapfile -t RECS < <(find "$DIR" -name '*.ttyrec' 2>/dev/null | sort)

if [ "${#RECS[@]}" -eq 0 ]; then
  echo "Aucun ttyrec dans $DIR" >&2; exit 1
fi

# Le xlogfile rapatrie dit quel joueur a ascensionne et avec quel score : sans
# ca, un numero dans une liste de fichiers ne dit rien de ce qu'on va regarder.
xlog_line () {
  local g="$1"
  local who; who=$(basename "$(dirname "$g")")
  python3 - "$DIR" "$who" <<'PYEOF' 2>/dev/null
import sys, os, glob
d, want = sys.argv[1], sys.argv[2]
for f in glob.glob(os.path.join(d, '**', 'asc.xlog'), recursive=True):
    for l in open(f):
        r = dict(kv.split('=', 1) for kv in l.strip().split(':') if '=' in kv)
        print("%-5s %12s pts  %6s tours  %dh%02d" % (
            r.get('name', '?'), format(int(r.get('points', 0)), ','),
            format(int(r.get('turns', 0)), ','),
            int(r.get('realtime', 0)) // 3600,
            (int(r.get('realtime', 0)) % 3600) // 60))
PYEOF
}

if [ $# -eq 0 ]; then
  echo "Ascensions disponibles :"
  i=1
  for r in "${RECS[@]}"; do
    sz=$(du -h "$r" | cut -f1)
    printf "  %d) %-38s %6s   %s\n" "$i" "${r#$DIR/}" "$sz" "$(basename "$(dirname "$r")")"
    i=$((i+1))
  done
  echo
  echo "Detail des ascensions enregistrees :"
  xlog_line "${RECS[0]}" | sed 's/^/    /'
  echo
  echo "Usage : $0 <numero> [-s vitesse]     (ex: $0 1 -s 200)"
  echo "Navigation avant/arriere : python3 tools/replay_ascension.py <ttyrec> --fin"
  exit 0
fi

n="$1"; shift
rec="${RECS[$((n-1))]:-}"
[ -z "$rec" ] && { echo "Numero invalide" >&2; exit 1; }
echo "Lecture de $rec"
echo "(espace = pause, f = avance d'une image, q = quitter)"
sleep 1
exec ttyplay "$@" "$rec"
