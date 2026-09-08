#!/usr/bin/env python3
"""Prepare pinned reference sources, Java oracle and/or local NetHack."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "BotHack": ("https://github.com/krajj7/BotHack.git", "70226b3c8ed12d29c64068aec0acc0ca71d57adf"),
    "NetHack": ("https://github.com/altorg/NetHack.git", "b60bd44c46ed263e89fcebafd5d7271c700446e9"),
}
JDK_URL = "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u504-b01/OpenJDK8U-jdk_x64_linux_hotspot_8u504b01.tar.gz"
JDK_SHA256 = "9c70e102f527ac674ac2fe9c7d47b9a04e2d19842ba5ab8e9b33f368bbadfaea"


def run(args, **kwargs):
    subprocess.run([str(arg) for arg in args], check=True, **kwargs)


def sources():
    for name, (url, rev) in SOURCES.items():
        target = ROOT / "upstream" / name
        if not target.exists():
            run(["git", "clone", url, target])
            run(["git", "-C", target, "checkout", "--detach", rev])
        head = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
        if head != rev:
            raise RuntimeError(f"{target}: expected {rev}, found {head}; preserving the existing checkout")
        changes = subprocess.check_output(["git", "-C", str(target), "diff", "HEAD", "--name-only"], text=True).strip()
        if changes:
            raise RuntimeError(f"Reference source has tracked changes: {changes}")


def oracle():
    jdk = ROOT / ".local/jdk8"
    if not (jdk / "bin/java").exists():
        archive = ROOT / ".local/jdk8.tar.gz"
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            urllib.request.urlretrieve(JDK_URL, archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != JDK_SHA256:
            raise RuntimeError("JDK archive hash does not match the pinned download")
        jdk.mkdir(exist_ok=True)
        # Verified upstream archive; strip its single top-level directory.
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                member.name = member.name.partition("/")[2]
                if member.name:
                    tar.extract(member, jdk, filter="data")
    env = dict(os.environ, JAVA_HOME=str(jdk), JAVA_CMD=str(jdk / "bin/java"),
               LEIN_JAVA_CMD=str(jdk / "bin/java"), PATH=str(jdk / "bin") + os.pathsep + os.environ["PATH"])
    source = ROOT / "upstream/BotHack"
    lein = ROOT / "tools/lein"
    with (ROOT / "artifacts/original-build.log").open("w") as log:
        run([lein, "compile"], cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT)
    with (ROOT / "artifacts/original-classpath.txt").open("w") as output:
        run([lein, "classpath"], cwd=source, env=env, stdout=output)
    jni = ROOT / ".build/jni"
    jni.mkdir(parents=True, exist_ok=True)
    run([jdk / "bin/javah", "-classpath", source / "target/classes", "-o", jni / "HandlerPTY.h", "de.mud.jta.plugin.HandlerPTY"])
    run(["gcc", "-shared", "-fPIC", "-O2", "-I" + str(jni), "-I" + str(jdk / "include"),
         "-I" + str(jdk / "include/linux"), source / "jta26/jni/src/HandlerPTY.c", "-o", jni / "libjtapty.so", "-lutil"])


def local_tools():
    if shutil.which("flex") and shutil.which("bison"):
        return
    if not shutil.which("apt-get"):
        raise RuntimeError("Install flex and bison, or use a Debian/Ubuntu system for --local-build-tools")
    debs = ROOT / ".local/debs"
    debs.mkdir(parents=True, exist_ok=True)
    run(["apt-get", "download", "flex", "bison", "libfl2"], cwd=debs)
    for deb in debs.glob("*.deb"):
        run(["dpkg-deb", "-x", deb, ROOT / ".local/toolchain"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--game", action="store_true")
    parser.add_argument("--local-build-tools", action="store_true")
    args = parser.parse_args()
    (ROOT / "artifacts").mkdir(exist_ok=True)
    sources()
    if args.local_build_tools:
        local_tools()
    if args.oracle:
        oracle()
    if args.game:
        with (ROOT / "artifacts/nethack-build.log").open("w") as log:
            run([sys.executable, ROOT / "tools/build_nethack.py"], stdout=log, stderr=subprocess.STDOUT)
    print("Requested reference components are ready.")


if __name__ == "__main__":
    main()
