"""Persistent EDN subprocess bridge used only by validation and data export."""
from pathlib import Path
import json
import subprocess
import sys
from collections.abc import Mapping
import edn_format as edn

ROOT = Path(__file__).resolve().parents[1]


def keywordize(x):
    if isinstance(x, dict):
        return {edn.Keyword(k): keywordize(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [keywordize(v) for v in x]
    return x


def plain(x):
    if isinstance(x, Mapping):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, edn.ImmutableList, set, frozenset)):
        return [plain(v) for v in x]
    return x


class Oracle:
    def __init__(self):
        source = ROOT / "upstream/BotHack"
        revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
        if revision != "70226b3c8ed12d29c64068aec0acc0ca71d57adf":
            raise RuntimeError("Oracle source revision differs from the pinned BotHack")
        subprocess.run(["git", "-C", str(source), "diff", "--exit-code", "HEAD", "--"], check=True, stdout=subprocess.DEVNULL)
        cp = (ROOT / "artifacts/original-classpath.txt").read_text().strip()
        self.log = (ROOT / "artifacts/oracle.log").open("a")
        self.process = subprocess.Popen([str(ROOT / ".local/jdk8/bin/java"), "-Xmx2g", "-cp", cp,
                                         "clojure.main", str(ROOT / "tools/oracle.clj")],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=self.log, text=True, bufsize=1, cwd=ROOT / "upstream/BotHack")

    def call(self, op, *args):
        request = {edn.Keyword("op"): edn.Keyword(op), edn.Keyword("args"): keywordize(list(args))}
        self.process.stdin.write(edn.dumps(request) + "\n")
        self.process.stdin.flush()
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError("Oracle exited; see artifacts/oracle.log")
            if line.startswith("@@BOTHACK@@"):
                break
            self.log.write(line)
            self.log.flush()
        response = plain(edn.loads(line[len("@@BOTHACK@@"):]))
        if "error" in response:
            raise RuntimeError(response["error"])
        return response["ok"]

    def close(self):
        self.process.stdin.close()
        try:
            self.process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.log.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


if __name__ == "__main__":
    with Oracle() as oracle:
        result = oracle.call("data")
        destination = ROOT / "bothack/data/original.json"
        destination.parent.mkdir(exist_ok=True)
        destination.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
        print(f"Exported {len(result['items'])} items, {len(result['monsters'])} monsters, {len(result['sokoban'])} Sokoban layouts")
