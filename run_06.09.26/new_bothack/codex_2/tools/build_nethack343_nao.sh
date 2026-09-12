#!/bin/bash
# Build NetHack 3.4.3 with the nethack.alt.org (NAO) patchset locally.
# This is BotHack's only supported target version (doc/compiling.md).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC_MIRROR="${1:?usage: build_nethack343_nao.sh <path-to-nh343-nao-git-checkout>}"
BUILD="$ROOT/upstream/nh343-nao-build"
PREFIX="$ROOT/upstream/nh343"

rm -rf "$BUILD" "$PREFIX"
mkdir -p "$BUILD" "$PREFIX"
tar -C "$SRC_MIRROR" --exclude=.git -cf - . | tar -C "$BUILD" -xf -

cd "$BUILD"

# --- paths: NAO ships HACKDIR=/nh343, VAR_PLAYGROUND=/nh343/var --------------
sed -i "s|^#  define HACKDIR \"/nh343\"|#  define HACKDIR \"$PREFIX\"|" include/config.h
sed -i "s|^#define VAR_PLAYGROUND \"/nh343/var\"|#define VAR_PLAYGROUND \"$PREFIX/var\"|" include/unixconf.h
# no mail daemon (bothack.nethackrc sets OPTIONS=!mail; simple mail needs a spool)
sed -i 's|^#define MAIL$|/* #define MAIL */|' include/unixconf.h

# --- Makefile.top: install into our prefix, no setgid games -----------------
sed -i "s|^PREFIX\t = .*|PREFIX = $ROOT/upstream|" sys/unix/Makefile.top
sed -i "s|^GAMEDIR  = .*|GAMEDIR  = $PREFIX|" sys/unix/Makefile.top
sed -i "s|^VARDIR  = .*|VARDIR  = $PREFIX/var|" sys/unix/Makefile.top
sed -i "s|^GAMEUID  = .*|GAMEUID  = $(id -un)|" sys/unix/Makefile.top
sed -i "s|^GAMEGRP  = .*|GAMEGRP  = $(id -gn)|" sys/unix/Makefile.top
sed -i "s|^GAMEPERM = .*|GAMEPERM = 0755|" sys/unix/Makefile.top

# --- Makefile.src: modern gcc + link ncurses (CURSES_GRAPHICS is on in NAO) --
sed -i 's|^CFLAGS = .*|CFLAGS = -g -O2 -fcommon -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0 -fno-stack-protector -std=gnu89 -Wno-implicit-function-declaration -Wno-int-conversion -Wno-incompatible-pointer-types -I../include|' sys/unix/Makefile.src
sed -i 's|^WINLIB = \$(WINTTYLIB)|WINLIB = $(WINTTYLIB) -lncurses|' sys/unix/Makefile.src

# --- no bison/flex on this host: use the pre-generated parsers NetHack ships.
# (verified byte-identical to vanilla 3.4.3; NAO does not patch the grammars)
cp sys/share/dgn_yacc.c sys/share/dgn_lex.c sys/share/lev_yacc.c sys/share/lev_lex.c util/
cp sys/share/dgn_comp.h sys/share/lev_comp.h include/
touch util/dgn_yacc.c util/dgn_lex.c util/lev_yacc.c util/lev_lex.c \
      include/dgn_comp.h include/lev_comp.h

sh sys/unix/setup.sh || true
make -j"$(nproc)" all 2>&1 | tail -20
make install 2>&1 | tail -20

echo "--- built: $PREFIX/nethack"
ls -la "$PREFIX"
