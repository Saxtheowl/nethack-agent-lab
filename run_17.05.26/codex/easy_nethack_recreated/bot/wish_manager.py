#!/usr/bin/env python3
"""
Wish Manager - Background daemon that maintains a pool of wish-ready
NetHack games by spawning wish bots.

Only active when /data/bots_enabled flag file exists.
Toggle via the SSH menu [b] option.
"""

import glob
import json
import logging
import os
import signal
import subprocess
import time

DATA_DIR = "/data/sessions"
BOT_SCRIPT = "/opt/nethack/bot/wish_bot.py"
ENABLED_FLAG = "/data/bots_enabled"
POOL_TARGET = 3
MAX_CONCURRENT_BOTS = 3
CHECK_INTERVAL = 5

logging.basicConfig(
    level=logging.INFO,
    format="[WISH_MANAGER] %(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# Track bot processes directly
active_bot_procs = []


def is_enabled():
    """Check if bot generation is enabled."""
    return os.path.exists(ENABLED_FLAG)


def load_session(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
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
        capture_output=True, check=False,
    )
    return result.returncode == 0


def cleanup_dead_sessions(sessions):
    for s in sessions:
        if s["status"] in ("wish_ready", "bot_playing", "claimed"):
            if not tmux_session_exists(s["session_name"]):
                log.info("Cleaning dead session: %s", s["session_name"])
                try:
                    os.remove(s["_path"])
                except OSError:
                    pass


def count_wish_ready(sessions):
    count = 0
    for s in sessions:
        if s["status"] == "wish_ready" and tmux_session_exists(s["session_name"]):
            count += 1
    return count


def count_bot_playing(sessions):
    count = 0
    for s in sessions:
        if s["status"] == "bot_playing" and tmux_session_exists(s["session_name"]):
            count += 1
    return count


def trim_excess_wish_ready(sessions):
    """Keep at most POOL_TARGET active wish-ready sessions."""
    ready_sessions = []
    for s in sessions:
        if s["status"] == "wish_ready" and tmux_session_exists(s["session_name"]):
            ready_sessions.append(s)

    if len(ready_sessions) <= POOL_TARGET:
        return

    # Keep the most recent ready sessions and remove the excess older ones.
    ready_sessions.sort(key=lambda s: s.get("timestamp", 0), reverse=True)
    for s in ready_sessions[POOL_TARGET:]:
        log.info("Pruning excess wish-ready session: %s", s["session_name"])
        subprocess.run(["tmux", "kill-session", "-t", s["session_name"]], check=False)
        try:
            os.remove(s["_path"])
        except OSError:
            pass


def reap_finished_bots():
    global active_bot_procs
    still_running = []
    for proc in active_bot_procs:
        if proc.poll() is None:
            still_running.append(proc)
    active_bot_procs = still_running


def kill_all_bots():
    """Terminate all running bot processes."""
    global active_bot_procs
    for proc in active_bot_procs:
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except (OSError, ProcessLookupError):
                pass
    active_bot_procs = []


def spawn_bot():
    log.info("Spawning new wish bot...")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        ["python3", "-u", BOT_SCRIPT],
        stdout=open(os.path.join("/data", "bot_output.log"), "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
        env=env,
    )
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
                log.info("Bots ENABLED. Target pool: %d, Max bots: %d",
                         POOL_TARGET, MAX_CONCURRENT_BOTS)
                was_enabled = True

            sessions = get_sessions()
            wish_ready = count_wish_ready(sessions)
            bot_playing = count_bot_playing(sessions)
            running_bots = len(active_bot_procs)

            needed = POOL_TARGET - wish_ready - bot_playing
            can_spawn = MAX_CONCURRENT_BOTS - running_bots

            if needed > 0 and can_spawn > 0:
                to_spawn = min(needed, can_spawn)
                log.info("Pool: %d/%d ready, %d bot_playing, %d bots running. Spawning %d more.",
                         wish_ready, POOL_TARGET, bot_playing, running_bots, to_spawn)
                for _ in range(to_spawn):
                    spawn_bot()
                    time.sleep(0.5)
            elif needed > 0:
                log.info("Pool: %d/%d ready, %d bot_playing, %d bots running (at max concurrent).",
                         wish_ready, POOL_TARGET, bot_playing, running_bots)

        except Exception as e:
            log.error("Error in main loop: %s", e)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
