"""Browse episode metadata and replay recorded games in the terminal."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


GREEN = "\033[32m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"


def load_results(root: Path) -> list[dict]:
    rows: list[dict] = []
    for path in root.glob("*/results.jsonl"):
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                row["_run"] = path.parent.name
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
    parser.add_argument("--inputs", action="store_true", help="display agent keystrokes")
    return parser


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

    ttyplay = Path(sys.executable).with_name("nle-ttyplay")
    command = [str(ttyplay), "--speed", str(args.speed)]
    if args.inputs:
        command.append("--print_inputs")
    command.append(row["ttyrec"])
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())

