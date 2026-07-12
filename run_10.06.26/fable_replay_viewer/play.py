#!/usr/bin/env python3
"""Lecteur CLI de replays NetHack (projet gpt_5.6).

Rejoue un ttyrec directement dans le terminal — les couleurs et le rendu sont
ceux de NetHack, sans réinterprétation. Navigation image par image ou par
sauts de 50 frames.

Usage :
    python3 play.py                       # choisir un run puis un épisode
    python3 play.py --run vast-validation-001 --episode 3
    python3 play.py --outcome success     # ne lister que les succès
    python3 play.py --list                # lister sans jouer
    python3 play.py --runs /autre/chemin  # autre répertoire de runs

Touches pendant la lecture :
    espace        lecture / pause
    → / n         +1 frame          ← / p     -1 frame
    ↑ / f         +50 frames        ↓ / b     -50 frames
    g / G         début / fin
    + / -         plus / moins vite
    q             quitter
"""

from __future__ import annotations

import argparse
import json
import os
import re
import select
import sys
import termios
import tty
from pathlib import Path

import replay_core

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RUNS = (BASE_DIR / ".." / "gpt_5.6" / "runs").resolve()
JUMP = 50

GREEN, RED, CYAN, YELLOW, DIM, RESET = (
    "\033[32m", "\033[31m", "\033[36m", "\033[33m", "\033[2m", "\033[0m",
)
ALT_SCREEN, MAIN_SCREEN = "\033[?1049h", "\033[?1049l"
CLEAR = "\033[0m\033[2J\033[H"
STATUS_ROW = 25


# ----------------------------- scan des runs -----------------------------
def _load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _resolve_ttyrec(run_dir: Path, episode: int, stored: str | None) -> Path | None:
    if stored and Path(stored).exists():
        return Path(stored)
    ep_dir = run_dir / "episodes" / f"{episode:06d}"
    found = sorted(ep_dir.glob("*.ttyrec*"))
    if found:
        return found[-1]
    root = sorted(run_dir.glob("*.ttyrec*"))
    return root[-1] if root else None


def _xlog_episode(run_dir: Path) -> dict | None:
    xlogs = sorted(run_dir.glob("*.xlogfile"))
    if not xlogs:
        return None
    lines = xlogs[-1].read_text().strip().splitlines()
    if not lines:
        return None
    fields = dict(
        pair.split("=", 1) for pair in lines[-1].split("\t") if "=" in pair
    )
    return {
        "episode": 0,
        "success": False,
        "failure_cause": fields.get("death") or "?",
        "steps": None,
        "policy": {
            "turn": int(fields["turns"]) if fields.get("turns", "").isdigit() else None,
            "depth": int(fields["maxlvl"]) if fields.get("maxlvl", "").isdigit() else None,
            "hp": None, "hpmax": None,
            "last_message": f"death={fields.get('death', '?')} points={fields.get('points', '?')}",
        },
    }


def scan_run(run_dir: Path) -> list[dict]:
    """Renvoie la liste des épisodes jouables d'un run."""
    raw: dict[int, dict] = {}
    results = run_dir / "results.jsonl"
    if results.exists():
        for line in results.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                raw[int(row["episode"])] = row
    ep_dir = run_dir / "episodes"
    if ep_dir.is_dir():
        for rp in ep_dir.glob("*/result.json"):
            row = _load_json(rp)
            if row is not None:
                raw.setdefault(int(row["episode"]), row)
    if not raw and not ep_dir.is_dir():
        synth = _xlog_episode(run_dir)
        if synth is not None and sorted(run_dir.glob("*.ttyrec*")):
            raw[0] = synth

    episodes = []
    for number in sorted(raw):
        row = raw[number]
        policy = row.get("policy") or {}
        ttyrec = _resolve_ttyrec(run_dir, number, row.get("ttyrec"))
        if ttyrec is None:
            continue
        episodes.append({
            "run": run_dir.name,
            "episode": number,
            "success": bool(row.get("success")),
            "failure_cause": row.get("failure_cause"),
            "failure_hint": policy.get("failure_hint"),
            "steps": row.get("steps"),
            "turn": policy.get("turn"),
            "depth": policy.get("depth"),
            "hp": policy.get("hp"),
            "hpmax": policy.get("hpmax"),
            "last_message": policy.get("last_message"),
            "ttyrec": ttyrec,
        })
    return episodes


def scan_runs(root: Path) -> list[dict]:
    runs = []
    for run_dir in sorted(root.iterdir()):
        if not run_dir.is_dir():
            continue
        episodes = scan_run(run_dir)
        if not episodes:
            continue
        wins = sum(1 for e in episodes if e["success"])
        runs.append({
            "name": run_dir.name,
            "dir": run_dir,
            "episodes": episodes,
            "count": len(episodes),
            "wins": wins,
            "rate": wins / len(episodes) if episodes else 0.0,
        })
    return runs


