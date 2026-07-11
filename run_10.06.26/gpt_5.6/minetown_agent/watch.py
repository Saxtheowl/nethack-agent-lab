"""Browse episode metadata and replay recorded games in the terminal."""

from __future__ import annotations

import argparse
import bz2
import gzip
import json
import os
import struct
import sys
import time
from pathlib import Path


GREEN = "\033[32m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"


def load_results(root: Path) -> list[dict]:
    rows: list[dict] = []
    paths = []
    if (root / "results.jsonl").exists():
        paths.append(root / "results.jsonl")
    paths.extend(root.glob("*/results.jsonl"))
    for path in paths:
        run_dir = path.parent
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                row["_run"] = run_dir.name
                row["_run_dir"] = str(run_dir)
                ttyrec = Path(row.get("ttyrec") or "")
                if row.get("ttyrec") and not ttyrec.exists():
                    local_ttyrecs = sorted(
                        (run_dir / "episodes" / f"{int(row['episode']):06d}").glob(
                            "*.ttyrec*.bz2"
                        )
                    )
                    if local_ttyrecs:
                        row["ttyrec"] = str(local_ttyrecs[-1])
                rows.append(row)
    return sorted(rows, key=lambda row: (row["_run"], row["episode"]), reverse=True)


def label(row: dict) -> str:
    color = GREEN if row.get("success") else RED
    outcome = "MINETOWN" if row.get("success") else row.get("failure_cause", "?")
    policy = row.get("policy", {})
    return (
        f"{color}{outcome:18s}{RESET} run={row['_run']} ep={row['episode']:04d} "
        f"steps={row.get('steps', 0):5d} turn={str(policy.get('turn')):>5s} "
        f"depth={str(policy.get('depth')):>2s} hp={policy.get('hp')}/{policy.get('hpmax')}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("runs"))
    parser.add_argument("--outcome", choices=("all", "success", "failure"), default="all")
    parser.add_argument("--episode", type=int, help="episode number in the newest matching run")
    parser.add_argument("--list", action="store_true", help="show episodes without replaying")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--speed", type=float, default=8.0)
    parser.add_argument("--max-delay", type=float, default=0.25)
    parser.add_argument("--inputs", action="store_true", help="display agent keystrokes")
    return parser


def _open_ttyrec(path: Path):
    suffixes = path.suffixes
    if suffixes and suffixes[-1] in {".bz2", ".bzip2"}:
        return bz2.BZ2File(path)
    if suffixes and suffixes[-1] in {".gz", ".gzip"}:
        return gzip.GzipFile(path)
    return path.open("rb")


def _ttyrec_frames(path: Path):
    with _open_ttyrec(path) as stream:
        while True:
            header = stream.read(13)
            if not header:
                return
            if len(header) != 13:
                raise OSError(f"entête ttyrec incomplet dans {path}")
            sec, usec, length, channel = struct.unpack("<iiiB", header)
            if sec < 0 or usec < 0 or length < 0 or channel not in (0, 1, 2):
                raise OSError(f"entête ttyrec illégal {(sec, usec, length, channel)}")
            data = stream.read(length)
            if len(data) != length:
                raise OSError(f"frame ttyrec incomplète dans {path}")
            yield sec + usec * 1e-6, channel, data


def replay_ttyrec(path: Path, speed: float, max_delay: float, show_inputs: bool) -> int:
    if speed <= 0:
        raise SystemExit("--speed doit être positif")
    previous_timestamp: float | None = None
    output = sys.stdout.buffer
    for timestamp, channel, data in _ttyrec_frames(path):
        if previous_timestamp is not None and channel == 0:
            delay = min(max_delay, max(0.0, timestamp - previous_timestamp) / speed)
            if delay:
                time.sleep(delay)
        previous_timestamp = timestamp

        if channel == 0:
            output.write(data)
            output.flush()
        elif channel == 1 and show_inputs:
            os.write(2, b"\n[input] " + data[:1].hex().encode("ascii") + b"\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    rows = load_results(args.root)
    if args.outcome == "success":
        rows = [row for row in rows if row.get("success")]
    elif args.outcome == "failure":
        rows = [row for row in rows if not row.get("success")]
    rows = [row for row in rows if row.get("ttyrec") and Path(row["ttyrec"]).exists()]
    if args.episode is not None:
        rows = [row for row in rows if row["episode"] == args.episode]
    if not rows:
        print("Aucun replay correspondant.", file=sys.stderr)
        return 1

    shown = rows[: args.limit]
    print(f"{CYAN}Parties enregistrées{RESET}")
    for index, row in enumerate(shown):
        print(f"{index:2d}  {label(row)}")
    if args.list:
        return 0

    if len(shown) == 1 or args.episode is not None:
        selected = 0
    else:
        try:
            selected = int(input("Numéro à rejouer [0] : ") or "0")
        except (EOFError, ValueError):
            selected = 0
    if not 0 <= selected < len(shown):
        raise SystemExit("sélection hors limites")
    row = shown[selected]
    print(json.dumps(row.get("policy", {}), indent=2, ensure_ascii=False))

    return replay_ttyrec(Path(row["ttyrec"]), args.speed, args.max_delay, args.inputs)


if __name__ == "__main__":
    raise SystemExit(main())
