"""Shared, model-agnostic decision plumbing for the Jev experiments.

The NetHack policies only depend on ``Decider.choose``.  OpenRouter/Jev is one
implementation; tests and future models can supply another implementation
without changing the game harness.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional


DEFAULT_MODEL = "typesafe/jev-1.13"
DEFAULT_URL = "https://openrouter.ai/api/alpha/decisions"
INPUT_USD_PER_TOKEN = 0.042 / 1_000_000


class DecisionError(RuntimeError):
    pass


@dataclass
class Decision:
    choice: str
    confidence: Optional[float]
    probabilities: Dict[str, float]
    latency_ms: int
    usage: Dict[str, Any]
    cost_usd: Optional[float]
    model: str
    request_id: Optional[str] = None


def _cost(usage: Mapping[str, Any]) -> Optional[float]:
    for key in ("cost", "total_cost", "cost_usd"):
        value = usage.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    tokens = usage.get("input_tokens", usage.get("prompt_tokens"))
    try:
        return round(float(tokens) * INPUT_USD_PER_TOKEN, 10)
    except (TypeError, ValueError):
        return None


class OpenRouterDecider:
    """Minimal HTTP client for OpenRouter's Decisions endpoint."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL,
                 url: str = DEFAULT_URL, timeout: float = 30.0,
                 retries: int = 2, offline: bool = False):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.model = model
        self.url = url
        self.timeout = timeout
        self.retries = retries
        self.offline = offline
        if not self.api_key and not offline:
            raise DecisionError("OPENROUTER_API_KEY is required (or use "
                                "--jev-offline for harness smoke tests)")

    def choose(self, state: Any, choices: Mapping[str, str],
               instructions: str) -> Decision:
        if not choices:
            raise DecisionError("Jev received no choices")
        if self.offline:
            key = next(iter(choices))
            probs = {k: (1.0 if k == key else 0.0) for k in choices}
            return Decision(key, 1.0, probs, 0,
                            {"input_tokens": 0, "offline": True}, 0.0,
                            "offline-first-choice")
        payload = {
            "model": self.model,
            "state": state,
            "questions": {
                "next_action": {
                    "type": "choice",
                    "instructions": instructions,
                    "criteria": dict(choices),
                }
            },
        }
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/bothack/jev-experiment",
            "X-Title": "BotHack Jev experiment",
        }
        started = time.monotonic()
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(self.url, data=body,
                                             headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout) as res:
                    raw = json.loads(res.read().decode("utf-8"))
                    request_id = res.headers.get("x-request-id")
                break
            except (urllib.error.URLError, urllib.error.HTTPError,
                    TimeoutError, ValueError) as exc:
                last_error = exc
                if attempt == self.retries:
                    raise DecisionError("OpenRouter decision failed: %s" % exc)
                time.sleep(min(0.25 * (2 ** attempt), 2.0))
        else:  # pragma: no cover
            raise DecisionError(str(last_error))
        latency_ms = round((time.monotonic() - started) * 1000)
        data = raw.get("data", raw)
        answer = (data.get("answers") or {}).get("next_action")
        if not isinstance(answer, dict) or answer.get("choice") not in choices:
            raise DecisionError("invalid Jev response: %s" %
                                json.dumps(raw)[:1000])
        usage = data.get("usage") or raw.get("usage") or {}
        return Decision(
            choice=answer["choice"],
            confidence=_float_or_none(answer.get("confidence")),
            probabilities={str(k): float(v) for k, v in
                           (answer.get("probabilities") or {}).items()},
            latency_ms=latency_ms,
            usage=dict(usage),
            cost_usd=_cost(usage),
            model=str(data.get("model") or raw.get("model") or self.model),
            request_id=str(data.get("id") or raw.get("id") or request_id)
            if (data.get("id") or raw.get("id") or request_id) else None,
        )


def _float_or_none(value: Any) -> Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