# ----------------------------- sélection -----------------------------
def rate_color(rate: float | None) -> str:
    if rate is None:
        return DIM
    if rate >= 0.8:
        return GREEN
    if rate >= 0.4:
        return YELLOW
    return RED


def episode_label(ep: dict) -> str:
    if ep["success"]:
        outcome = f"{GREEN}MINETOWN{RESET}"
    else:
        outcome = f"{RED}{ep.get('failure_cause') or 'échec':<16}{RESET}"
    msg = ep.get("last_message") or ""
    return (
        f"ep {ep['episode']:>4}  {outcome:<16}  "
        f"steps={str(ep.get('steps')):>5}  T={str(ep.get('turn')):>5}  "
        f"Dlvl={str(ep.get('depth')):>2}  hp={ep.get('hp')}/{ep.get('hpmax')}  "
        f"{DIM}{msg[:40]}{RESET}"
    )


def choose_run(runs: list[dict]) -> dict | None:
    print(f"{CYAN}Runs disponibles{RESET}")
    for i, run in enumerate(runs):
        c = rate_color(run["rate"])
        print(
            f"{i:>3}  {run['name']:<32} {c}{run['rate'] * 100:>3.0f}%{RESET}  "
            f"{run['wins']}/{run['count']} succès"
        )
    choice = input(f"\nNuméro du run [{len(runs) - 1}] : ").strip()
    if not choice:
        return runs[-1]
    if choice.isdigit() and 0 <= int(choice) < len(runs):
        return runs[int(choice)]
    print("Sélection invalide.", file=sys.stderr)
    return None


def choose_episode(run: dict, outcome: str) -> dict | None:
    episodes = run["episodes"]
    if outcome == "success":
        episodes = [e for e in episodes if e["success"]]
    elif outcome == "failure":
        episodes = [e for e in episodes if not e["success"]]
    if not episodes:
        print("Aucun épisode correspondant.", file=sys.stderr)
        return None
    print(f"\n{CYAN}{run['name']}{RESET} — {len(episodes)} épisode(s)")
    for i, ep in enumerate(episodes):
        print(f"{i:>3}  {episode_label(ep)}")
    choice = input(f"\nNuméro à rejouer [0] : ").strip() or "0"
    if choice.isdigit() and 0 <= int(choice) < len(episodes):
        return episodes[int(choice)]
    print("Sélection invalide.", file=sys.stderr)
    return None


# ----------------------------- lecteur -----------------------------
def load_frames(path: Path):
    """Sépare les frames de sortie (octets terminal) et les touches agent.

    Renvoie (frames, inputs) où frames[i] = octets de la i-ème sortie et
    inputs[i] = touche agent ayant précédé cette frame (ou None).
    """
    frames: list[bytes] = []
    times: list[float] = []
    inputs: list[str | None] = []
    pending: str | None = None
    for timestamp, channel, data in replay_core.iter_records(path):
        if channel == 1:
            pending = replay_core.describe_key(data)
        elif channel == 0:
            frames.append(data)
            times.append(timestamp)
            inputs.append(pending)
            pending = None
    t0 = times[0] if times else 0.0
    rel = [t - t0 for t in times]
    return frames, rel, inputs


def _read_key(timeout: float) -> str | None:
    ready, _, _ = select.select([sys.stdin], [], [], max(0.0, timeout))
    if not ready:
        return None
    key = os.read(sys.stdin.fileno(), 8)
    mapping = {
        b"\x1b[C": "n", b"\x1b[D": "p",   # → ←
        b"\x1b[A": "F", b"\x1b[B": "B",   # ↑ ↓ (sauts de 50)
    }
    if key in mapping:
        return mapping[key]
    return key.decode("utf-8", "replace")[:1]


def _status(index: int, total: int, rel_t: float, speed: float,
            paused: bool, key: str | None) -> None:
    state = f"{YELLOW}PAUSE{RESET}" if paused else f"{GREEN}LECTURE{RESET}"
    key_txt = f"  {CYAN}⌨ {key}{RESET}" if key else ""
    bar = (
        f"\033[{STATUS_ROW};1H\033[2K{RESET}"
        f"[{state}] frame {index + 1}/{total}  t={rel_t:5.1f}s  "
        f"x{speed:.1f}{key_txt}"
        f"\033[{STATUS_ROW + 1};1H\033[2K{DIM}"
        f"espace play/pause · →/← ±1 · ↑/↓ ±{JUMP} · g/G début/fin · +/- vitesse · q quitter{RESET}"
    )
    sys.stdout.write(bar)
    sys.stdout.flush()


def _render_full(frames, index: int) -> None:
    sys.stdout.buffer.write(CLEAR.encode())
    sys.stdout.buffer.write(b"".join(frames[: index + 1]))
    sys.stdout.buffer.flush()


