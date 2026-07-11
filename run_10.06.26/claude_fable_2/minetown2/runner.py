"""Runner de batchs local/distant avec résumés succès/échecs en direct."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import traceback
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from nle import nethack

from .env import CHARACTER, NetHackMinetown
from .policy import MinetownPolicy


def _json_default(value):
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _classify_failure(result: dict) -> str:
    if result.get("success"):
        return "success"
    if result.get("error"):
        return "agent_error"
    if result.get("death"):
        return f"combat:{result['death']}"
    summary = result.get("policy", {})
    text = " ".join(summary.get("recent_messages", [])).lower()
    hunger = summary.get("hunger")
    if "starv" in text or "faint" in text or (hunger is not None and hunger >= 4):
        return "starvation"
    if "poison" in text:
        return "poison"
    if "drown" in text:
        return "drowning"
    if "killed by" in text or "you die" in text:
        hint = summary.get("failure_hint", "combat")
        return hint if str(hint).startswith("combat:") else "combat"
    if result.get("truncated") or result.get("end_status") == -1:
        actions = summary.get("actions", {})
        if actions.get("wait_blocked", 0) > max(100, result.get("steps", 0) // 3):
            return "blocked_or_stuck"
        return "step_timeout"
    return summary.get("failure_hint", "unknown")


def _ttyrec_in(directory: Path) -> str | None:
    ttyrecs = sorted(directory.glob("*.ttyrec*.bz2"))
    return str(ttyrecs[-1].resolve()) if ttyrecs else None


def _xlog_death(directory: Path) -> str | None:
    files = sorted(directory.glob("*.xlogfile"))
    if not files:
        return None
    lines = files[-1].read_text(errors="replace").splitlines()
    if not lines:
        return None
    fields = {}
    for field in lines[-1].split("\t"):
        key, separator, value = field.partition("=")
        if separator:
            fields[key] = value
    death = fields.get("death", "")
    if death.startswith("killed by "):
        return death.removeprefix("killed by ").removeprefix("a ").removeprefix("an ")
    if death and death not in {"quit", "escaped", "ascended"}:
        return death
    return None


def _snapshot(obs: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    """NLE réutilise ses buffers d'observation : copies indispensables."""

    return {key: value.copy() for key, value in obs.items()}


# Réponses de secours si la politique lève une exception : on alterne pour
# sortir des prompts (ESC), consommer les --More-- (\r) et laisser passer un
# tour (s).  L'épisode continue au lieu de finir en agent_error.
_RECOVERY_KEYS = (int(nethack.Command.ESC), 13, ord("s"))


def run_episode(
    episode: int,
    run_dir: str,
    max_steps: int,
    record: bool,
) -> dict:
    """Une partie comptée, non seedée, non-wizard, dans un process isolé."""

    episode_dir = Path(run_dir) / "episodes" / f"{episode:06d}"
    episode_dir.mkdir(parents=True, exist_ok=True)
    env = None
    obs = None
    last_live_obs = None
    policy = MinetownPolicy()
    result: dict = {
        "episode": episode,
        "counted": True,
        "character": CHARACTER,
        "nethack": "3.6.7",
        "success": False,
        "terminated": False,
        "truncated": False,
        "end_status": None,
        "steps": 0,
        "policy_errors": 0,
        "worker_pid": os.getpid(),
    }
    try:
        env = NetHackMinetown(
            max_episode_steps=max_steps,
            save_ttyrec_every=1 if record else 0,
            savedir=str(episode_dir) if record else None,
            render_mode="ansi",
            fix_moon_phase=False,
        )
        obs, info = env.reset()
        # Le canal privé de l'évaluateur ne doit jamais atteindre la politique.
        if "internal" in obs or "program_state" in obs:
            raise AssertionError("private evaluator observations leaked to policy")
        last_live_obs = _snapshot(obs)

        recovery_cycle = 0
        for step in range(max_steps):
            try:
                action = policy.act(obs)
            except Exception:
                result["policy_errors"] += 1
                if result["policy_errors"] <= 3:
                    result.setdefault("policy_error_tracebacks", []).append(
                        traceback.format_exc()
                    )
                if result["policy_errors"] > 60:
                    raise
                raw = _RECOVERY_KEYS[recovery_cycle % len(_RECOVERY_KEYS)]
                recovery_cycle += 1
                action = MinetownPolicy._index(raw)
            obs, reward, terminated, truncated, info = env.step(action)
            result["steps"] = step + 1
            if int(obs["blstats"][nethack.NLE_BL_HP]) > 0:
                last_live_obs = _snapshot(obs)
            if terminated or truncated:
                result["terminated"] = bool(terminated)
                result["truncated"] = bool(truncated)
                result["end_status"] = int(info.get("end_status", 0))
                result["success"] = result["end_status"] == int(
                    NetHackMinetown.StepStatus.TASK_SUCCESSFUL
                )
                break
        else:
            result["truncated"] = True
            result["end_status"] = -1

        result["policy"] = policy.summary(last_live_obs)
    except BaseException as exc:  # Diagnostics persistés depuis les workers.
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        try:
            result["policy"] = policy.summary(last_live_obs)
        except Exception:
            result["policy"] = {}
    finally:
        if env is not None:
            env.close()

    result["ttyrec"] = _ttyrec_in(episode_dir)
    result["death"] = _xlog_death(episode_dir)
    result["failure_cause"] = _classify_failure(result)
    result_path = episode_dir / "result.json"
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True, default=_json_default) + "\n"
    )
    return result


