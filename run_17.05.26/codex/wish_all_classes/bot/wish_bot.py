#!/usr/bin/env python3
"""
Wish Bot - Plays NetHack until it reaches the "For what do you wish?"
prompt, then leaves the tmux session alive for a player.
"""

import json
import os
import random
import shutil
import string
import subprocess
import sys
import tempfile
import time

from wish_utils import make_unique_char_name

NETHACK = "/usr/local/bin/nethack"
DATA_DIR = "/data/sessions"
SAVE_DIR = "/data/saves"
HACKDIR_ROOT = "/data/hackdirs"
SESSION_HACKDIR_ROOT = "/data/game_hackdirs"
GAME_TIMEOUT = 120

ROLE_SPECS = {
    "Archeologist": "role:Archeologist,race:dwarf,align:lawful,gender:female",
    "Barbarian": "role:Barbarian,race:orc,align:chaotic,gender:female",
    "Caveman": "role:Caveman,race:dwarf,align:lawful,gender:female",
    "Healer": "role:Healer,race:gnome,align:neutral,gender:female",
    "Knight": "role:Knight,race:human,align:lawful,gender:female",
    "Monk": "role:Monk,race:human,align:neutral,gender:female",
    "Priest": "role:Priest,race:human,align:lawful,gender:female",
    "Ranger": "role:Ranger,race:elf,align:chaotic,gender:female",
    "Rogue": "role:Rogue,race:orc,align:chaotic,gender:female",
    "Samurai": "role:Samurai,race:human,align:lawful,gender:female",
    "Tourist": "role:Tourist,race:human,align:neutral,gender:female",
    "Valkyrie": "role:Valkyrie,race:dwarf,align:lawful,gender:female",
    "Wizard": "role:Wizard,race:elf,align:chaotic,gender:female",
}

BASE_OPTIONS = [
    "OPTIONS=!news,!legacy,!splash_screen",
    "OPTIONS=!autopickup",
    "OPTIONS=color",
    "OPTIONS=hilite_pet",
    "OPTIONS=!tombstone",
    "OPTIONS=!mail",
    "OPTIONS=!sparkle",
    "OPTIONS=suppress_alert:3.6.7",
]

STATIC_HACKDIR_FILES = {
    "license",
    "logfile",
    "nethack",
    "nethack.maxplayers25.bak",
    "nhdat",
    "perm",
    "record",
    "recover",
    "symbols",
    "sysconf",
    "xlogfile",
}


def selected_role():
    role = os.environ.get("WISH_ROLE", "Valkyrie")
    if role not in ROLE_SPECS:
        raise SystemExit(f"unknown WISH_ROLE: {role}")
    return role


def make_bot_nethackrc(role):
    fd, path = tempfile.mkstemp(prefix=f"nethackrc-{role.lower()}-", text=True)
    with os.fdopen(fd, "w") as fh:
        fh.write(f"OPTIONS={ROLE_SPECS[role]}\n")
        for line in BASE_OPTIONS:
            fh.write(line + "\n")
    return path


def hackdir_for_role(role):
    return os.path.join(HACKDIR_ROOT, role)


def prepare_session_hackdir(session_name, role):
    path = os.path.join(SESSION_HACKDIR_ROOT, session_name)
    role_dir = hackdir_for_role(role)
    shutil.rmtree(path, ignore_errors=True)
    shutil.copytree(role_dir, path, symlinks=True)

    for name in os.listdir(path):
        if name in STATIC_HACKDIR_FILES or name == "save":
            continue
        runtime_path = os.path.join(path, name)
        if os.path.isdir(runtime_path) and not os.path.islink(runtime_path):
            shutil.rmtree(runtime_path, ignore_errors=True)
        else:
            try:
                os.remove(runtime_path)
            except OSError:
                pass

    save_path = os.path.join(path, "save")
    if os.path.lexists(save_path):
        if os.path.isdir(save_path) and not os.path.islink(save_path):
            shutil.rmtree(save_path)
        else:
            os.remove(save_path)
    os.symlink(SAVE_DIR, save_path)

    sysconf = os.path.join(path, "sysconf")
    try:
        with open(sysconf) as fh:
            lines = fh.readlines()
    except OSError:
        lines = []
    replaced = False
    with open(sysconf, "w") as fh:
        for line in lines:
            if line.startswith("MAXPLAYERS="):
                fh.write("MAXPLAYERS=60\n")
                replaced = True
            else:
                fh.write(line)
        if not replaced:
            fh.write("MAXPLAYERS=60\n")
    return path


