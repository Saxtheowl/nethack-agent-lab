#!/usr/bin/env python3
"""Serveur web du viewer de replays Fable.

Scanne un répertoire ``runs`` (celui du projet gpt_5.6 par défaut), expose
les métadonnées de tous les runs/épisodes et rend les replays ttyrec à la
demande. Aucune dépendance en dehors de la stdlib et de pyte.

Usage :
    python3 server.py [--runs CHEMIN] [--port 8674] [--host 127.0.0.1]
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import threading
import time
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import replay_core

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DEFAULT_RUNS = (BASE_DIR / ".." / "gpt_5.6" / "runs").resolve()

RUN_NAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")
INDEX_TTL = 10.0
REPLAY_CACHE_SIZE = 24

# Runs antérieurs au correctif anti-triche (commit d1392f7) et non « strict » :
# l'agent modifiait la source pour révéler la carte / dépasser l'avantage défini.
CHEAT_CUTOFF = "2026-07-11T16:40:51+00:00"


def is_clean(name: str, started_at: str | None) -> bool:
    if "strict" in name.lower():
        return True
    if started_at:
        return started_at >= CHEAT_CUTOFF
    return False

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _wilson_95(successes: int, total: int):
    if not total:
        return None
    z = 1.959963984540054
    phat = successes / total
    denom = 1 + z * z / total
    center = phat + z * z / (2 * total)
    margin = z * ((phat * (1 - phat) + z * z / (4 * total)) / total) ** 0.5
    return [(center - margin) / denom, (center + margin) / denom]


def _resolve_ttyrec(run_dir: Path, row: dict) -> Path | None:
    stored = row.get("ttyrec")
    if stored:
        path = Path(stored)
        if path.exists():
            return path
    episode_dir = run_dir / "episodes" / f"{int(row['episode']):06d}"
    candidates = sorted(episode_dir.glob("*.ttyrec*"))
    if candidates:
        return candidates[-1]
    # certains runs (smoke tests) déposent le ttyrec à la racine du run
    root_candidates = sorted(run_dir.glob("*.ttyrec*"))
    return root_candidates[-1] if root_candidates else None


def _parse_xlogfile(run_dir: Path) -> dict | None:
    """Lit un unique xlogfile racine et le convertit en résultat d'épisode 0."""
    xlogs = sorted(run_dir.glob("*.xlogfile"))
    if not xlogs:
        return None
    text = xlogs[-1].read_text().strip().splitlines()
    if not text:
        return None
    fields = {}
    for pair in text[-1].split("\t"):
        if "=" in pair:
            key, _, value = pair.partition("=")
            fields[key] = value
    return {
        "episode": 0,
        "success": False,
        "failure_cause": fields.get("death") or "inconnu",
        "steps": None,
        "policy": {
            "turn": int(fields["turns"]) if fields.get("turns", "").isdigit() else None,
            "depth": int(fields["maxlvl"]) if fields.get("maxlvl", "").isdigit() else None,
            "xp_level": None,
            "hp": int(fields["hp"]) if fields.get("hp", "").isdigit() else None,
            "hpmax": int(fields["maxhp"]) if fields.get("maxhp", "").isdigit() else None,
            "last_message": f"death={fields.get('death', '?')} · points={fields.get('points', '?')}",
        },
    }


