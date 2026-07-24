"""Parallel counted Minetown runs using AutoAscend's public-observation agent."""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from .env import NetHackMinetown
from .runner import _json_default, _print_progress, _summary, _ttyrec_in, _xlog_death


ROOT = Path(__file__).resolve().parents[1]
AUTOASCEND_ROOT = ROOT / "research" / "autoascend"


class OldGymAPI:
    """Expose the old four-value Gym API expected by AutoAscend."""

    def __init__(self, env):
        self.env = env
        self._actions = list(env.actions)
        self._steps = 0
        self._turns = 0

    def __getattr__(self, name):
        return getattr(self.env, name)

    def reset(self):
        self._steps = 0
        return self.env.reset()[0]

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        self._steps += 1
        self._turns = int(obs["blstats"][20])
        return obs, reward, terminated or truncated, info

    def get_seeds(self):
        # Counted games deliberately disable deterministic seeding.
        return None, None


def run_episode(episode: int, run_dir: str, max_steps: int, record: bool) -> dict:
    if str(AUTOASCEND_ROOT) not in sys.path:
        sys.path.insert(0, str(AUTOASCEND_ROOT))
    from autoascend.env_wrapper import EnvWrapper

    episode_dir = Path(run_dir) / "episodes" / f"{episode:06d}"
    episode_dir.mkdir(parents=True, exist_ok=True)
    base = None
    wrapped = None
    result = {
        "episode": episode,
        "counted": True,
        "character": "val-dwa-fem-law",
        "nethack": "3.6.7",
        "success": False,
        "steps": 0,
    }
    try:
        base = NetHackMinetown(
            max_episode_steps=max_steps,
            save_ttyrec_every=1 if record else 0,
            savedir=str(episode_dir) if record else None,
            fix_moon_phase=False,
        )
        wrapped = EnvWrapper(
            OldGymAPI(base),
            visualizer_args={"enable": False},
            step_limit=None,
            # AutoAscend recovers from parser assertions by resetting its
            # inferred state. These assertions caused 5/18 strict failures.
            agent_args={"panic_on_errors": True, "verbose": False},
        )
        wrapped.main()
        result["steps"] = wrapped.step_count
        result["success"] = wrapped.end_reason == "Minetown"
        result["end_reason"] = wrapped.end_reason
        result["policy"] = {
            "engine": "autoascend",
            "panics": len(wrapped.agent.all_panics),
            "panic_causes": Counter(
                f"{type(exc).__name__}: {str(exc)[:240]}"
                for exc in wrapped.agent.all_panics
            ).most_common(5),
            "milestone": str(wrapped.agent.global_logic.milestone),
            "dungeon": int(wrapped.agent.blstats.dungeon_number),
            "dlevel": int(wrapped.agent.blstats.level_number),
            "turn": int(wrapped.agent.blstats.time),
            "armor_class": int(wrapped.agent.blstats.armor_class),
            "hp": int(wrapped.agent.blstats.hitpoints),
            "hpmax": int(wrapped.agent.blstats.max_hitpoints),
            "hunger": int(wrapped.agent.blstats.hunger_state),
            "nutrition_stock": int(wrapped.agent.inventory.items.total_nutrition()),
            "searches": int(sum(level.search_count.sum()
                                  for level in wrapped.agent.levels.values())),
            "visited_tiles": int(sum(level.was_on.sum()
                                      for level in wrapped.agent.levels.values())),
            "known_levels": len(wrapped.agent.levels),
            "experience_level": int(wrapped.agent.blstats.experience_level),
            "forage_attacks": int(wrapped.agent._forage_attacks),
            "inventory": str(wrapped.agent.inventory.items),
        }
    except BaseException as exc:
        result["steps"] = wrapped.step_count if wrapped is not None else 0
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        if wrapped is not None:
            result["end_reason"] = wrapped.end_reason
            result["success"] = wrapped.end_reason == "Minetown"
    finally:
        if base is not None:
            base.close()

    result["ttyrec"] = _ttyrec_in(episode_dir)
    result["death"] = _xlog_death(episode_dir)
    if result["success"]:
        result["failure_cause"] = "success"
    elif result.get("death"):
        result["failure_cause"] = f"combat:{result['death']}"
    elif result.get("error"):
        result["failure_cause"] = "agent_error"
    else:
        result["failure_cause"] = "step_timeout"
    (episode_dir / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, default=_json_default) + "\n"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument("--max-steps", type=int, default=50_000)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--no-record", action="store_true")
    args = parser.parse_args()
    args.run_dir.mkdir(parents=True, exist_ok=True)
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(run_episode, i, str(args.run_dir), args.max_steps, not args.no_record)
            for i in range(args.episodes)
        ]
        for future in as_completed(futures):
            results.append(future.result())
            _print_progress(results)
    results.sort(key=lambda row: row["episode"])
    summary = _summary(results)
    (args.run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
