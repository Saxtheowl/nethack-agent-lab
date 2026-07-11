from __future__ import annotations

import numpy as np

from minetown_agent.env import NetHackMinetown


def _inventory(obs):
    descriptions = []
    for raw in obs["inv_strs"]:
        if not np.any(raw):
            break
        descriptions.append(bytes(raw).split(b"\0", 1)[0].decode())
    return descriptions


def test_counted_environment_hides_internal_signal_and_has_starting_kit():
    env = NetHackMinetown(max_episode_steps=10)
    try:
        obs, _ = env.reset()
        assert "internal" not in obs
        assert "program_state" not in obs
        inventory = _inventory(obs)
        assert any(
            "blessed greased +2 gray dragon scale mail (being worn)" in item
            for item in inventory
        )
        assert any("8 blessed +1 daggers" in item for item in inventory)
        assert any("12 blessed scrolls of magic mapping" in item for item in inventory)
        assert any("5 blessed potions of extra healing" in item for item in inventory)
        assert any("2 potions of holy water" in item for item in inventory)
        assert any("pick-axe" in item for item in inventory)
        assert int(obs["blstats"][16]) == -5
    finally:
        env.close()
