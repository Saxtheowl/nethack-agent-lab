"""FastAPI replay server for BotHack/NetHack ttyrecs.

Endpoints:
  GET  /                       → static index.html (game list + replay UI)
  GET  /api/games              → list every game folder under /data/games
  GET  /api/games/{gid}        → metadata + turn index for one game
  GET  /api/games/{gid}/bytes  → raw byte slice (?start=&end= frame indices)
                                  Used by the front-end to fast-forward to a
                                  particular frame by replaying all preceding
                                  bytes into xterm.js.
  GET  /api/games/{gid}/frames → list of frames as JSON (offsets+timestamps).
                                  Front-end uses this to drive playback.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

import ttyrec as ttyrec_mod  # local module


DATA_DIR = Path(os.environ.get("NH_RUNS", str(Path(__file__).parent.parent / "runs")))
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="BotHack Replay", docs_url=None, redoc_url=None)


# ---------- helpers ---------------------------------------------------------

def _game_dirs() -> list[Path]:
    """Every game directory: runs/<batch>/<gNNNN> containing a ttyrec."""
    out: list[Path] = []
    if DATA_DIR.exists():
        for batch in sorted(DATA_DIR.iterdir()):
            if not batch.is_dir():
                continue
            for g in sorted(batch.iterdir()):
                if g.is_dir() and (g / "game.ttyrec").exists():
                    out.append(g)
    return out


def _find_game(gid: str) -> Path:
    """gid = '<batch>__<game>'."""
    if "__" in gid:
        batch, game = gid.split("__", 1)
        p = DATA_DIR / batch / game
        if p.is_dir():
            return p
    raise HTTPException(404, f"game {gid!r} not found")


def _ttyrec_path(game_dir: Path) -> Path | None:
    """Find the ttyrec file in a game dir. Prefer the canonical name set by
    run_one.sh on completion; otherwise return any in-progress recording
    (BotHack names them `<unix_millis>.ttyrec` while the game is live)."""
    canon = game_dir / "game.ttyrec"
    if canon.exists():
        return canon
    candidates = sorted(game_dir.glob("*.ttyrec"))
    if candidates:
        return candidates[0]
    return None


@lru_cache(maxsize=32)
def _load_parsed_cached(ttyrec_path: str, mtime: float, size: int) -> tuple[list, dict]:
    """Parse a ttyrec and build its turn index. Cache key includes mtime+size
    so a growing in-progress ttyrec gets re-parsed when it changes."""
    frames = ttyrec_mod.parse(ttyrec_path)
    idx = ttyrec_mod.build_turn_index(frames)
    return frames, idx


def _load_parsed(ttyrec_path: str) -> tuple[list, dict]:
    st = os.stat(ttyrec_path)
    return _load_parsed_cached(ttyrec_path, st.st_mtime, st.st_size)


# ---------- routes ----------------------------------------------------------

@app.get("/api/games")
def list_games():
    games = []
    for d in _game_dirs():
        meta: dict = {}
        mp = d / "meta.json"
        if mp.exists():
            try:
                meta = json.loads(mp.read_text())
            except Exception:
                pass
        ttyrec = _ttyrec_path(d)
        if not meta:
            continue  # unfinished/killed game: don't list ghosts
        won = meta.get("result") == "minetown"
        games.append({
            "id": f"{d.parent.name}__{d.name}",
            "category": "winning" if won else "attempts",
            "seed": None,
            "in_progress": not mp.exists(),
            "ascended": won,
            "final_turn": meta.get("turn"),
            "exit_code": f"{meta.get('result')} {meta.get('branch')}:{meta.get('dlvl')} {meta.get('death') or ''}",
            "started_at": None,
            "finished_at": None,
            "ttyrec_size": ttyrec.stat().st_size if ttyrec else 0,
        })
    games.sort(key=lambda g: (not g["ascended"], g["id"]))
    return {"games": games, "total_winning": sum(1 for g in games if g["ascended"])}


@app.get("/api/games/{gid}")
def get_game(gid: str):
    d = _find_game(gid)
    meta_path = d / "meta.json"
    ttyrec = _ttyrec_path(d)
    if ttyrec is None:
        raise HTTPException(404, "no ttyrec for this game")

    frames, idx = _load_parsed(str(ttyrec))

    meta: dict = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())

    return JSONResponse({
        "id": gid,
        "meta": meta,
        "frame_count": idx["frame_count"],
        "duration_sec": idx["duration_sec"],
        "turn_first_frame": idx["turn_first_frame"],
        "ttyrec_bytes": sum(len(f.payload) for f in frames),
    })


@app.get("/api/games/{gid}/frames")
def get_frames(gid: str):
    """Return per-frame metadata: relative timestamp, payload length, turn.

    The actual bytes are served by /bytes — we don't ship them here to keep
    the JSON small. The front-end uses this to schedule playback.
    """
    d = _find_game(gid)
    ttyrec = _ttyrec_path(d)
    if ttyrec is None:
        raise HTTPException(404, "no ttyrec for this game")

    frames, idx = _load_parsed(str(ttyrec))
    base_t = frames[0].t if frames else 0.0
    body = {
        "frame_count": len(frames),
        "first_ts": base_t,
        "rel_ts": [round(f.t - base_t, 4) for f in frames],
        "lengths": [len(f.payload) for f in frames],
        "turn_at_frame": idx["turn_at_frame"],
        "turn_first_frame": idx["turn_first_frame"],
    }
    return JSONResponse(body)


@app.get("/api/games/{gid}/bytes")
def get_bytes(
    gid: str,
    start: int = Query(0, ge=0),
    end: Optional[int] = Query(None, ge=0),
):
    """Return concatenated raw payloads for frames[start:end] (exclusive end).

    Front-end calls this to:
      • on initial load: fetch all bytes up to the current cursor and feed them
        to xterm.js to materialize the screen state at any frame index;
      • on big jumps (≥10 turns away): refetch a contiguous slice and reseed
        xterm.js with an init sequence first.
    """
    d = _find_game(gid)
    ttyrec = _ttyrec_path(d)
    if ttyrec is None:
        raise HTTPException(404, "no ttyrec for this game")
    frames, _ = _load_parsed(str(ttyrec))
    if end is None:
        end = len(frames)
    end = min(end, len(frames))
    blob = ttyrec_mod.frame_bytes_concat(frames, start, end)
    return Response(content=blob, media_type="application/octet-stream")


@app.get("/api/games/{gid}/raw.ttyrec")
def get_raw(gid: str):
    """Serve the original ttyrec file for `ttyplay`/`ipbt`-style external use."""
    d = _find_game(gid)
    ttyrec = _ttyrec_path(d)
    if ttyrec is None:
        raise HTTPException(404, "no ttyrec for this game")
    return FileResponse(str(ttyrec), media_type="application/octet-stream",
                        filename=f"{gid}.ttyrec")


# ---------- static front-end -----------------------------------------------

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def root():
    idx = STATIC_DIR / "index.html"
    if idx.exists():
        return FileResponse(str(idx))
    return JSONResponse({"hint": "POST a game first; static/index.html missing"})


@app.get("/replay")
def replay():
    page = STATIC_DIR / "replay.html"
    if page.exists():
        return FileResponse(str(page))
    return JSONResponse({"error": "replay.html missing"})


@app.get("/health")
def health():
    return {"ok": True, "data_dir": str(DATA_DIR), "games": len(_game_dirs())}
