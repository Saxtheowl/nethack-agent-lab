#!/usr/bin/env python3
"""Shared helpers for wish game metadata and character allocation."""

from __future__ import annotations

import glob
import json
import os
import random
import re
import string
import subprocess
import sys
import time

CLAIM_LABEL_RE = re.compile(r"wish partie (\d+)$")
SAVE_FILE_RE = re.compile(r"^[0-9]+")
CHAR_ALPHABET = string.ascii_lowercase + string.digits


def load_json(path):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def iter_json_dir(directory):
    for path in sorted(glob.glob(os.path.join(directory, "*.json"))):
        data = load_json(path)
        if data is None:
            continue
        yield path, data


def list_tmux_sessions():
    result = subprocess.run(
        ["tmux", "list-sessions", "-F", "#{session_name}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def save_name_from_path(path):
    base = os.path.basename(path)
    if not base.endswith(".gz"):
        return None
    return SAVE_FILE_RE.sub("", base[:-3])


def list_save_names(save_dir):
    names = set()
    for path in glob.glob(os.path.join(save_dir, "*.gz")):
        name = save_name_from_path(path)
        if name:
            names.add(name)
    return names


def list_session_char_names(data_dir):
    names = set()
    for _, data in iter_json_dir(data_dir):
        char_name = data.get("char_name")
        if char_name:
            names.add(char_name)
    return names


def existing_character_names(data_dir, save_dir):
    return list_session_char_names(data_dir) | list_save_names(save_dir)


def make_unique_char_name(data_dir, save_dir, prefix="W", suffix_len=7):
    existing = existing_character_names(data_dir, save_dir)
    for _ in range(4096):
        candidate = prefix + "".join(random.choices(CHAR_ALPHABET, k=suffix_len))
        if candidate not in existing:
            return candidate
    raise RuntimeError("failed to allocate a unique wish character name")


def claim_records(claim_dir):
    records = []
    for path, data in iter_json_dir(claim_dir):
        data["_path"] = path
        records.append(data)
    return records


def claim_index_by_char_name(claim_dir):
    return {
        record.get("char_name"): record
        for record in claim_records(claim_dir)
        if record.get("char_name")
    }


def ensure_claimed_wish(claim_dir, session_name, char_name, role="", hackdir=""):
    os.makedirs(claim_dir, exist_ok=True)

    existing = None
    max_id = 0

    for record in claim_records(claim_dir):
        label = record.get("label", "")
        match = CLAIM_LABEL_RE.match(label)
        if match:
            max_id = max(max_id, int(match.group(1)))
        if record.get("char_name") == char_name:
            existing = record

    now = int(time.time())
    if existing:
        record = dict(existing)
        record["source_session"] = session_name
        if role:
            record["role"] = role
        if hackdir:
            record["hackdir"] = hackdir
        record["updated_at"] = now
        path = record["_path"]
    else:
        claim_id = max_id + 1
        record = {
            "claim_id": claim_id,
            "label": f"wish partie {claim_id}",
            "char_name": char_name,
            "role": role,
            "hackdir": hackdir,
            "source_session": session_name,
            "created_at": now,
            "updated_at": now,
        }
        path = os.path.join(claim_dir, f"{claim_id:04d}_{char_name}.json")

    record.pop("_path", None)
    with open(path, "w") as fh:
        json.dump(record, fh)
    return record


def list_wish_ready_sessions(data_dir, role_filter=None):
    active_sessions = list_tmux_sessions()
    ready = []
    for path, data in iter_json_dir(data_dir):
        if data.get("status") != "wish_ready":
            continue
        if role_filter and data.get("role") != role_filter:
            continue
        session_name = data.get("session_name")
        if not session_name or session_name not in active_sessions:
            continue
        ready.append(
            {
                "path": path,
                "session_name": session_name,
                "char_name": data.get("char_name", "?"),
                "role": data.get("role", ""),
                "hackdir": data.get("hackdir", ""),
            }
        )
    return ready


def list_claimed_active_sessions(data_dir, claim_dir):
    active_sessions = list_tmux_sessions()
    claims = claim_index_by_char_name(claim_dir)
    sessions = []

    for _, data in iter_json_dir(data_dir):
        if data.get("status") != "claimed":
            continue
        session_name = data.get("session_name")
        char_name = data.get("char_name")
        if not session_name or not char_name or session_name not in active_sessions:
            continue
        claim = claims.get(char_name, {})
        sessions.append(
            {
                "session_name": session_name,
                "char_name": char_name,
                "label": claim.get("label", "wish"),
                "claim_id": claim.get("claim_id", ""),
                "source_session": claim.get("source_session", ""),
                "role": claim.get("role", data.get("role", "")),
                "hackdir": claim.get("hackdir", data.get("hackdir", "")),
            }
        )
    return sessions


def cmd_claim_info(args):
    claim_dir, char_name = args
    claim = claim_index_by_char_name(claim_dir).get(char_name)
    if not claim:
        return 1
    print(claim.get("label", "wish"))
    print(claim.get("claim_id", ""))
    print(claim.get("source_session", ""))
    print(claim.get("role", ""))
    print(claim.get("hackdir", ""))
    print(claim.get("dlvl", ""))
    print(claim.get("exp", ""))
    print(claim.get("turns", ""))
    return 0


def cmd_ensure_claim(args):
    claim_dir, session_name, char_name, *rest = args
    role = rest[0] if rest else ""
    hackdir = rest[1] if len(rest) > 1 else ""
    record = ensure_claimed_wish(claim_dir, session_name, char_name, role, hackdir)
    print(record["label"])
    return 0


def cmd_list_ready(args):
    data_dir, *rest = args
    role_filter = rest[0] if rest else None
    for record in list_wish_ready_sessions(data_dir, role_filter):
        print(
            "\t".join(
                [
                    record["session_name"],
                    record["char_name"],
                    record["path"],
                    record["role"],
                    record.get("hackdir", ""),
                ]
            )
        )
    return 0


def cmd_list_claimed_active(args):
    data_dir, claim_dir = args
    for record in list_claimed_active_sessions(data_dir, claim_dir):
        print(
            "\t".join(
                [
                    record["session_name"],
                    record["char_name"],
                    record["label"],
                    record.get("role", ""),
                    record.get("hackdir", ""),
                ]
            )
        )
    return 0


def cmd_update_stats(args):
    claim_dir, char_name, dlvl, exp, turns = args
    claim = claim_index_by_char_name(claim_dir).get(char_name)
    if not claim:
        return 1
    path = claim.get("_path")
    if not path:
        return 1
    record = dict(claim)
    record.pop("_path", None)
    if dlvl:
        record["dlvl"] = dlvl
    if exp:
        record["exp"] = exp
    if turns:
        record["turns"] = turns
    record["updated_at"] = int(time.time())
    with open(path, "w") as fh:
        json.dump(record, fh)
    return 0


def main(argv):
    commands = {
        "claim-info": (2, cmd_claim_info),
        "ensure-claim": ((3, 4, 5), cmd_ensure_claim),
        "list-ready": ((1, 2), cmd_list_ready),
        "list-claimed-active": (2, cmd_list_claimed_active),
        "update-stats": (5, cmd_update_stats),
    }
    if len(argv) < 2 or argv[1] not in commands:
        print(
            "usage: wish_utils.py <claim-info|ensure-claim|list-ready|list-claimed-active> ...",
            file=sys.stderr,
        )
        return 2

    arg_count, handler = commands[argv[1]]
    args = argv[2:]
    if isinstance(arg_count, tuple):
        valid_count = len(args) in arg_count
    else:
        valid_count = len(args) == arg_count
    if not valid_count:
        return 2
    return handler(args)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
