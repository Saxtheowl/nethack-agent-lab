#!/usr/bin/env python3
"""Run ORIGINAL Clojure mainbot for baseline measurements, never the Python bot.

Results are taken from xlogfile, not guessed from terminal victory messages.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bothack.benchmark import parse_xlog, legitimate_ascension


def descendants(pid):
    path = Path(f"/proc/{pid}/task/{pid}/children")
    try:
        children = [int(value) for value in path.read_text().split()]
    except FileNotFoundError:
        return []
    return [desc for child in children for desc in [*descendants(child), child]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=None, help="Wall-clock limit; a timeout is NOT a game loss")
    parser.add_argument("--name", default="Ref" + str(int(time.time()))[-7:])
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{0,19}", args.name):
        parser.error("Use an alphanumeric NetHack name")
    run = ROOT / "artifacts" / ("original-" + args.name)
    run.mkdir(parents=True, exist_ok=False)
    rc = run / "nethackrc"
    rc.write_bytes((ROOT / "upstream/BotHack/bothack.nethackrc").read_bytes())
    # shlex.quote is shell quoting. JSON quoting is only used for EDN strings.
    import shlex
    # JTA's native HandlerPTY calls execve(command), without shell parsing.
    launcher = run / "launch"
    # HandlerPTY also replaces the environment with TERM=xterm only.
    launcher.write_text("#!/bin/sh\nexport NETHACKOPTIONS=" + shlex.quote(str(rc)) + "\nexec " + shlex.join([str(ROOT / ".local/nethack/nethack"), "-u", args.name]) + "\n")
    launcher.chmod(0o755)
    command = str(launcher)
    config = run / "config.edn"
    config.write_text('{:bot "bothack.bots.mainbot" :ttyrec true :interface :shell :no-exit false :quit-resumed true :nh-command ' + json.dumps(command) + '}\n')
    cp = (ROOT / "artifacts/original-classpath.txt").read_text().strip()
    env = dict(os.environ, NETHACKOPTIONS=str(rc), TERM="xterm", LINES="24", COLUMNS="80")
    cmd = [str(ROOT / ".local/jdk8/bin/java"), "-Xmx2g", "-Djava.awt.headless=true", "-Djava.library.path=" + str(ROOT / ".build/jni"),
           "-cp", cp, "clojure.main", "-m", "bothack.main", str(config)]
    started = time.monotonic()
    timeout = False
    with (run / "console.log").open("w") as log:
        process = subprocess.Popen(cmd, cwd=run, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            timeout = True
            # forkpty creates a separate session; kill descendants too, without touching other games.
            children = descendants(process.pid)
            for pid in [*children, process.pid]:
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    xlog = ROOT / ".local/nethack/var/xlogfile"
    records = []
    raw_records = []
    if xlog.exists():
        for line in xlog.read_text().splitlines():
            record = parse_xlog(line)
            if record.get("name") == args.name:
                records.append(record)
                raw_records.append(line)
    (run / "xlogfile").write_text("\n".join(raw_records) + ("\n" if raw_records else ""))
    result = {"implementation": "original-clojure", "name": args.name,
              "timeout": timeout, "seconds": time.monotonic() - started,
              "exit_code": process.returncode, "records": records,
              "ascended": any(legitimate_ascension(record) for record in records),
              "rc_sha256": hashlib.sha256(rc.read_bytes()).hexdigest(),
              "status": "timeout" if timeout else "finished" if records else "no-game-result"}
    (run / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