class DecisionJournal:
    """Append-only decision/outcome log plus aggregate counters."""

    def __init__(self, out_dir: str, mode: str):
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        self.path = Path(out_dir) / "jev_decisions.jsonl"
        self.file = self.path.open("w", encoding="utf-8")
        self.mode = mode
        self.started = time.time()
        self.calls = 0
        self.errors = 0
        self.input_tokens = 0
        self.output_tokens = 0
        self.cost_usd = 0.0
        self.latency_ms = 0
        self.pending = None
        self.stop_reason = None

    def request_stop(self, reason: str) -> None:
        """Ask the game supervisor to stop at the next engine request."""
        if self.stop_reason is None:
            self.stop_reason = str(reason)
            self._write({"event": "guard_stop", "mode": self.mode,
                         "reason": self.stop_reason, "calls": self.calls})

    def continuation(self, state: Mapping[str, Any], intention: str,
                     step: int) -> None:
        """Record reuse of a previously paid high-level decision."""
        self.observe(state)
        self._write({"event": "intent_continuation", "mode": self.mode,
                     "turn": state.get("turn"), "intention": intention,
                     "step": step, "context": state_snapshot(state)})

    def decide(self, decider: OpenRouterDecider, state: Mapping[str, Any],
               candidates: Mapping[str, Any], instructions: str,
               executed: bool, bothack_action: Optional[Mapping[str, Any]] = None,
               trigger: Optional[Iterable[str]] = None,
               track_outcome: bool = False) -> str:
        self.observe(state)
        descriptions = {k: str(v["description"]) for k, v in candidates.items()}
        decision_id = "%s-%06d" % (self.mode.lower(), self.calls + 1)
        base = {
            "event": "decision", "id": decision_id, "mode": self.mode,
            "wall_s": round(time.time() - self.started, 3),
            "turn": state.get("turn"), "context": state,
            "choices": descriptions, "executed": executed,
        }
        if bothack_action is not None:
            base["bothack_action"] = json_safe(bothack_action)
        if trigger:
            base["trigger"] = list(trigger)
        try:
            answer = decider.choose(state, descriptions, instructions)
        except Exception as exc:
            self.errors += 1
            base.update(error=repr(exc), chosen=None)
            self._write(base)
            raise
        self.calls += 1
        self.latency_ms += answer.latency_ms
        self.input_tokens += int(answer.usage.get(
            "input_tokens", answer.usage.get("prompt_tokens", 0)) or 0)
        self.output_tokens += int(answer.usage.get(
            "output_tokens", answer.usage.get("completion_tokens", 0)) or 0)
        self.cost_usd += answer.cost_usd or 0.0
        base.update(chosen=answer.choice, confidence=answer.confidence,
                    probabilities=answer.probabilities,
                    latency_ms=answer.latency_ms, usage=answer.usage,
                    cost_usd=answer.cost_usd, model=answer.model,
                    request_id=answer.request_id)
        self._write(base)
        if executed or track_outcome:
            self.pending = (decision_id, state_snapshot(state))
        return answer.choice

    def observe(self, state: Mapping[str, Any]) -> None:
        if self.pending is None:
            return
        decision_id, before = self.pending
        after = state_snapshot(state)
        self._write({"event": "outcome", "decision_id": decision_id,
                     "before": before, "after": after,
                     "turn_delta": (after.get("turn") or 0) -
                                   (before.get("turn") or 0),
                     "hp_delta": _delta(after.get("hp"), before.get("hp")),
                     "messages": state.get("messages", [])})
        self.pending = None

    def error(self, state: Mapping[str, Any], exc: Exception,
              fallback: Optional[str]) -> None:
        self.errors += 1
        self._write({"event": "error", "mode": self.mode,
                     "turn": state.get("turn"), "error": repr(exc),
                     "fallback": fallback})

    def summary(self) -> Dict[str, Any]:
        return {
            "calls": self.calls, "errors": self.errors,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": round(self.cost_usd, 8),
            "latency_ms": self.latency_ms,
            "mean_latency_ms": round(self.latency_ms / self.calls, 1)
            if self.calls else None,
        }

    def close(self, final_state: Optional[Mapping[str, Any]] = None) -> None:
        if final_state:
            self.observe(final_state)
        self._write({"event": "summary", **self.summary()})
        self.file.close()

    def _write(self, record: Mapping[str, Any]) -> None:
        self.file.write(json.dumps(json_safe(record), ensure_ascii=False) + "\n")
        self.file.flush()


def _delta(a: Any, b: Any) -> Optional[float]:
    try:
        return float(a) - float(b)
    except (TypeError, ValueError):
        return None


def state_snapshot(state: Mapping[str, Any]) -> Dict[str, Any]:
    player = state.get("player") or {}
    return {"turn": state.get("turn"), "level": state.get("level"),
            "branch": state.get("branch"), "position": state.get("position"),
            "hp": player.get("hp"), "xl": player.get("xplvl")}


def json_safe(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        return repr(value)[:300]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(k): json_safe(v, depth + 1) for k, v in value.items()
                if str(k) not in ("handler", "handlers", "rng")
                and not callable(v)}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [json_safe(v, depth + 1) for v in list(value)[:100]]
    if hasattr(value, "x") and hasattr(value, "y"):
        return {"x": value.x, "y": value.y}
    return repr(value)[:300]


def action_summary(action: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not action:
        return {"type": None}
    result = {"type": action.get("type")}
    for key in ("dir", "slot", "pos", "reason"):
        if action.get(key) is not None:
            result[key] = json_safe(action.get(key))
    return result
