"""Replay CLI des parties du bot (inspiré du mt-watch de gpt_5.6).

Usage typique :
    ./venv/bin/python tools/watch.py --fetch m367-11        # rapatrie 3 succès + 3 échecs
    ./venv/bin/python tools/watch.py --list                 # tableau des parties locales
    ./venv/bin/python tools/watch.py --outcome minetown     # rejoue un succès
    ./venv/bin/python tools/watch.py --outcome died --speed 12

Contrôles pendant le replay :
    espace  play/pause      n / →  +1 frame      p / ←  -1 frame
    g début   G fin         + / -  vitesse       q quitter
"""

from __future__ import annotations

import argparse
import json
import os
import select
import struct
import subprocess
import sys
import termios
import time
import tty
from pathlib import Path

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"
ALT_SCREEN = "\033[?1049h"
MAIN_SCREEN = "\033[?1049l"
CLEAR = "\033[0m\033[H\033[2J"

SSH = ["ssh", "-p", "17882", "-o", "StrictHostKeyChecking=no", "root@ssh1.vast.ai"]
SCP_BASE = ["scp", "-P", "17882", "-o", "StrictHostKeyChecking=no"]


def fetch(batch: str, count: int, dest: Path) -> None:
    """Rapatrie `count` succès et `count` échecs du batch depuis l'instance."""
    script = (
        'python3 -c "'
        "import json,glob;"
        f"metas=sorted(glob.glob('/root/runs/{batch}/*/meta.json'));"
        "ok=[];ko=[]\n"
        "for p in metas:\n"
        "    r=json.load(open(p)).get('result','')\n"
        "    (ok if r=='minetown' else ko).append(p.rsplit('/',1)[0])\n"
        f"print('\\n'.join(ok[:{count}]+ko[:{count}]))\n"
        '"'
    )
    out = subprocess.run(SSH + [script], capture_output=True, text=True, timeout=60)
    dirs = [l for l in out.stdout.splitlines() if l.startswith("/root/runs/")]
    if not dirs:
        sys.exit(f"aucune partie trouvée pour {batch} ({out.stderr.strip()[-200:]})")
    dest.mkdir(parents=True, exist_ok=True)
    for d in dirs:
        name = f"{batch}__{Path(d).name}"
        tgt = dest / name
        tgt.mkdir(exist_ok=True)
        subprocess.run(
            SCP_BASE + [f"root@ssh1.vast.ai:{d}/meta.json",
                        f"root@ssh1.vast.ai:{d}/game.ttyrec", str(tgt) + "/"],
            capture_output=True, timeout=120)
        print(f"  récupéré {name}")
    print(f"{len(dirs)} parties dans {dest}/")


def load_games(root: Path) -> list[dict]:
    rows = []
    for meta_path in sorted(root.glob("**/meta.json")):
        d = meta_path.parent
        rec = d / "game.ttyrec"
        if not rec.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text())
        except Exception:
            meta = {}
        meta["_dir"] = d
        meta["_name"] = d.name
        rows.append(meta)
    rows.sort(key=lambda r: r["_name"], reverse=True)
    return rows


def label(row: dict) -> str:
    res = str(row.get("result", "?"))
    color = GREEN if res == "minetown" else (YELLOW if res.startswith("abort") else RED)
    death = row.get("death") or ""
    extra = f" ({death})" if death else ""
    return (f"{color}{res[:34]:34s}{RESET} {row['_name']:24s} "
            f"T={row.get('turns', row.get('turn', '?')):>5} "
            f"wall={int(row.get('wall_seconds', 0)):>4}s{extra}")


def _ttyrec_frames(path: Path):
    with path.open("rb") as stream:
        while True:
            header = stream.read(12)
            if len(header) < 12:
                return
            sec, usec, length = struct.unpack("<iii", header)
            if sec < 0 or usec < 0 or length < 0 or length > 1 << 22:
                return
            data = stream.read(length)
            if len(data) != length:
                return
            yield sec + usec * 1e-6, 0, data


def _write_status(index, frames, speed, paused):
    state = "pause" if paused else "play "
    sys.stdout.write(
        f"{RESET}\033[24;1H\033[2K[{state}] frame {index + 1}/{len(frames)} "
        f"speed={speed:.1f}  espace|n/→|p/←|g|G|+/-|q")
    sys.stdout.flush()


