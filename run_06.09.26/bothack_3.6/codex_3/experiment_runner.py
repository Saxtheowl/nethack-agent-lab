"""Shared CLI adapter that runs an experiment without modifying BotHack."""
from __future__ import annotations

import hashlib
import json
import os
import random
import sys
from pathlib import Path

from jev_common import (DEFAULT_MODEL, DEFAULT_URL, DecisionJournal,
                        OpenRouterDecider)


ROOT = Path(__file__).resolve().parent
DEFAULT_BASE = ROOT.parent / "claude"


def _hash_files(paths):
    h = hashlib.sha256()
    for path in paths:
        path = Path(path)
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()[:16]


def run(mode, installer, argv=None, extra_files=()):
    argv = list(sys.argv[1:] if argv is None else argv)
    base = os.environ.get("BOTHACK_BASE", str(DEFAULT_BASE))
    if "--bothack-base" in argv:
        i = argv.index("--bothack-base")
        base = argv[i + 1]
        del argv[i:i + 2]
    base = str(Path(base).resolve())
    if not Path(base, "nhbot", "rungame.py").exists():
        raise SystemExit("BotHack base not found: %s" % base)
    sys.path.insert(0, base)

    from nhbot import rungame
    import pybothack.bh36 as bh36

    parser = rungame.build_parser()
    parser.add_argument("--bothack-base", help="handled before parsing")
    parser.add_argument("--jev-model", default=DEFAULT_MODEL)
    parser.add_argument("--jev-url", default=DEFAULT_URL)
    parser.add_argument("--jev-timeout", type=float, default=30.0)
    parser.add_argument("--jev-retries", type=int, default=2)
    parser.add_argument("--jev-offline", action="store_true",
                        help="smoke test only: choose the first option, no API")
    parser.add_argument("--jev-on-error", choices=("stop", "safe"),
                        default="stop")
    parser.add_argument("--jev-max-decisions", type=int, default=0,
                        help="hard cap on paid model decisions (0 disables)")
    parser.add_argument("--jev-repeat-limit", type=int, default=0,
                        help="stop after this many identical intentions")
    parser.add_argument("--jev-depth-patience", type=int, default=0,
                        help="stop after this many decisions without a new depth")
    parser.add_argument("--jev-intent-steps", type=int, default=1,
                        help="reuse a high-level intention for this many actions")
    args = parser.parse_args(argv)
    out = str(Path(args.out).resolve())
    journal = DecisionJournal(out, mode)
    decider = OpenRouterDecider(model=args.jev_model, url=args.jev_url,
                                timeout=args.jev_timeout,
                                retries=args.jev_retries,
                                offline=args.jev_offline)
    original = bh36.new_bh36
    original_supervisor = rungame.Supervisor
    holder = {}

    from pybothack.nhbridge import BridgeAbort

    class JevSupervisor(original_supervisor):
        def on_request(self, bridge, req):
            if journal.stop_reason:
                raise BridgeAbort("stuck", journal.stop_reason)
            if (args.jev_max_decisions and
                    journal.calls >= args.jev_max_decisions):
                raise BridgeAbort(
                    "limit", "jev_max_decisions %d" % args.jev_max_decisions)
            return super().on_request(bridge, req)

    rungame.Supervisor = JevSupervisor

    def factory(config=None, rng=None):
        bh = original(config, rng=rng)
        holder["bh"] = bh
        installer(bh, decider, journal, args)
        return bh

    bh36.new_bh36 = factory
    result = None
    try:
        if args.scenario:
            args.wizard = True
            from nhbot import scenarios
            scenario = scenarios.load(args.scenario)
            if args.max_turns is None and scenario.get("max_turns"):
                args.max_turns = scenario["max_turns"]
            if scenario.get("profile") and args.profile == "full":
                args.profile = scenario["profile"]
            if scenario.get("skip"):
                os.environ["BOTHACK_SKIP"] = ",".join(scenario["skip"])
        if args.no_assist:
            args.invincible = False
            args.nostarve = False
            args.kit = "none"
        os.environ["BOTHACK_PROFILE"] = args.profile
        if args.tactics is None:
            args.tactics = "assisted" if args.invincible else "normal"
        os.environ["BOTHACK_TACTICS"] = args.tactics
        result = rungame.run_game(args)
    finally:
        bh36.new_bh36 = original
        rungame.Supervisor = original_supervisor
        final_state = None
        if holder.get("bh") is not None:
            try:
                from jev_policy_support import game_state
                final_state = game_state(holder["bh"].game.deref())
            except Exception:
                pass
        journal.close(final_state)

    files = [ROOT / "jev_common.py", ROOT / "experiment_runner.py",
             ROOT / "jev_policy_support.py"]
    files.extend(Path(p) for p in extra_files)
    metadata = {
        "mode": mode, "model": args.jev_model, "endpoint": args.jev_url,
        "offline": args.jev_offline, "bothack_base": base,
        "experiment_code_hash": _hash_files(files),
        "decision_log": "jev_decisions.jsonl",
        "limitations": ("Jev is a typed choice model; it selects only from "
                        "the candidates exposed by this policy."),
        "estimated_input_price_usd_per_million": 0.042,
    }
    manifest_path = Path(out, "manifest.json")
    manifest = json.loads(manifest_path.read_text())
    manifest["experiment"] = metadata
    manifest_path.write_text(json.dumps(manifest, indent=1) + "\n")
    result["experiment"] = metadata
    result["jev"] = journal.summary()
    Path(out, "result.json").write_text(json.dumps(result, indent=1) + "\n")
    summary = {k: result.get(k) for k in
               ("outcome", "reason", "turns", "lvl", "max_depth", "xl",
                "last_stage", "elapsed_s", "turns_per_s", "jev")}
    print(json.dumps(summary))
    return 0
