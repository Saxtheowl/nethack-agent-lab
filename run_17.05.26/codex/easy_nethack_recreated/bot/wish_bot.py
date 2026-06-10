#!/usr/bin/env python3
"""
Wish Bot - Plays NetHack as a Valkyrie Dwarf, drinks from fountains
until getting "For what do you wish?" prompt, then stops.

The bot runs inside a tmux session so a player can later attach to it.
"""

import json
import os
import random
import string
import subprocess
import sys
import time

from wish_utils import make_unique_char_name

NETHACK = "/usr/local/bin/nethack"
BOT_NETHACKRC = "/opt/nethack/nethackrc.bot"
DATA_DIR = "/data/sessions"
SAVE_DIR = "/data/saves"
# Max time (seconds) to spend on a single game before quitting
GAME_TIMEOUT = 120


def random_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))


def tmux_send(session, keys):
    """Send keys to a tmux session."""
    subprocess.run(["tmux", "send-keys", "-t", session, keys], check=False)


def tmux_send_literal(session, text):
    """Send literal text to a tmux session (no key interpretation)."""
    subprocess.run(["tmux", "send-keys", "-t", session, "-l", text], check=False)


def tmux_capture(session):
    """Capture the current tmux pane content."""
    result = subprocess.run(
        ["tmux", "capture-pane", "-t", session, "-p"],
        capture_output=True, text=True, check=False
    )
    return result.stdout if result.returncode == 0 else ""


def tmux_session_exists(session):
    """Check if a tmux session exists."""
    result = subprocess.run(
        ["tmux", "has-session", "-t", session],
        capture_output=True, check=False
    )
    return result.returncode == 0


def write_status(session_name, status, extra=None):
    """Write session status to JSON file."""
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
    """Kill tmux session and remove status file."""
    subprocess.run(["tmux", "kill-session", "-t", session_name], check=False)
    status_file = os.path.join(DATA_DIR, f"{session_name}.json")
    if os.path.exists(status_file):
        os.remove(status_file)