def _render_until(frames, index, speed, paused):
    sys.stdout.buffer.write(CLEAR.encode())
    for _, _, data in frames[: index + 1]:
        sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()
    _write_status(index, frames, speed, paused)


def _read_key(timeout):
    ready, _, _ = select.select([sys.stdin], [], [], max(0.0, timeout))
    if not ready:
        return None
    key = os.read(sys.stdin.fileno(), 8)
    if key == b"\x1b[C":
        return "n"
    if key == b"\x1b[D":
        return "p"
    return key.decode("utf-8", "replace")


def interactive(path: Path, speed: float, max_delay: float) -> int:
    frames = list(_ttyrec_frames(path))
    if not frames:
        print("ttyrec vide", file=sys.stderr)
        return 1
    index, paused = 0, True
    old = termios.tcgetattr(sys.stdin.fileno())
    try:
        tty.setcbreak(sys.stdin.fileno())
        sys.stdout.write(ALT_SCREEN)
        _render_until(frames, index, speed, paused)
        while True:
            if paused:
                key = _read_key(3600.0)
            elif index + 1 >= len(frames):
                paused = True
                _write_status(index, frames, speed, paused)
                key = _read_key(3600.0)
            else:
                prev_ts = frames[index][0]
                index += 1
                ts, _, data = frames[index]
                key = _read_key(min(max_delay, max(0.0, ts - prev_ts) / speed))
                if key is None:
                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
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
                paused, index = True, 0
                _render_until(frames, index, speed, paused)
            elif key == "G":
                paused, index = True, len(frames) - 1
                _render_until(frames, index, speed, paused)
            elif key in {"+", "="}:
                speed = min(200.0, speed * 1.5)
                _write_status(index, frames, speed, paused)
            elif key in {"-", "_"}:
                speed = max(0.1, speed / 1.5)
                _write_status(index, frames, speed, paused)
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)
        sys.stdout.write(MAIN_SCREEN)
        sys.stdout.flush()


def stream(path: Path, speed: float, max_delay: float) -> int:
    prev = None
    for ts, _, data in _ttyrec_frames(path):
        if prev is not None:
            time.sleep(min(max_delay, max(0.0, ts - prev) / speed))
        prev = ts
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path,
                    default=Path(__file__).resolve().parent.parent / "runs" / "replays")
    ap.add_argument("--fetch", metavar="BATCH",
                    help="rapatrie des parties du batch depuis l'instance Vast")
    ap.add_argument("--n", type=int, default=3, help="parties par catégorie à rapatrier")
    ap.add_argument("--outcome", default="all",
                    help="all | minetown | died | abort (préfixe du résultat)")
    ap.add_argument("--game", help="nom exact (ex: m367-11__g0004)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--speed", type=float, default=8.0)
    ap.add_argument("--max-delay", type=float, default=0.25)
    ap.add_argument("--raw", action="store_true", help="stream sans contrôles")
    args = ap.parse_args(argv)

    if args.fetch:
        fetch(args.fetch, args.n, args.root)
        if not args.list:
            return 0

    rows = load_games(args.root)
    if args.outcome != "all":
        rows = [r for r in rows if str(r.get("result", "")).startswith(args.outcome)]
    if args.game:
        rows = [r for r in rows if r["_name"] == args.game]
    if not rows:
        print(f"aucune partie dans {args.root} (utilise --fetch m367-N)", file=sys.stderr)
        return 1
    shown = rows[: args.limit]
    print(f"{CYAN}Parties enregistrées ({args.root}){RESET}")
    for i, row in enumerate(shown):
        print(f"{i:2d}  {label(row)}")
    if args.list:
        return 0
    if len(shown) == 1:
        sel = 0
    else:
        try:
            sel = int(input("Numéro à rejouer [0] : ") or "0")
        except (EOFError, ValueError):
            sel = 0
    if not 0 <= sel < len(shown):
        sys.exit("sélection hors limites")
    rec = shown[sel]["_dir"] / "game.ttyrec"
    print(label(shown[sel]))
    if not args.raw and sys.stdin.isatty() and sys.stdout.isatty():
        return interactive(rec, args.speed, args.max_delay)
    return stream(rec, args.speed, args.max_delay)


if __name__ == "__main__":
    raise SystemExit(main())
