"""Environnement compté Minetown.

La politique reçoit les observations ordinaires du NetHack Challenge.  Le bit
exact ``in_town`` vit dans l'observation privée ``internal`` de NLE et n'est
consommé que par :class:`NetHackMinetown` pour terminer l'épisode.  Il est
volontairement absent du dictionnaire retourné à la politique.
"""

from __future__ import annotations

import enum

from nle import nethack
from nle.env.tasks import NetHackChallenge


CHARACTER = "val-dwa-fem-law"
INTERNAL_IN_TOWN = 9


class NetHackMinetown(NetHackChallenge):
    """NetHack 3.6.7 complet, non-wizard, terminant au premier tile de la ville."""

    class StepStatus(enum.IntEnum):
        ABORTED = -1
        RUNNING = 0
        DEATH = 1
        TASK_SUCCESSFUL = 2

    def __init__(self, *args, character: str = CHARACTER, **kwargs):
        # NetHackChallenge force wizard=False et expose le clavier complet.
        # Baser la classe dessus rend les runs comptés incapables d'activer
        # silencieusement le mode wizard ou des seeds déterministes.
        if "options" not in kwargs:
            kwargs["options"] = list(nethack.NETHACKOPTIONS)
        super().__init__(*args, character=character, **kwargs)

    def _is_episode_end(self, observation):
        internal = observation[self._internal_index]
        if internal[INTERNAL_IN_TOWN]:
            return self.StepStatus.TASK_SUCCESSFUL
        return self.StepStatus.RUNNING

    def _reward_fn(self, last_observation, action, observation, end_status):
        del last_observation, action, observation
        return float(end_status == self.StepStatus.TASK_SUCCESSFUL)