def random_id():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


def tmux_send(session, keys):
    subprocess.run(["tmux", "send-keys", "-t", session, keys], check=False)


def tmux_send_literal(session, text):
    subprocess.run(["tmux", "send-keys", "-t", session, "-l", text], check=False)


def tmux_capture(session):
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", session, "-p"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def tmux_session_exists(session):
    result = subprocess.run(
        ["tmux", "has-session", "-t", session],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def write_status(session_name, status, extra=None):
    data = {
        "session_name": session_name,
        "status": status,
        "timestamp": time.time(),
    }
    if extra:
        data.update(extra)
    path = os.path.join(DATA_DIR, f"{session_name}.json")
    with open(path, "w") as f:
        json.dump(data, f)
    return path


def cleanup_session(session_name):
    subprocess.run(["tmux", "kill-session", "-t", session_name], check=False)
    status_file = os.path.join(DATA_DIR, f"{session_name}.json")
    if os.path.exists(status_file):
        os.remove(status_file)
    shutil.rmtree(os.path.join(SESSION_HACKDIR_ROOT, session_name), ignore_errors=True)


def skip_initial_prompts(session):
    time.sleep(1)
    deadline = time.time() + 10
    while time.time() < deadline:
        screen = tmux_capture(session)
        if "Do you want your possessions identified?" in screen:
            return False
        if "Really quit?" in screen:
            tmux_send(session, "y")
            time.sleep(0.5)
            return False

        lines = screen.strip().split("\n")
        map_lines = lines[1:22] if len(lines) > 22 else lines[1:]
        if any("@" in line for line in map_lines):
            return True

        tmux_send(session, " ")
        time.sleep(0.5)

    return False


def find_player_pos(screen):
    lines = screen.strip().split("\n")
    map_lines = lines[1:22] if len(lines) > 22 else lines[1:]
    for row_idx, line in enumerate(map_lines):
        col = line.find("@")
        if col != -1:
            return row_idx, col
    return None


def find_fountain_pos(screen):
    lines = screen.strip().split("\n")
    map_lines = lines[1:22] if len(lines) > 22 else lines[1:]
    for row_idx, line in enumerate(map_lines):
        col = line.find("{")
        if col != -1:
            return row_idx, col
    return None


def move_towards(session, player_pos, target_pos):
    pr, pc = player_pos
    tr, tc = target_pos
    dr = tr - pr
    dc = tc - pc
    if dr == 0 and dc == 0:
        return True

    key = ""
    if dr < 0 and dc < 0:
        key = "y"
    elif dr < 0 and dc == 0:
        key = "k"
    elif dr < 0 and dc > 0:
        key = "u"
    elif dr == 0 and dc < 0:
        key = "h"
    elif dr == 0 and dc > 0:
        key = "l"
    elif dr > 0 and dc < 0:
        key = "b"
    elif dr > 0 and dc == 0:
        key = "j"
    elif dr > 0 and dc > 0:
        key = "n"

    if key:
        tmux_send(session, key)
        time.sleep(0.2)
    return False


def handle_prompts(session):
    for _ in range(15):
        screen = tmux_capture(session)
        if "--More--" in screen:
            tmux_send(session, " ")
            time.sleep(0.3)
        elif "For what do you wish?" in screen:
            return "WISH"
        elif "Do you want your possessions identified?" in screen:
            return "DEAD"
        elif "Really quit?" in screen:
            tmux_send(session, "y")
            time.sleep(0.3)
            return "QUIT"
        elif "[ynaq]" in screen:
            tmux_send(session, "n")
            time.sleep(0.3)
        elif "[ynq]" in screen or "[yn]" in screen:
            tmux_send(session, "n")
            time.sleep(0.3)
        elif "(end)" in screen:
            tmux_send(session, " ")
            time.sleep(0.3)
        elif "Pick up what?" in screen or "Pick an object" in screen:
            tmux_send(session, "\x1b")
            time.sleep(0.2)
        elif "What do you want to drink" in screen:
            tmux_send(session, "\x1b")
            time.sleep(0.2)
        elif "Pane is dead" in screen:
            return "DEAD"
        else:
            break
    return None


def quaff_fountain(session):
    tmux_send(session, "q")
    time.sleep(0.3)

    screen = tmux_capture(session)
    if "Drink from the fountain" in screen or "drink from" in screen.lower():
        tmux_send(session, "y")
        time.sleep(0.3)
    elif "What do you want to drink" in screen:
        tmux_send(session, "\x1b")
        time.sleep(0.2)
        tmux_send(session, "q")
        time.sleep(0.3)
        tmux_send(session, ".")
        time.sleep(0.3)

    time.sleep(0.3)
    handle_prompts(session)


def quit_game(session):
    tmux_send(session, "\x1b")
    time.sleep(0.2)
    tmux_send_literal(session, "#quit\n")
    time.sleep(0.5)

    for _ in range(10):
        result = handle_prompts(session)
        if result not in ("QUIT", "DEAD"):
            break


def try_lamp(session, screen):
    player_pos = find_player_pos(screen)
    if not player_pos:
        return None

    lines = screen.strip().split("\n")
    map_lines = lines[1:22] if len(lines) > 22 else lines[1:]
    for row_idx, line in enumerate(map_lines):
        col = line.find("(")
        if col == -1:
            continue
        obj_pos = row_idx, col
        if abs(obj_pos[0] - player_pos[0]) > 3 or abs(obj_pos[1] - player_pos[1]) > 3:
            continue

        for _ in range(6):
            screen = tmux_capture(session)
            player_pos = find_player_pos(screen)
            if not player_pos:
                return None
            if player_pos == obj_pos:
                break
            move_towards(session, player_pos, obj_pos)
            time.sleep(0.3)
            result = handle_prompts(session)
            if result:
                return result

        tmux_send(session, ",")
        time.sleep(0.5)
        result = handle_prompts(session)
        if result:
            return result

        tmux_send(session, "a")
        time.sleep(0.3)
        screen = tmux_capture(session)
        if "What do you want to use" in screen:
            tmux_send(session, "b")
            time.sleep(0.5)
            return handle_prompts(session)
        tmux_send(session, "\x1b")
        time.sleep(0.2)
    return None


def play_one_game(session_name, role, nethackrc):
    char_name = make_unique_char_name(DATA_DIR, SAVE_DIR, prefix=role[0].upper())
    hackdir = prepare_session_hackdir(session_name, role)
    env_cmd = (
        f"cd {hackdir} && "
        f"export HACKDIR='{hackdir}' NETHACKOPTIONS='@{nethackrc}'; "
        f"exec {NETHACK} -u {char_name}"
    )
    subprocess.run(
        [
            "tmux",
            "new-session",
            "-d",
            "-s",
            session_name,
            "-x",
            "80",
            "-y",
            "24",
            "bash",
            "-c",
            env_cmd,
        ],
        check=False,
    )

    time.sleep(0.5)
    if not tmux_session_exists(session_name):
        return "ERROR"

    write_status(session_name, "bot_playing", {"char_name": char_name, "role": role, "hackdir": hackdir})

    if not skip_initial_prompts(session_name):
        cleanup_session(session_name)
        return "DEAD"

    game_start = time.time()
    on_fountain = False
    fountain_target = None
    last_player_pos = None
    stuck_count = 0
    explore_steps = 0

    while time.time() - game_start < GAME_TIMEOUT:
        if not tmux_session_exists(session_name):
            cleanup_session(session_name)
            return "DEAD"

        screen = tmux_capture(session_name)
        if not screen.strip():
            time.sleep(0.5)
            continue

        if "For what do you wish?" in screen:
            write_status(session_name, "wish_ready", {"char_name": char_name, "role": role, "hackdir": hackdir})
            return "WISH"
        if "Do you want your possessions identified?" in screen:
            tmux_send(session_name, "n")
            time.sleep(0.5)
            handle_prompts(session_name)
            cleanup_session(session_name)
            return "DEAD"

        result = handle_prompts(session_name)
        if result == "WISH":
            write_status(session_name, "wish_ready", {"char_name": char_name, "role": role, "hackdir": hackdir})
            return "WISH"
        if result == "DEAD":
            cleanup_session(session_name)
            return "DEAD"

        if on_fountain:
            if "dried up" in screen or "no longer" in screen:
                on_fountain = False
                fountain_target = None
                explore_steps = 0
                continue

            quaff_fountain(session_name)
            time.sleep(0.3)
            screen = tmux_capture(session_name)
            if "For what do you wish?" in screen:
                write_status(session_name, "wish_ready", {"char_name": char_name, "role": role, "hackdir": hackdir})
                return "WISH"
            result = handle_prompts(session_name)
            if result == "WISH":
                write_status(session_name, "wish_ready", {"char_name": char_name, "role": role, "hackdir": hackdir})
                return "WISH"
            if result == "DEAD":
                cleanup_session(session_name)
                return "DEAD"
            if "don't have anything to drink" in screen:
                on_fountain = False
                fountain_target = None
                explore_steps = 0
            continue

        fountain_pos = find_fountain_pos(screen)
        if fountain_pos:
            player_pos = find_player_pos(screen)
            if player_pos:
                fountain_target = fountain_pos
                if player_pos == last_player_pos:
                    stuck_count += 1
                    if stuck_count > 8:
                        quit_game(session_name)
                        cleanup_session(session_name)
                        return "STUCK"
                    tmux_send(session_name, random.choice("hjklyubn"))
                    time.sleep(0.3)
                    handle_prompts(session_name)
                    continue
                stuck_count = 0
                last_player_pos = player_pos

                on_target = move_towards(session_name, player_pos, fountain_pos)
                time.sleep(0.3)
                result = handle_prompts(session_name)
                if result == "WISH":
                    write_status(session_name, "wish_ready", {"char_name": char_name, "role": role, "hackdir": hackdir})
                    return "WISH"
                if result == "DEAD":
                    cleanup_session(session_name)
                    return "DEAD"
                if on_target:
                    on_fountain = True
                continue

            tmux_send(session_name, random.choice("hjklyubn"))
            time.sleep(0.3)
            handle_prompts(session_name)
            continue

        if fountain_target:
            player_pos = find_player_pos(screen)
            if player_pos and player_pos == fountain_target:
                on_fountain = True
                continue
            fountain_target = None

        result = try_lamp(session_name, screen)
        if result == "WISH":
            write_status(session_name, "wish_ready", {"char_name": char_name, "role": role, "hackdir": hackdir})
            return "WISH"
        if result == "DEAD":
            cleanup_session(session_name)
            return "DEAD"

        if explore_steps < 30:
            explore_steps += 1
            tmux_send(session_name, random.choice("hjklyubn"))
            time.sleep(0.15)
            result = handle_prompts(session_name)
            if result == "WISH":
                write_status(session_name, "wish_ready", {"char_name": char_name, "role": role, "hackdir": hackdir})
                return "WISH"
            if result == "DEAD":
                cleanup_session(session_name)
                return "DEAD"
            continue

        quit_game(session_name)
        cleanup_session(session_name)
        return "NO_FOUNTAIN"

    quit_game(session_name)
    cleanup_session(session_name)
    return "TIMEOUT"


def run_bot():
    os.makedirs(DATA_DIR, exist_ok=True)
    role = selected_role()
    nethackrc = make_bot_nethackrc(role)
    session_prefix = f"wish-{role.lower()}-{random_id()}"
    attempt = 0

    try:
        while True:
            attempt += 1
            current_session = f"{session_prefix}-{attempt}"
            result = play_one_game(current_session, role, nethackrc)
            if result == "WISH":
                print(f"[BOT] {role} WISH FOUND in session {current_session} after {attempt} attempts!")
                sys.exit(0)
            print(f"[BOT] {role} attempt {attempt}: {result} (session {current_session})")
            time.sleep(0.3)
    finally:
        try:
            os.remove(nethackrc)
        except OSError:
            pass


if __name__ == "__main__":
    run_bot()