def _render_delta(frames, start: int, end: int) -> None:
    if end <= start:
        return
    sys.stdout.buffer.write(b"".join(frames[start + 1 : end + 1]))
    sys.stdout.buffer.flush()


def play(ep: dict, speed: float, max_delay: float) -> int:
    frames, times, inputs = load_frames(ep["ttyrec"])
    total = len(frames)
    if not total:
        print("ttyrec vide", file=sys.stderr)
        return 1

    index = 0
    paused = True
    old = termios.tcgetattr(sys.stdin.fileno())
    try:
        tty.setcbreak(sys.stdin.fileno())
        sys.stdout.write(ALT_SCREEN)
        _render_full(frames, index)
        _status(index, total, times[index], speed, paused, inputs[index])

        while True:
            if paused or index + 1 >= total:
                if index + 1 >= total and not paused:
                    paused = True
                    _status(index, total, times[index], speed, paused, inputs[index])
                key = _read_key(3600.0)
            else:
                dt = max(0.0, times[index + 1] - times[index])
                delay = min(max_delay, dt / speed)
                key = _read_key(delay)
                if key is None:
                    index += 1
                    _render_delta(frames, index - 1, index)
                    _status(index, total, times[index], speed, paused, inputs[index])
                    continue

            if key in ("q", "\x03", "\x04"):
                return 0
            if key in (" ", "\r", "\n"):
                paused = not paused
            elif key in ("n", "."):
                paused = True
                if index + 1 < total:
                    index += 1
                    _render_delta(frames, index - 1, index)
            elif key in ("p", ","):
                paused = True
                index = max(0, index - 1)
                _render_full(frames, index)
            elif key == "F":  # ↑ / avance de 50
                paused = True
                new = min(total - 1, index + JUMP)
                _render_delta(frames, index, new)
                index = new
            elif key == "B":  # ↓ / recule de 50
                paused = True
                index = max(0, index - JUMP)
                _render_full(frames, index)
            elif key == "f":
                paused = True
                new = min(total - 1, index + JUMP)
                _render_delta(frames, index, new)
                index = new
            elif key == "b":
                paused = True
                index = max(0, index - JUMP)
                _render_full(frames, index)
            elif key == "g":
                paused = True
                index = 0
                _render_full(frames, index)
            elif key == "G":
                paused = True
                index = total - 1
                _render_full(frames, index)
            elif key in ("+", "="):
                speed = min(200.0, speed * 1.5)
            elif key in ("-", "_"):
                speed = max(0.1, speed / 1.5)
            _status(index, total, times[index], speed, paused, inputs[index])
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old)
        sys.stdout.write(MAIN_SCREEN)
        sys.stdout.flush()


# ----------------------------- main -----------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--run", help="nom du run (sinon menu interactif)")
    parser.add_argument("--episode", type=int, help="numéro d'épisode")
    parser.add_argument("--outcome", choices=("all", "success", "failure"), default="all")
    parser.add_argument("--list", action="store_true", help="lister sans jouer")
    parser.add_argument("--speed", type=float, default=4.0)
    parser.add_argument("--max-delay", type=float, default=0.25)
    args = parser.parse_args(argv)

    root = args.runs.resolve()
    if not root.is_dir():
        parser.error(f"répertoire runs introuvable : {root}")

    runs = scan_runs(root)
    if not runs:
        print(f"Aucun run jouable dans {root}", file=sys.stderr)
        return 1

    if args.list and not args.run:
        for run in runs:
            c = rate_color(run["rate"])
            print(f"{run['name']:<32} {c}{run['rate'] * 100:>3.0f}%{RESET}  "
                  f"{run['wins']}/{run['count']}")
        return 0

    # choix du run
    if args.run:
        run = next((r for r in runs if r["name"] == args.run), None)
        if run is None:
            print(f"Run introuvable : {args.run}", file=sys.stderr)
            return 1
    else:
        run = choose_run(runs)
        if run is None:
            return 1

    if args.list:
        for ep in run["episodes"]:
            print(episode_label(ep))
        return 0

    # choix de l'épisode
    if args.episode is not None:
        ep = next((e for e in run["episodes"] if e["episode"] == args.episode), None)
        if ep is None:
            print(f"Épisode {args.episode} introuvable dans {run['name']}", file=sys.stderr)
            return 1
    else:
        ep = choose_episode(run, args.outcome)
        if ep is None:
            return 1

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        print("Un vrai terminal est requis pour la lecture interactive.", file=sys.stderr)
        return 1
    print(f"\nLecture de {run['name']} ep {ep['episode']}…", file=sys.stderr)
    return play(ep, args.speed, args.max_delay)


if __name__ == "__main__":
    raise SystemExit(main())
