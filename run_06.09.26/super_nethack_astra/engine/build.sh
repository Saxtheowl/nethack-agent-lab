#!/bin/bash
# Build vanilla NetHack 3.6.7 (tty + curses) into engine/install from the
# official tarball. No patches. Dumplogs go to runs/dumplog/.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(dirname "$here")"
tarball="${TARBALL:-$root/../bothack_3.6/claude/vendor/nethack-3.6.7.tar.gz}"
src="$here/nethack-3.6.7"
if [[ ! -d "$src" ]]; then
    tar xzf "$tarball" -C "$here"
    mv "$here/NetHack-NetHack-3.6.7_Released" "$src"
fi
cd "$src"
sed "s#^PREFIX=\$(wildcard ~)/nh/install#PREFIX=$here/install#" sys/unix/hints/linux > sys/unix/hints/linux-local
(cd sys/unix && sh setup.sh hints/linux-local >/dev/null)
# no yacc/lex needed: use the pre-generated parsers shipped in sys/share
for f in dgn_yacc.c lev_yacc.c dgn_lex.c lev_lex.c; do cp --update=none sys/share/$f util/$f; done
for f in dgn_comp.h lev_comp.h; do cp --update=none sys/share/$f include/$f; done
make all >"$here/make.log" 2>&1        # serial: -j races in dat/
make install >>"$here/make.log" 2>&1
mkdir -p "$root/runs/dumplog"
sed -i "s|^#DUMPLOGFILE=.*|DUMPLOGFILE=$root/runs/dumplog/%n.%t.txt|" "$here/install/games/lib/nethackdir/sysconf"
