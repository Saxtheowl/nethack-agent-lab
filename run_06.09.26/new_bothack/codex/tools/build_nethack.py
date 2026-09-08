#!/usr/bin/env python3
"""Build the pinned NAO source in isolation, without root or gameplay changes."""
from pathlib import Path
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REV = "b60bd44c46ed263e89fcebafd5d7271c700446e9"


def main():
    source = ROOT / "upstream/NetHack"
    if not source.exists():
        subprocess.run(["git", "clone", "https://github.com/altorg/NetHack.git", str(source)], check=True)
    build = ROOT / ".build/nethack"
    install = ROOT / ".local/nethack"
    if not (build / ".configured").exists() or (build / ".configured").read_text() != str(ROOT):
        build.mkdir(parents=True, exist_ok=True)
        archive = subprocess.run(["git", "-C", str(source), "archive", REV], check=True, capture_output=True)
        subprocess.run(["tar", "-x", "-C", str(build)], input=archive.stdout, check=True)
        # The NAO tree already contains symlinked Unix Makefiles.
        for name in ["src/Makefile", "util/Makefile"]:
            p = build / name
            p.write_text(p.read_text().replace("-m32", "") + "\nCFLAGS += -fcommon -std=gnu89\n")
        for name in ["include/config.h", "include/unixconf.h"]:
            p = build / name
            s = p.read_text().replace('"/nh343/var"', '"' + str(install / "var") + '"')
            s = s.replace('"/nh343"', '"' + str(install) + '"')
            s = s.replace('"/dgldir/userdata/%N/%n/dumplog/%t.nh343.txt"', '"' + str(install / "var/%N-%t.txt") + '"')
            p.write_text(s)
        (build / ".configured").write_text(str(ROOT))
    env = dict(os.environ)
    # Upstream's 80-byte compression filename buffer overflows with a long
    # workspace path. Expand storage only; retain the game's rules and RNG.
    files_c = build / "src/files.c"
    old = files_c.read_text()
    fixed = old.replace("char cfn[80];", "char cfn[FQN_MAX_FILENAME + 32];")
    if fixed != old:
        files_c.write_text(fixed)
    local = ROOT / ".local/toolchain/usr"
    env["PATH"] = str(local / "bin") + os.pathsep + env["PATH"]
    if (local / "share/bison").exists():
        env["BISON_PKGDATADIR"] = str(local / "share/bison")
    args = ["make", "GAME=nethack", "CFLAGS=-g -O -I../include -fcommon -std=gnu89", f"GAMEDIR={install}", f"VARDIR={install / 'var'}", "CHOWN=true", "CHGRP=true"]
    subprocess.run(args + ["all"], cwd=build, env=env, check=True)
    # The historical install target deletes GAMEDIR recursively. Existing
    # games, score records and save files must survive a rebuild.
    target = "update" if install.exists() else "install"
    subprocess.run(args + [target], cwd=build, env=env, check=True)
    patches = subprocess.run(["diff", "-u", str(source / "include/config.h"), str(build / "include/config.h")], capture_output=True, text=True)
    (ROOT / "artifacts/nethack-config.patch").write_text(patches.stdout)
    patch = subprocess.run(["diff", "-u", str(source / "src/files.c"), str(files_c)], capture_output=True, text=True)
    (ROOT / "artifacts/nethack-filename.patch").write_text(patch.stdout)
    (ROOT / "artifacts/nethack-build.json").write_text(json.dumps({"revision": REV, "executable": str(install / "nethack"), "wizard": False, "changes": ["installation paths", "64-bit compilation", "GCC -fcommon -std=gnu89", "larger compression filename buffer for long workspace paths"]}, indent=2) + "\n")


if __name__ == "__main__":
    main()
