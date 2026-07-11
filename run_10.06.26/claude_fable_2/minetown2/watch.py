"""Browse episode metadata and replay recorded games in the terminal."""

from __future__ import annotations

import argparse
import bz2
import gzip
import json
import os
import select
import struct
import sys
import termios
import time
import tty
from pathlib import Path


GREEN = "\033[32m"
RED = "\033[31m"
CYAN = "\033[36m"
RESET = "\033[0m"
ALT_SCREEN = "\033[?1049h"
MAIN_SCREEN = "\033[?1049l"
CLEAR = "\033[0m\033[H\033[2J"


def load_results(root: Path) -> list[dict]:
    rows: list[dict] = []
    seen: set[tuple[str, int]] = set()

    def add_row(row: dict, run_dir: Path) -> None:
        key = (str(run_dir.resolve()), int(row["episode"]))
        if key in seen:
            return
        seen.add(key)
        row["_run"] = run_dir.name
        row["_run_dir"] = str(run_dir)
        ttyrec = Path(row.get("ttyrec") or "")
        if not row.get("ttyrec") or not ttyrec.exists():
            local_ttyrecs = sorted(
                (run_dir / "episodes" / f"{int(row['episode']):06d}").glob(
                    "*.ttyrec*.bz2"
                )
            )
            if local_ttyrecs:
                row["ttyrec"] = str(local_ttyrecs[-1])
        rows.append(row)

    paths = []
    if (root / "results.jsonl").exists():
        paths.append(root / "results.jsonl")
    paths.extend(root.glob("*/results.jsonl"))
    for path in paths:
        run_dir = path.parent
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                add_row(row, run_dir)
    run_dirs = [root] if (root / "episodes").is_dir() else list(root.iterdir()) if root.is_dir() else []
    for run_dir in run_dirs:
        for path in (run_dir / "episodes").glob("*/result.json"):
            add_row(json.loads(path.read_text()), run_dir)
    return sorted(rows, key=lambda row: (row["_run"], row["episode"]), reverse=True)


def available_runs(root: Path) -> list[str]:
    base = root if root.exists() and root.name == "runs" else Path("runs")
    if not base.exists():
        return []
    return sorted(
        path.name
        for path in base.iterdir()
        if (path / "results.jsonl").exists() or (path / "episodes").is_dir()
    )


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
    parser.add_argument("--json", action="store_true", help="print stored policy metadata before replay")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="stream ttyrec bytes without interactive controls",
    )
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


def load_ttyrec(path: Path) -> list[tuple[float, int, bytes]]:
    return list(_ttyrec_frames(path))


def _write_status(index: int, frames: list[tuple[float, int, bytes]], speed: float, paused: bool) -> None:
    if not frames:
        return
    state = "pause" if paused else "play "
    status = (
        f"{RESET}\033[24;1H\033[2K"
        f"[{state}] frame {index + 1}/{len(frames)}  speed={speed:.1f}  "
        "espace play/pause | n/→ +1 | p/← -1 | g début | G fin | +/- vitesse | q quitter"
    )
    sys.stdout.write(status)
    sys.stdout.flush()


def _render_until(frames: list[tuple[float, int, bytes]], index: int, speed: float, paused: bool) -> None:
    sys.stdout.buffer.write(CLEAR.encode("ascii"))
    for _, channel, data in frames[: index + 1]:
        if channel == 0:
            sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()
    _write_status(index, frames, speed, paused)


def _read_key(timeout: float) -> str | None:
    ready, _, _ = select.select([sys.stdin], [], [], max(0.0, timeout))
    if not ready:
        return None
    key = os.read(sys.stdin.fileno(), 8)
    if key == b"\x1b[C":
        return "n"
    if key == b"\x1b[D":
        return "p"
    return key.decode("utf-8", "replace")


def interactive_ttyrec(
    path: Path,
    speed: float,
    max_delay: float,
    show_inputs: bool,
) -> int:
    if speed <= 0:
        raise SystemExit("--speed doit être positif")
    frames = load_ttyrec(path)
    if not frames:
        print("ttyrec vide", file=sys.stderr)
        return 1

    index = 0
    paused = True
    old_termios = termios.tcgetattr(sys.stdin.fileno())
    try:
        tty.setcbreak(sys.stdin.fileno())
        sys.stdout.write(ALT_SCREEN)
        _render_until(frames, index, speed, paused)
        while True:
            if paused:
                key = _read_key(3600.0)
            else:
                if index + 1 >= len(frames):
                    paused = True
                    _write_status(index, frames, speed, paused)
                    key = _read_key(3600.0)
                else:
                    previous_timestamp = frames[index][0]
                    index += 1
                    timestamp, channel, data = frames[index]
                    delay = min(max_delay, max(0.0, timestamp - previous_timestamp) / speed)
                    key = _read_key(delay)
                    if key is None:
                        if channel == 0:
                            sys.stdout.buffer.write(data)
                            sys.stdout.buffer.flush()
                        elif channel == 1 and show_inputs:
                            os.write(2, b"\n[input] " + data[:1].hex().encode("ascii") + b"\n")
                        _write_status(index, frames, speed, paused)
                        continue

            if key in {"q", "\x03", "\x04"}:
                return 0
            if key in {" ", "\r", "\n"}:
                paused = not paused
                _write_status(index, frames, speed, paused)
            elif key in {"n", "."}:
                paused = True
                index = min(len(frames) - 1, index + 1)
                _render_until(frames, index, speed, paused)
            elif key in {"p", ","}:
                paused = True
                index = max(0, index - 1)
                _render_until(frames, index, speed, paused)
            elif key == "g":
                paused = True
                index = 0
                _render_until(frames, index, speed, paused)
            elif key == "G":
                paused = True
                index = len(frames) - 1
                _render_until(frames, index, speed, paused)
            elif key in {"+", "="}:
                speed = min(200.0, speed * 1.5)
                _write_status(index, frames, speed, paused)
            elif key in {"-", "_"}:
                speed = max(0.1, speed / 1.5)
                _write_status(index, frames, speed, paused)
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_termios)
        sys.stdout.write(MAIN_SCREEN)
        sys.stdout.flush()


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
        if not args.root.exists():
            runs = ", ".join(available_runs(args.root)[-8:])
            suffix = f" Runs disponibles récents: {runs}" if runs else ""
            print(f"Run introuvable: {args.root}.{suffix}", file=sys.stderr)
        else:
            print("Aucun replay correspondant dans ce run.", file=sys.stderr)
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
    print(label(row))
    if args.json:
        print(json.dumps(row.get("policy", {}), indent=2, ensure_ascii=False))

    if not args.raw and sys.stdin.isatty() and sys.stdout.isatty():
        return interactive_ttyrec(Path(row["ttyrec"]), args.speed, args.max_delay, args.inputs)
    return replay_ttyrec(Path(row["ttyrec"]), args.speed, args.max_delay, args.inputs)


if __name__ == "__main__":
    raise SystemExit(main())
