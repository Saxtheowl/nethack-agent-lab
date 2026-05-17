from __future__ import annotations

import argparse
import json
import mimetypes
import os
from functools import lru_cache
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import ttyrec as ttyrec_mod


STATIC_DIR = Path(__file__).parent / "static"


def _json_load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _ttyrec_path(game_dir: Path) -> Path | None:
    for name in ("game.ttyrec", "game.ttyrec.xz"):
        candidate = game_dir / name
        if candidate.exists():
            return candidate
    candidates: list[Path] = []
    for pattern in ("*.ttyrec", "*.ttyrec.xz"):
        candidates.extend(game_dir.glob(pattern))
    return sorted(candidates)[0] if candidates else None


def _last_record_line(game_dir: Path) -> str | None:
    for name in ("record", "logfile"):
        path = game_dir / name
        if not path.exists():
            continue
        lines = [line.strip() for line in path.read_text(errors="ignore").splitlines() if line.strip()]
        if lines:
            return lines[-1]
    return None


def _death_from_record(record: str | None) -> str | None:
    if not record:
        return None
    parts = record.split()
    if not parts:
        return None
    tail = parts[-1]
    if "," in tail:
        return tail.split(",", 1)[1].replace("_", " ")
    return None


def _seed_meta(root: Path, game_id: str) -> dict:
    return _json_load(root / "wins" / game_id / "seed.json") or _json_load(root / "seeds" / f"{game_id}.json")


def _seed_value(meta: dict) -> object | None:
    for key in ("seed", "NETHACK_SEED", "nethack_seed"):
        if key in meta and meta[key] not in ("", None):
            return meta[key]
    return None


def _game_entry(root: Path, game_dir: Path, category: str) -> dict:
    game_id = game_dir.name
    seed_meta = _seed_meta(root, game_id)
    ttyrec = _ttyrec_path(game_dir)
    record = _last_record_line(game_dir)
    ascended = category == "winning" or bool(record and "ascended" in record.lower())
    seed = _seed_value(seed_meta)
    seed_source = None
    seed_note = seed_meta.get("seed_note")
    if seed is None:
        seed_source = "historical/unknown" if category == "winning" and not seed_meta else "not recorded"
        seed_note = seed_note or "No deterministic seed is recorded for this ttyrec."

    return {
        "id": game_id,
        "category": category,
        "seed": seed,
        "seed_source": seed_source,
        "seed_note": seed_note,
        "seed_meta": seed_meta,
        "recording_id": str(ttyrec.relative_to(root)) if ttyrec else None,
        "ascended": ascended,
        "in_progress": False,
        "final_turn": None,
        "death": None if ascended else _death_from_record(record),
        "record": record,
        "started_at": seed_meta.get("started_utc"),
        "finished_at": None,
        "ttyrec_size": ttyrec.stat().st_size if ttyrec else 0,
    }


def _game_dirs(root: Path) -> list[tuple[Path, str]]:
    out: list[tuple[Path, str]] = []
    wins = root / "wins"
    if wins.exists():
        out.extend((p, "winning") for p in sorted(wins.iterdir()) if p.is_dir())
    return out


def _find_game(root: Path, game_id: str) -> Path:
    candidate = root / "wins" / game_id
    if candidate.is_dir():
        return candidate
    raise FileNotFoundError(game_id)


@lru_cache(maxsize=32)
def _load_parsed_cached(path: str, mtime: float, size: int):
    frames = ttyrec_mod.parse(path)
    return frames, ttyrec_mod.build_turn_index(frames)


def _load_parsed(path: Path):
    stat = path.stat()
    return _load_parsed_cached(str(path), stat.st_mtime, stat.st_size)


