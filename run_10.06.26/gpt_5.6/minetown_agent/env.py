"""Counted Minetown environment.

The policy receives the ordinary NetHack Challenge observations.  The exact
``in_town`` bit lives in NLE's private ``internal`` observation and is consumed
only by :class:`NetHackMinetown` to end an episode.  It is deliberately absent
from the dictionary returned to the policy.
"""

from __future__ import annotations

import enum

from nle import nethack
from nle.env.tasks import NetHackChallenge


CHARACTER = "val-dwa-fem-law"
INTERNAL_IN_TOWN = 9


class NetHackMinetown(NetHackChallenge):
    """Full, non-wizard NetHack 3.6.7 ending on the first Minetown tile."""

    class StepStatus(enum.IntEnum):
        ABORTED = -1
        RUNNING = 0
        DEATH = 1
        TASK_SUCCESSFUL = 2

    def __init__(self, *args, character: str = CHARACTER, **kwargs):
        # NetHackChallenge itself fixes wizard=False and exposes the full
        # keyboard.  Keeping this class based on Challenge makes counted runs
        # incapable of silently enabling wizard mode or deterministic seeds.
        if "options" not in kwargs:
            kwargs["options"] = [*nethack.NETHACKOPTIONS, "pettype:none"]
        super().__init__(*args, character=character, **kwargs)

    def _is_episode_end(self, observation):
        internal = observation[self._internal_index]
        if internal[INTERNAL_IN_TOWN]:
            return self.StepStatus.TASK_SUCCESSFUL
        return self.StepStatus.RUNNING

    def _reward_fn(self, last_observation, action, observation, end_status):
        del last_observation, action, observation
        return float(end_status == self.StepStatus.TASK_SUCCESSFUL)
