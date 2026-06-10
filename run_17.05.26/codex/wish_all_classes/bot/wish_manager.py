#!/usr/bin/env python3
"""Maintain wish-ready NetHack games for every role."""

import glob
import json
import logging
import os
import signal
import shutil
import subprocess
import time

DATA_DIR = "/data/sessions"
BOT_SCRIPT = "/opt/nethack/bot/wish_bot.py"
ENABLED_FLAG = "/data/bots_enabled"
ROLES = [
    "Archeologist",
    "Barbarian",
    "Caveman",
    "Healer",
    "Knight",
    "Monk",
    "Priest",
    "Ranger",
    "Rogue",
    "Samurai",
    "Tourist",
    "Valkyrie",
    "Wizard",
]
POOL_TARGET_PER_ROLE = int(os.environ.get("WISH_POOL_TARGET_PER_ROLE", "1"))
MAX_CONCURRENT_BOTS = int(os.environ.get("WISH_MAX_CONCURRENT_BOTS", "13"))
MAX_ACTIVE_NETHACK = int(os.environ.get("WISH_MAX_ACTIVE_NETHACK", "55"))
CHECK_INTERVAL = 5

logging.basicConfig(
    level=logging.INFO,
    format="[WISH_MANAGER] %(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

active_bot_procs = []


def is_enabled():
    return os.path.exists(ENABLED_FLAG)


def load_session(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def get_sessions():
    sessions = []
    for path in glob.glob(os.path.join(DATA_DIR, "*.json")):
        data = load_session(path)
        if data:
            data["_path"] = path
            sessions.append(data)
    return sessions


def tmux_session_exists(name):
    result = subprocess.run(
        ["tmux", "has-session", "-t", name],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def remove_session_hackdir(session):
    hackdir = session.get("hackdir", "")
    if not hackdir.startswith("/data/game_hackdirs/"):
        return
    shutil.rmtree(hackdir, ignore_errors=True)


def count_active_nethack_sessions():
    result = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_name}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return 0
    count = 0
    for line in result.stdout.splitlines():
        name = line.strip()
        if name.startswith("wish-") or name.startswith("play-"):
            count += 1
    return count


def cleanup_dead_sessions(sessions):
    for session in sessions:
        if session.get("status") in ("wish_ready", "bot_playing", "claimed"):
            name = session.get("session_name")
            if name and not tmux_session_exists(name):
                log.info("Cleaning dead session: %s", name)
                if session.get("status") != "claimed":
                    remove_session_hackdir(session)
                try:
                    os.remove(session["_path"])
                except OSError:
                    pass


def sessions_for_role(sessions, role, status):
    matching = []
    for session in sessions:
        if session.get("role") != role or session.get("status") != status:
            continue
        name = session.get("session_name")
        if name and tmux_session_exists(name):
            matching.append(session)
    return matching


def trim_excess_wish_ready(sessions):
    for role in ROLES:
        ready = sessions_for_role(sessions, role, "wish_ready")
        if len(ready) <= POOL_TARGET_PER_ROLE:
            continue

        ready.sort(key=lambda s: s.get("timestamp", 0), reverse=True)
        for session in ready[POOL_TARGET_PER_ROLE:]:
            name = session["session_name"]
            log.info("Pruning excess %s wish-ready session: %s", role, name)
            subprocess.run(["tmux", "kill-session", "-t", name], check=False)
            remove_session_hackdir(session)
            try:
                os.remove(session["_path"])
            except OSError:
                pass


def reap_finished_bots():
    global active_bot_procs
    active_bot_procs = [proc for proc in active_bot_procs if proc.poll() is None]


def kill_all_bots():
    global active_bot_procs
    for proc in active_bot_procs:
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass
    active_bot_procs = []


def running_bot_count_for_role(role):
    count = 0
    for proc in active_bot_procs:
        if proc.poll() is None and getattr(proc, "_wish_role", None) == role:
            count += 1
    return count


def spawn_bot(role):
    log.info("Spawning new %s wish bot...", role)
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["WISH_ROLE"] = role
    proc = subprocess.Popen(
        ["python3", "-u", BOT_SCRIPT],
        stdout=open(os.path.join("/data", "bot_output.log"), "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
    )
    proc._wish_role = role
    active_bot_procs.append(proc)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    log.info("Wish Manager started. Waiting for activation...")
    was_enabled = False

    while True:
        try:
            reap_finished_bots()
            sessions = get_sessions()
            cleanup_dead_sessions(sessions)
            sessions = get_sessions()
            trim_excess_wish_ready(sessions)

            if not is_enabled():
                if was_enabled:
                    log.info("Bots DISABLED. Stopping all bots.")
                    kill_all_bots()
                    was_enabled = False
                time.sleep(CHECK_INTERVAL)
                continue

            if not was_enabled:
                log.info(
                    "Bots ENABLED. Target: %d wish games per role, max bots: %d, active cap: %d",
                    POOL_TARGET_PER_ROLE,
                    MAX_CONCURRENT_BOTS,
                    MAX_ACTIVE_NETHACK,
                )
                was_enabled = True

            sessions = get_sessions()
            running_total = len(active_bot_procs)
            active_nethack = count_active_nethack_sessions()
            slots = min(
                MAX_CONCURRENT_BOTS - running_total,
                MAX_ACTIVE_NETHACK - active_nethack,
            )
            if slots <= 0:
                log.info(
                    "Spawn paused: %d active NetHack sessions, %d bots running.",
                    active_nethack,
                    running_total,
                )
                time.sleep(CHECK_INTERVAL)
                continue

            for role in ROLES:
                if slots <= 0:
                    break
                ready = len(sessions_for_role(sessions, role, "wish_ready"))
                playing = len(sessions_for_role(sessions, role, "bot_playing"))
                running = running_bot_count_for_role(role)
                needed = POOL_TARGET_PER_ROLE - ready - playing
                if needed <= 0:
                    continue

                to_spawn = min(needed, slots)
                log.info(
                    "%s pool: %d/%d ready, %d bot_playing, %d bots running. Spawning %d.",
                    role,
                    ready,
                    POOL_TARGET_PER_ROLE,
                    playing,
                    running,
                    to_spawn,
                )
                for _ in range(to_spawn):
                    spawn_bot(role)
                    slots -= 1
                    time.sleep(0.5)

        except Exception as exc:
            log.error("Error in main loop: %s", exc)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
