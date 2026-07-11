"""Vérifications du protocole compté."""

import numpy as np
from nle import nethack

from minetown2.env import CHARACTER, NetHackMinetown
from minetown2.policy import RAW_TO_INDEX, MinetownPolicy


def test_env_hides_private_channels_and_starts_with_gdsm():
    env = NetHackMinetown(max_episode_steps=50)
    try:
        obs, _ = env.reset()
        assert "internal" not in obs
        assert "program_state" not in obs
        assert env.character == CHARACTER
        inventory = []
        for raw in obs["inv_strs"]:
            if not np.any(raw):
                break
            inventory.append(bytes(raw).split(b"\0", 1)[0].decode())
        assert any("gray dragon scale mail" in item for item in inventory), inventory
        gdsm = next(item for item in inventory if "gray dragon scale mail" in item)
        assert "+2" in gdsm and "greased" in gdsm, gdsm
    finally:
        env.close()


def test_policy_runs_some_steps():
    env = NetHackMinetown(max_episode_steps=300)
    policy = MinetownPolicy()
    try:
        obs, _ = env.reset()
        for _ in range(300):
            action = policy.act(obs)
            obs, _, terminated, truncated, _ = env.step(action)
            if terminated or truncated:
                break
        assert policy.steps > 0
    finally:
        env.close()


def test_keyboard_coverage():
    import string

    for char in string.ascii_letters + string.digits + "-\r":
        assert ord(char) in RAW_TO_INDEX