def wilson(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total))
        / denominator
    )
    return max(0.0, center - margin), min(1.0, center + margin)


def _summary(results: list[dict]) -> dict:
    successes = sum(bool(row.get("success")) for row in results)
    total = len(results)
    low, high = wilson(successes, total)
    successful_steps = [row["steps"] for row in results if row.get("success")]
    return {
        "episodes": total,
        "successes": successes,
        "win_rate": successes / total if total else 0.0,
        "wilson_95": [low, high],
        "failure_causes": dict(Counter(row["failure_cause"] for row in results)),
        "policy_errors": sum(int(row.get("policy_errors") or 0) for row in results),
        "median_success_steps": (
            statistics.median(successful_steps) if successful_steps else None
        ),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _print_progress(results: list[dict]) -> None:
    summary = _summary(results)
    causes = Counter(row["failure_cause"] for row in results if not row.get("success"))
    common = ", ".join(f"{name}={count}" for name, count in causes.most_common(4))
    low, high = summary["wilson_95"]
    print(
        f"[{summary['episodes']:4d}] Minetown {summary['successes']:4d}/"
        f"{summary['episodes']:4d} = {summary['win_rate']:.1%} "
        f"(IC95 {low:.1%}–{high:.1%})"
        + (f" | échecs: {common}" if common else ""),
        flush=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--workers", type=int, default=min(4, os.cpu_count() or 1))
    parser.add_argument("--max-steps", type=int, default=3000)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument(
        "--no-record",
        action="store_true",
        help="désactive la capture ttyrec pour les batchs exploratoires",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.episodes <= 0 or args.workers <= 0 or args.max_steps <= 0:
        raise SystemExit("episodes, workers and max-steps must be positive")

    run_dir = args.run_dir or Path("runs") / datetime.now(UTC).strftime(
        "%Y%m%d-%H%M%S"
    )
    run_dir = run_dir.resolve()
    (run_dir / "episodes").mkdir(parents=True, exist_ok=True)
    config = {
        "episodes": args.episodes,
        "workers": args.workers,
        "max_steps": args.max_steps,
        "record": not args.no_record,
        "counted": True,
        "wizard": False,
        "seeded": False,
        "character": CHARACTER,
        "nethack": "3.6.7",
        "started_at": datetime.now(UTC).isoformat(),
    }
    (run_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    print(f"Run compté: {run_dir}", flush=True)

    results: list[dict] = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                run_episode,
                episode,
                str(run_dir),
                args.max_steps,
                not args.no_record,
            ): episode
            for episode in range(args.episodes)
        }
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            with (run_dir / "results.jsonl").open("a", encoding="utf-8") as stream:
                stream.write(
                    json.dumps(result, sort_keys=True, default=_json_default) + "\n"
                )
            _print_progress(results)

    results.sort(key=lambda row: row["episode"])
    summary = _summary(results)
    (run_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if not any(row.get("error") for row in results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
