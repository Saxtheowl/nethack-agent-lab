#!/usr/bin/env python3
"""Build NetHack 3.4.3 with the nethack.alt.org (NAO) patches, without root.

Source: altorg/NetHack branch 3.4.3-nao (the code that ran on nethack.alt.org,
the historical target of krajj7's BotHack).  Only installation paths and
modern-GCC compatibility flags are changed - no gameplay changes.
"""
from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REV = "b60bd44c46ed263e89fcebafd5d7271c700446e9"  # 3.4.3-nao (latest, fortify-safe)


def main():
    source = ROOT / "upstream/NetHack"
    build = ROOT / ".build/nethack"
    install = ROOT / ".local/nethack"
    if not (build / ".configured").exists() or (build / ".configured").read_text() != str(ROOT):
        if build.exists():
            subprocess.run(["rm", "-rf", str(build)], check=True)
        build.mkdir(parents=True)
        archive = subprocess.run(["git", "-C", str(source), "archive", REV], check=True, capture_output=True)
        subprocess.run(["tar", "-x", "-C", str(build)], input=archive.stdout, check=True)
        # 64-bit + modern GCC compatibility (NAO Makefile compiles with -m32 by default)
        for name in ["src/Makefile", "util/Makefile"]:
            p = build / name
            p.write_text(p.read_text().replace("-m32", "") + "\nCFLAGS += -fcommon -std=gnu89 -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0\n")
        # installation paths only
        for name in ["include/config.h", "include/unixconf.h"]:
            p = build / name
            s = p.read_text()
            s = s.replace('"/nh343/var"', '"' + str(install / "var") + '"')
            s = s.replace('"/nh343"', '"' + str(install) + '"')
            s = s.replace('"/dgldir/userdata/%N/%n/dumplog/%t.nh343.txt"',
                          '"' + str(install / "var/%N-%t.txt") + '"')
            p.write_text(s)
        (build / ".configured").write_text(str(ROOT))
    env = dict(os.environ)
    local = ROOT / ".local/toolchain/usr"
    env["PATH"] = str(local / "bin") + os.pathsep + env["PATH"]
    if (local / "share/bison").exists():
        env["BISON_PKGDATADIR"] = str(local / "share/bison")
    args = ["make", "GAME=nethack",
            "CFLAGS=-g -O -I../include -fcommon -std=gnu89 -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0",
            f"GAMEDIR={install}", f"VARDIR={install / 'var'}",
            "CHOWN=true", "CHGRP=true"]
    subprocess.run(args + ["all"], cwd=build, env=env, check=True)
    subprocess.run(args + ["install"], cwd=build, env=env, check=True)
    info = {"revision": REV,
            "source": "https://github.com/altorg/NetHack branch 3.4.3-nao",
            "executable": str(install / "nethack"),
            "wizard": False,
            "changes": ["installation paths", "64-bit compilation",
                        "GCC -fcommon -std=gnu89 -U_FORTIFY_SOURCE -D_FORTIFY_SOURCE=0"]}
    (ROOT / "artifacts/nethack-build.json").write_text(json.dumps(info, indent=2) + "\n")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