def wait_for_screen(session, text, timeout=10, interval=0.3):
    """Wait until text appears on screen. Returns True if found."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        screen = tmux_capture(session)
        if text in screen:
            return True
        time.sleep(interval)
    return False


def skip_initial_prompts(session):
    """Skip through any initial prompts/messages until the map appears."""
    # Wait a moment for nethack to start
    time.sleep(1)

    # Press space/enter to skip any remaining prompts for up to 10 seconds
    deadline = time.time() + 10
    while time.time() < deadline:
        screen = tmux_capture(session)

        # Check if we died already or game over
        if "Do you want your possessions identified?" in screen:
            return False
        if "Really quit?" in screen:
            tmux_send(session, "y")
            time.sleep(0.5)
            return False

        # If we see the player '@' on screen, the map is showing
        lines = screen.strip().split('\n')
        # Look for '@' in the map area (lines 1-21 roughly)
        map_lines = lines[1:22] if len(lines) > 22 else lines[1:]
        for line in map_lines:
            if '@' in line:
                return True

        # Press space to dismiss any prompt
        tmux_send(session, " ")
        time.sleep(0.5)

    return False


def find_fountain(screen):
    """Check if there's a fountain '{' on the map."""
    lines = screen.strip().split('\n')
    map_lines = lines[1:22] if len(lines) > 22 else lines[1:]
    for line in map_lines:
        if '{' in line:
            return True
    return False


def find_player_pos(screen):
    """Find the player '@' position on the map. Returns (row, col) or None."""
    lines = screen.strip().split('\n')
    map_lines = lines[1:22] if len(lines) > 22 else lines[1:]
    for row_idx, line in enumerate(map_lines):
        col = line.find('@')
        if col != -1:
            return (row_idx, col)
    return None


def find_fountain_pos(screen):
    """Find the nearest fountain '{' position. Returns (row, col) or None."""
    lines = screen.strip().split('\n')
    map_lines = lines[1:22] if len(lines) > 22 else lines[1:]
    for row_idx, line in enumerate(map_lines):
        col = line.find('{')
        if col != -1:
            return (row_idx, col)
    return None


def move_towards(session, player_pos, target_pos):
    """Send movement keys to move player towards target. Returns True if on target."""
    pr, pc = player_pos
    tr, tc = target_pos

    dr = tr - pr
    dc = tc - pc

    # If already on the target, return True
    if dr == 0 and dc == 0:
        return True

    # Determine movement direction
    key = ""
    if dr < 0 and dc < 0:
        key = "y"  # up-left
    elif dr < 0 and dc == 0:
        key = "k"  # up
    elif dr < 0 and dc > 0:
        key = "u"  # up-right
    elif dr == 0 and dc < 0:
        key = "h"  # left
    elif dr == 0 and dc > 0:
        key = "l"  # right
    elif dr > 0 and dc < 0:
        key = "b"  # down-left
    elif dr > 0 and dc == 0:
        key = "j"  # down
    elif dr > 0 and dc > 0:
        key = "n"  # down-right

    if key:
        tmux_send(session, key)
        time.sleep(0.2)

    return False


def quaff_fountain(session):
    """Try to quaff from a fountain at the current position."""
    tmux_send(session, "q")  # quaff command
    time.sleep(0.3)

    screen = tmux_capture(session)
    # NetHack asks which direction or "Drink from the fountain?"
    if "Drink from the fountain" in screen:
        tmux_send(session, "y")
        time.sleep(0.3)
    elif "drink from" in screen.lower():
        tmux_send(session, "y")
        time.sleep(0.3)
    elif "What do you want to drink" in screen:
        # It's asking us to pick an inventory item - we don't want that
        tmux_send(session, "\x1b")  # escape
        time.sleep(0.2)
        # Try quaffing at fountain with '.' for "here"
        tmux_send(session, "q")
        time.sleep(0.3)
        tmux_send(session, ".")
        time.sleep(0.3)

    # Handle --More-- prompts
    time.sleep(0.3)
    handle_prompts(session)


def handle_prompts(session):
    """Handle --More-- and other prompts after an action."""
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
            # "Do you want an account of creatures vanquished?" etc.
            tmux_send(session, "n")
            time.sleep(0.3)
        elif "[ynq]" in screen or "[yn]" in screen:
            # Generic yes/no prompts (attributes, etc.) - dismiss with 'n'
            tmux_send(session, "n")
            time.sleep(0.3)
        elif "(end)" in screen:
            tmux_send(session, " ")  # dismiss info screen
            time.sleep(0.3)
        elif "Pick up what?" in screen or "Pick an object" in screen:
            tmux_send(session, "\x1b")  # escape
            time.sleep(0.2)
        elif "What do you want to drink" in screen:
            tmux_send(session, "\x1b")  # escape
            time.sleep(0.2)
        elif "Pane is dead" in screen:
            return "DEAD"
        else:
            break
    return None


def quit_game(session):
    """Quit the current game."""
    # First escape any current prompt
    tmux_send(session, "\x1b")
    time.sleep(0.2)
    # Send #quit - use literal mode for the '#' character
    tmux_send_literal(session, "#quit\n")
    time.sleep(0.5)

    for _ in range(10):
        screen = tmux_capture(session)
        if "Really quit?" in screen:
            tmux_send(session, "y")
            time.sleep(0.3)
        elif "Do you want your possessions identified?" in screen:
            tmux_send(session, "n")
            time.sleep(0.3)
        elif "--More--" in screen:
            tmux_send(session, " ")
            time.sleep(0.3)
        elif "[ynaq]" in screen:
            tmux_send(session, "n")
            time.sleep(0.3)
        elif "[ynq]" in screen or "[yn]" in screen:
            tmux_send(session, "n")
            time.sleep(0.3)
        elif "(end)" in screen:
            tmux_send(session, " ")
            time.sleep(0.3)
        else:
            break


def try_lamp(session, screen):
    """If there's an object '(' on the ground, try to pick it up and apply it."""
    player_pos = find_player_pos(screen)
    if not player_pos:
        return None

    # Check if there's a '(' (tool/lamp) visible nearby
    lines = screen.strip().split('\n')
    map_lines = lines[1:22] if len(lines) > 22 else lines[1:]

    for row_idx, line in enumerate(map_lines):
        col = line.find('(')
        if col != -1:
            obj_pos = (row_idx, col)
            # Try to walk to it if close
            pr, pc = player_pos
            if abs(obj_pos[0] - pr) <= 3 and abs(obj_pos[1] - pc) <= 3:
                # Move towards the object
                for _ in range(6):
                    screen = tmux_capture(session)
                    player_pos = find_player_pos(screen)
                    if not player_pos:
                        return None
                    if player_pos[0] == obj_pos[0] and player_pos[1] == obj_pos[1]:
                        break
                    move_towards(session, player_pos, obj_pos)
                    time.sleep(0.3)
                    result = handle_prompts(session)
                    if result == "WISH":
                        return "WISH"
                    if result == "DEAD":
                        return "DEAD"

                # Pick up
                tmux_send(session, ",")
                time.sleep(0.5)
                result = handle_prompts(session)
                if result == "WISH":
                    return "WISH"

                # Try to apply (rub) it
                tmux_send(session, "a")
                time.sleep(0.3)
                screen = tmux_capture(session)
                # If inventory selection, pick first tool-like item
                if "What do you want to use" in screen:
                    # Try common lamp letters
                    tmux_send(session, "b")
                    time.sleep(0.5)
                    result = handle_prompts(session)
                    if result == "WISH":
                        return "WISH"
                else:
                    tmux_send(session, "\x1b")
                    time.sleep(0.2)

    return None


def make_char_name():
    """Generate a unique character name for this game."""
    return make_unique_char_name(DATA_DIR, SAVE_DIR)


def play_one_game(session_name):
    """
    Play a single NetHack game, drinking from fountains.
    Returns 'WISH' if wish prompt found, 'DEAD' if died, 'TIMEOUT' if timed out.
    """
    # Each game gets a unique character name to avoid save file collisions
    char_name = make_char_name()

    # Create tmux session with nethack
    env_cmd = f"export NETHACKOPTIONS='@{BOT_NETHACKRC}'; exec {NETHACK} -u {char_name}"
    subprocess.run([
        "tmux", "new-session", "-d", "-s", session_name,
        "-x", "80", "-y", "24",
        "bash", "-c", env_cmd
    ], check=False)

    time.sleep(0.5)

    if not tmux_session_exists(session_name):
        return "ERROR"

    write_status(session_name, "bot_playing", {"char_name": char_name})

    # Wait for the game to start and map to appear
    if not skip_initial_prompts(session_name):
        cleanup_session(session_name)
        return "DEAD"

    game_start = time.time()
    quaff_attempts = 0
    on_fountain = False  # Track if we've walked onto a fountain
    fountain_target = None  # Remembered fountain position
    last_player_pos = None
    stuck_count = 0
    explore_steps = 0  # Steps taken exploring without a fountain

    while time.time() - game_start < GAME_TIMEOUT:
        if not tmux_session_exists(session_name):
            # Session died (nethack crashed/exited)
            cleanup_session(session_name)
            return "DEAD"

        screen = tmux_capture(session_name)

        if not screen.strip():
            time.sleep(0.5)
            continue

        # Check for wish
        if "For what do you wish?" in screen:
            write_status(session_name, "wish_ready", {"char_name": char_name})
            return "WISH"

        # Check for death
        if "Do you want your possessions identified?" in screen:
            tmux_send(session_name, "n")
            time.sleep(0.5)
            handle_prompts(session_name)
            cleanup_session(session_name)
            return "DEAD"

        # Handle any pending prompts
        result = handle_prompts(session_name)
        if result == "WISH":
            write_status(session_name, "wish_ready", {"char_name": char_name})
            return "WISH"
        if result == "DEAD":
            cleanup_session(session_name)
            return "DEAD"

        # If we're standing on a fountain, keep quaffing
        if on_fountain:
            # Check if "dried up" or "no longer" in recent output
            if "dried up" in screen or "no longer" in screen:
                on_fountain = False
                fountain_target = None
                # Reset explore to look for another fountain on this level
                explore_steps = 0
                continue

            quaff_fountain(session_name)
            quaff_attempts += 1
            time.sleep(0.3)

            # Check result after quaff
            screen = tmux_capture(session_name)
            if "For what do you wish?" in screen:
                write_status(session_name, "wish_ready", {"char_name": char_name})
                return "WISH"
            result = handle_prompts(session_name)
            if result == "WISH":
                write_status(session_name, "wish_ready", {"char_name": char_name})
                return "WISH"
            if result == "DEAD":
                cleanup_session(session_name)
                return "DEAD"

            # Check if fountain dried up (we'll see no { and message about drying)
            screen = tmux_capture(session_name)
            if "don't have anything to drink" in screen:
                # Not on fountain anymore, or it dried up
                on_fountain = False
                fountain_target = None
                explore_steps = 0  # Explore for more fountains
            continue

        # Check for fountain on the map
        if find_fountain(screen):
            player_pos = find_player_pos(screen)
            fountain_pos = find_fountain_pos(screen)

            if player_pos and fountain_pos:
                fountain_target = fountain_pos

                # Stuck detection: if we haven't moved, try random direction or give up
                if player_pos == last_player_pos:
                    stuck_count += 1
                    if stuck_count > 8:
                        # Can't reach fountain, give up on this game
                        quit_game(session_name)
                        time.sleep(0.5)
                        handle_prompts(session_name)
                        cleanup_session(session_name)
                        return "STUCK"
                    # Try a random direction to get unstuck
                    tmux_send(session_name, random.choice("hjklyubn"))
                    time.sleep(0.3)
                    handle_prompts(session_name)
                    continue
                else:
                    stuck_count = 0
                last_player_pos = player_pos

                # Move to fountain
                on_target = move_towards(session_name, player_pos, fountain_pos)
                time.sleep(0.3)

                result = handle_prompts(session_name)
                if result == "WISH":
                    write_status(session_name, "wish_ready", {"char_name": char_name})
                    return "WISH"
                if result == "DEAD":
                    cleanup_session(session_name)
                    return "DEAD"

                if on_target:
                    # We're on the fountain now
                    on_fountain = True
                # Either way, loop again
                continue
            else:
                # Can't find positions, try moving randomly
                tmux_send(session_name, random.choice("hjklyubn"))
                time.sleep(0.3)
                handle_prompts(session_name)
        else:
            # No fountain visible
            # If we were heading to a fountain and it disappeared, we might be on it
            if fountain_target:
                player_pos = find_player_pos(screen)
                if player_pos and player_pos == fountain_target:
                    on_fountain = True
                    continue
                fountain_target = None

            # Try lamp strategy briefly
            result = try_lamp(session_name, screen)
            if result == "WISH":
                write_status(session_name, "wish_ready", {"char_name": char_name})
                return "WISH"

            # Explore: walk around briefly to find a fountain
            if explore_steps < 30:
                explore_steps += 1
                # Quick random movement to check nearby rooms
                tmux_send(session_name, random.choice("hjklyubn"))
                time.sleep(0.15)
                result = handle_prompts(session_name)
                if result == "WISH":
                    write_status(session_name, "wish_ready", {"char_name": char_name})
                    return "WISH"
                if result == "DEAD":
                    cleanup_session(session_name)
                    return "DEAD"
                continue

            # No fountain found quickly - quit and try a new game
            quit_game(session_name)
            time.sleep(0.5)
            handle_prompts(session_name)
            cleanup_session(session_name)
            return "NO_FOUNTAIN"

    # Timeout
    quit_game(session_name)
    time.sleep(0.5)
    handle_prompts(session_name)
    cleanup_session(session_name)
    return "TIMEOUT"


def run_bot():
    """Main bot loop: keep trying games until we get a wish."""
    os.makedirs(DATA_DIR, exist_ok=True)

    session_name = f"wish-{random_id()}"
    attempt = 0

    while True:
        attempt += 1
        current_session = f"{session_name}-{attempt}"
        result = play_one_game(current_session)

        if result == "WISH":
            print(f"[BOT] WISH FOUND in session {current_session} after {attempt} attempts!")
            sys.exit(0)
        else:
            print(f"[BOT] Attempt {attempt}: {result} (session {current_session})")
            # Brief pause between attempts
            time.sleep(0.3)


if __name__ == "__main__":
    run_bot()