class ReplayHandler(BaseHTTPRequestHandler):
    root = Path("/lab")

    def log_message(self, format: str, *args) -> None:
        return

    def send_json(self, payload: object) -> None:
        body = json.dumps(payload).encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, status: HTTPStatus, text: str) -> None:
        body = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str | None = None) -> None:
        if not path.exists() or not path.is_file():
            self.send_text(HTTPStatus.NOT_FOUND, "not found")
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def safe_static(self, requested: str) -> Path | None:
        rel = requested.removeprefix("/static/") or "index.html"
        path = (STATIC_DIR / rel).resolve()
        try:
            path.relative_to(STATIC_DIR.resolve())
        except ValueError:
            return None
        return path

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self.send_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
                return
            if parsed.path == "/replay":
                self.send_file(STATIC_DIR / "replay.html", "text/html; charset=utf-8")
                return
            if parsed.path.startswith("/static/"):
                path = self.safe_static(parsed.path)
                if path is None:
                    self.send_text(HTTPStatus.BAD_REQUEST, "invalid static path")
                else:
                    self.send_file(path)
                return
            if parsed.path == "/api/games":
                games = [_game_entry(self.root, d, category) for d, category in _game_dirs(self.root)]
                games.sort(key=lambda g: (g["category"] != "winning", g["id"]))
                self.send_json({"games": games, "total_winning": sum(1 for g in games if g["ascended"])})
                return
            if parsed.path == "/api/winning":
                wins = [_game_entry(self.root, d, "winning") for d in sorted((self.root / "wins").iterdir()) if d.is_dir()]
                self.send_json({"wins": wins, "total": len(wins)})
                return
            if parsed.path == "/health":
                self.send_json({"ok": True, "root": str(self.root), "games": len(_game_dirs(self.root))})
                return

            parts = parsed.path.strip("/").split("/")
            if len(parts) >= 3 and parts[0] == "api" and parts[1] == "games":
                game_id = unquote(parts[2])
                game_dir = _find_game(self.root, game_id)
                ttyrec = _ttyrec_path(game_dir)
                if ttyrec is None:
                    self.send_text(HTTPStatus.NOT_FOUND, "no ttyrec for this game")
                    return
                frames, idx = _load_parsed(ttyrec)

                if len(parts) == 3:
                    category = "winning" if game_dir.parent.name == "wins" else "attempts"
                    meta = _game_entry(self.root, game_dir, category)
                    self.send_json(
                        {
                            "id": game_id,
                            "meta": meta,
                            "frame_count": idx["frame_count"],
                            "duration_sec": idx["duration_sec"],
                            "turn_first_frame": idx["turn_first_frame"],
                            "ttyrec_bytes": sum(len(f.payload) for f in frames),
                        }
                    )
                    return
                if len(parts) == 4 and parts[3] == "frames":
                    base_t = frames[0].t if frames else 0.0
                    self.send_json(
                        {
                            "frame_count": len(frames),
                            "first_ts": base_t,
                            "rel_ts": [round(f.t - base_t, 4) for f in frames],
                            "lengths": [len(f.payload) for f in frames],
                            "turn_at_frame": idx["turn_at_frame"],
                            "turn_first_frame": idx["turn_first_frame"],
                        }
                    )
                    return
                if len(parts) == 4 and parts[3] == "bytes":
                    query = parse_qs(parsed.query)
                    start = max(0, int(query.get("start", ["0"])[0]))
                    end = int(query.get("end", [str(len(frames))])[0])
                    end = max(start, min(end, len(frames)))
                    body = ttyrec_mod.frame_bytes_concat(frames, start, end)
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "application/octet-stream")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                if len(parts) == 4 and parts[3] == "raw.ttyrec":
                    self.send_file(ttyrec, "application/octet-stream")
                    return
            self.send_text(HTTPStatus.NOT_FOUND, "not found")
        except FileNotFoundError:
            self.send_text(HTTPStatus.NOT_FOUND, "game not found")
        except Exception as exc:
            self.send_text(HTTPStatus.INTERNAL_SERVER_ERROR, f"{type(exc).__name__}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8080, type=int)
    parser.add_argument("--root", default=os.environ.get("BOTLAB_ROOT", "/lab"))
    args = parser.parse_args()
    ReplayHandler.root = Path(args.root)
    ThreadingHTTPServer((args.host, args.port), ReplayHandler).serve_forever()


if __name__ == "__main__":
    main()