class Library:
    """Index des runs + cache LRU des replays rendus (déjà gzippés)."""

    def __init__(self, root: Path):
        self.root = root
        self._lock = threading.Lock()
        self._index = None
        self._index_at = 0.0
        self._episode_rows: dict[tuple[str, int], dict] = {}
        self._replays: OrderedDict[tuple[str, int], bytes] = OrderedDict()

    def index(self) -> dict:
        with self._lock:
            if self._index is not None and time.monotonic() - self._index_at < INDEX_TTL:
                return self._index
            self._index = self._scan()
            self._index_at = time.monotonic()
            return self._index

    def _scan(self) -> dict:
        runs = []
        episodes = []
        self._episode_rows = {}
        if self.root.is_dir():
            for run_dir in sorted(self.root.iterdir()):
                if not run_dir.is_dir():
                    continue
                info, rows = self._scan_run(run_dir)
                if info is None:
                    continue
                runs.append(info)
                episodes.extend(rows)
        return {"root": str(self.root), "runs": runs, "episodes": episodes}

    def _scan_run(self, run_dir: Path):
        raw: dict[int, dict] = {}
        results = run_dir / "results.jsonl"
        if results.exists():
            for line in results.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    raw[int(row["episode"])] = row
        episodes_dir = run_dir / "episodes"
        if episodes_dir.is_dir():
            for result_path in episodes_dir.glob("*/result.json"):
                row = _read_json(result_path)
                if row is not None:
                    raw.setdefault(int(row["episode"]), row)
        if not raw and not episodes_dir.is_dir():
            # dernier recours : ttyrec + xlogfile déposés à la racine du run
            synthetic = _parse_xlogfile(run_dir)
            if synthetic is None or not sorted(run_dir.glob("*.ttyrec*")):
                return None, []
            raw[0] = synthetic

        config = _read_json(run_dir / "config.json") or {}
        summary = _read_json(run_dir / "summary.json") or {}

        rows = []
        successes = 0
        causes: dict[str, int] = {}
        success_steps = []
        for number in sorted(raw):
            row = raw[number]
            policy = row.get("policy") or {}
            success = bool(row.get("success"))
            if success:
                successes += 1
                if isinstance(row.get("steps"), int):
                    success_steps.append(row["steps"])
            else:
                cause = row.get("failure_cause") or "inconnu"
                causes[cause] = causes.get(cause, 0) + 1
            ttyrec = _resolve_ttyrec(run_dir, row)
            entry = {
                "run": run_dir.name,
                "episode": number,
                "success": success,
                "failure_cause": row.get("failure_cause"),
                "failure_hint": policy.get("failure_hint"),
                "steps": row.get("steps"),
                "turn": policy.get("turn"),
                "depth": policy.get("depth"),
                "xp": policy.get("xp_level"),
                "hp": policy.get("hp"),
                "hpmax": policy.get("hpmax"),
                "excalibur": bool(policy.get("excalibur")),
                "last_message": policy.get("last_message"),
                "has_replay": ttyrec is not None,
            }
            rows.append(entry)
            self._episode_rows[(run_dir.name, number)] = row

        total = len(rows)
        success_steps.sort()
        median = success_steps[len(success_steps) // 2] if success_steps else None
        info = {
            "name": run_dir.name,
            "family": re.sub(r"-\d+$", "", run_dir.name),
            "clean": is_clean(run_dir.name, config.get("started_at")),
            "episodes": total,
            "successes": successes,
            "win_rate": (successes / total) if total else None,
            "wilson_95": summary.get("wilson_95") or _wilson_95(successes, total),
            "median_success_steps": summary.get("median_success_steps") or median,
            "failure_causes": summary.get("failure_causes") or causes,
            "started_at": config.get("started_at"),
            "nethack": config.get("nethack"),
            "character": config.get("character"),
            "max_steps": config.get("max_steps"),
            "workers": config.get("workers"),
            "wizard": config.get("wizard"),
            "counted": config.get("counted"),
            "replays": sum(1 for entry in rows if entry["has_replay"]),
        }
        return info, rows

    def episode_result(self, run: str, episode: int) -> dict | None:
        self.index()
        with self._lock:
            return self._episode_rows.get((run, episode))

    def ttyrec_path(self, run: str, episode: int) -> Path | None:
        row = self.episode_result(run, episode)
        if row is None:
            return None
        return _resolve_ttyrec(self.root / run, row)

    def replay(self, run: str, episode: int) -> bytes | None:
        """JSON gzippé du replay rendu, avec cache LRU."""
        key = (run, episode)
        with self._lock:
            if key in self._replays:
                self._replays.move_to_end(key)
                return self._replays[key]
        row = self.episode_result(run, episode)
        if row is None:
            return None
        ttyrec = _resolve_ttyrec(self.root / run, row)
        if ttyrec is None:
            return None
        payload = replay_core.render_episode(ttyrec)
        payload["run"] = run
        payload["episode"] = episode
        payload["meta"] = row
        body = gzip.compress(
            json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8"), 6
        )
        with self._lock:
            self._replays[key] = body
            while len(self._replays) > REPLAY_CACHE_SIZE:
                self._replays.popitem(last=False)
        return body


LIBRARY: Library


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _send(self, status: int, body: bytes, content_type: str, gzipped: bool = False):
        accepts_gzip = "gzip" in self.headers.get("Accept-Encoding", "")
        if gzipped and not accepts_gzip:
            body = gzip.decompress(body)
            gzipped = False
        elif not gzipped and accepts_gzip and len(body) > 512:
            body = gzip.compress(body, 6)
            gzipped = True
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        if gzipped:
            self.send_header("Content-Encoding", "gzip")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload, status: int = 200):
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        self._send(status, body, "application/json; charset=utf-8")

    def _send_error_json(self, status: int, message: str):
        self._send_json({"error": message}, status)

    def _parse_episode_query(self, query: dict):
        run = (query.get("run") or [""])[0]
        episode_raw = (query.get("episode") or [""])[0]
        if not RUN_NAME_RE.match(run) or not episode_raw.isdigit():
            return None, None
        return run, int(episode_raw)

    def do_GET(self):
        try:
            self._route()
        except BrokenPipeError:
            pass
        except Exception as exc:  # renvoyer l'erreur au client plutôt que crasher
            try:
                self._send_error_json(500, f"{type(exc).__name__}: {exc}")
            except Exception:
                pass

    def _route(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self._send_static(STATIC_DIR / "index.html")
        elif path.startswith("/static/"):
            target = (STATIC_DIR / path[len("/static/"):]).resolve()
            if STATIC_DIR.resolve() not in target.parents or not target.is_file():
                self._send_error_json(404, "fichier introuvable")
                return
            self._send_static(target)
        elif path == "/api/index":
            self._send_json(LIBRARY.index())
        elif path == "/api/replay":
            run, episode = self._parse_episode_query(query)
            if run is None:
                self._send_error_json(400, "paramètres run/episode invalides")
                return
            body = LIBRARY.replay(run, episode)
            if body is None:
                self._send_error_json(404, "replay introuvable pour cet épisode")
                return
            self._send(200, body, "application/json; charset=utf-8", gzipped=True)
        elif path == "/api/ttyrec":
            run, episode = self._parse_episode_query(query)
            ttyrec = LIBRARY.ttyrec_path(run, episode) if run is not None else None
            if ttyrec is None:
                self._send_error_json(404, "ttyrec introuvable")
                return
            body = ttyrec.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(body)))
            self.send_header(
                "Content-Disposition", f'attachment; filename="{run}-ep{episode:06d}{"".join(ttyrec.suffixes)}"'
            )
            self.end_headers()
            self.wfile.write(body)
        else:
            self._send_error_json(404, "route inconnue")

    def _send_static(self, path: Path):
        if not path.is_file():
            self._send_error_json(404, "fichier introuvable")
            return
        content_type = CONTENT_TYPES.get(path.suffix, "application/octet-stream")
        self._send(200, path.read_bytes(), content_type)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=DEFAULT_RUNS, help="répertoire runs à explorer")
    parser.add_argument("--port", type=int, default=8674)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args(argv)

    global LIBRARY
    LIBRARY = Library(args.runs.resolve())
    if not LIBRARY.root.is_dir():
        parser.error(f"répertoire runs introuvable : {LIBRARY.root}")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Fable Replay Viewer — http://{args.host}:{args.port}/")
    print(f"Runs : {LIBRARY.root}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
