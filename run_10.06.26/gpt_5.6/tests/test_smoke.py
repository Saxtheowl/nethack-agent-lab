from __future__ import annotations

from minetown_agent.env import NetHackMinetown
from minetown_agent.policy import MinetownPolicy


def test_policy_survives_a_short_real_game_without_protocol_errors():
    env = NetHackMinetown(max_episode_steps=250)
    policy = MinetownPolicy()
    try:
        obs, _ = env.reset()
        for _ in range(250):
            action = policy.act(obs)
            assert env.action_space.contains(action)
            obs, _, terminated, truncated, _ = env.step(action)
            if terminated or truncated:
                break
        assert policy.steps > 0
    finally:
        env.close()

