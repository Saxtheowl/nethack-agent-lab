#!/bin/bash
# Build the patched NetHack 3.6.7 ("bot" window port + logged assists).
#   engine/build.sh            incremental build of engine/nethack-3.6.7
#   engine/build.sh --clean    rebuild from scratch
# Output: build/install/{bin/nethack, nhdir/...}; engine/nethack-3.6.7-bot.patch
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(dirname "$here")"
src="$here/nethack-3.6.7"
final="$root/build/install"
# install into a fresh directory and swap it in by rename: games that are
# running keep their (unlinked) binary; nothing is overwritten in place
prefix="$root/build/install.new"
mkdir -p "$root/build"
# HEADLESS=1: only the "bot" window port (no tty, no ncurses needed)
hints="linux-bot"
[[ "${HEADLESS:-0}" == "1" ]] && hints="linux-bot-headless"
rm -rf "$prefix"
cp "$here/hints/$hints" "$src/sys/unix/hints/$hints"
cd "$src"
if [[ "${1:-}" == "--clean" || ! -f Makefile || "$(cat .hints 2>/dev/null)" != "$hints" ]]; then
    echo "$hints" > .hints
    [[ -f Makefile ]] && make spotless >/dev/null 2>&1 || true
    (cd sys/unix && sh setup.sh "hints/$hints" >/dev/null)
fi
# no yacc/lex needed: use the pre-generated parsers shipped in sys/share
for f in dgn_yacc.c lev_yacc.c dgn_lex.c lev_lex.c; do cp -n sys/share/$f util/$f; done
for f in dgn_comp.h lev_comp.h; do cp -n sys/share/$f include/$f; done
make -C src -j"${JOBS:-3}" BOTPREFIX="$final" >"$root/build/make.log" 2>&1 || { tail -40 "$root/build/make.log"; exit 1; }
make BOTPREFIX="$final" all >"$root/build/make.log" 2>&1 || { tail -40 "$root/build/make.log"; exit 1; }
mkdir -p "$prefix"
make BOTPREFIX="$prefix" install >>"$root/build/make.log" 2>&1 || { tail -40 "$root/build/make.log"; exit 1; }
# the "nethack" shell wrapper is not wanted; the harness runs the binary
cp "$prefix/nhdir/nethack" "$prefix/nethack.bin" 2>/dev/null || true
# regenerate the patch against the pristine sources
(cd "$root" && diff -ruN --exclude='*.o' --exclude=Makefile --exclude='*.orig' \
     --exclude=nethack --exclude=makedefs --exclude=lev_comp --exclude=dgn_comp \
     --exclude=dlb --exclude=recover --exclude='*.lev' --exclude=nhdat \
     --exclude='date.h' --exclude='onames.h' --exclude='pm.h' --exclude='vis_tab.*' \
     --exclude='lev_*.c' --exclude='dgn_*.c' --exclude='*_yacc.c' --exclude='*_lex.c' \
     --exclude='*.tab.*' --exclude='Sys*' --exclude='monstr.c' --exclude='tile.c' \
     --exclude='dat' --exclude='util' --exclude='doc' \
     vendor/NetHack-NetHack-3.6.7_Released engine/nethack-3.6.7 > "$here/nethack-3.6.7-bot.patch" || true)
rm -rf "$root/build/install.old"
[[ -d "$final" ]] && mv "$final" "$root/build/install.old"
mv "$prefix" "$final"
sha256sum "$final/nhdir/nethack" | tee "$root/build/nethack.sha256"
