#!/bin/bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
export PATH="$ROOT/.deps/root/usr/bin:$PATH"
export BISON_PKGDATADIR="$ROOT/.deps/root/usr/share/bison"
cd "$ROOT/vendor/NetHack-NetHack-3.6.7_Released"
cat > sys/unix/hints/bothack <<EOF
#-PRE
PREFIX=$ROOT/build
HACKDIR=\$(PREFIX)/game
INSTDIR=\$(HACKDIR)
VARDIR=\$(HACKDIR)
SHELLDIR=\$(PREFIX)/bin
CFLAGS=-O2 -I../include -DNOTPARMDECL -DDLB -DHACKDIR=\\"\$(HACKDIR)\\" -DCONFIG_ERROR_SECURE=FALSE -DSCORE_ON_BOTL
YACC=bison -y
LEX=flex
LINK=\$(CC)
WINSRC=\$(WINTTYSRC)
WINOBJ=\$(WINTTYOBJ)
WINLIB=-lncurses -ltinfo
CHOWN=true
CHGRP=true
GAMEPERM=0755
VARDIRPERM=0755
VARFILEPERM=0600
EOF
sh sys/unix/setup.sh sys/unix/hints/bothack
make -j4 YACC='bison -y' LEX=flex nethack
make YACC='bison -y' LEX=flex all > "$ROOT/build.log" 2>&1
make YACC='bison -y' LEX=flex install >> "$ROOT/build.log" 2>&1

cp sys/unix/sysconf "$ROOT/build/game/sysconf"
