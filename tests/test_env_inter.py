# tests/test_env_inter.py
"""
Integration tests for TrafficEnv (core/env_interact.py) in dry-run mode.

Dry-run mode
------------
Passing ``sumo_cfg_path=None`` to TrafficEnv disables all SUMO interaction.
No simulation process is started, no network or detector files are read, and
all traffic metrics remain at their zero defaults throughout every episode.
This makes the suite runnable without a SUMO installation and without any
generated scenario files.

What is exercised
-----------------
The tests exercise the full Python call stack from the gym API surface down
through the SAR components:

  gym API  →  TrafficEnv  →  StateRepresentation (m43_state_v0)
                          →  ActionStrategy      (m43_action_v0)
                          →  RewardFunction      (m43_reward_v0)

Concretely:

  TestSpaces   — gym space objects are correctly configured before any episode
                 starts (shape, dtype, bounds, number of discrete actions).

  TestReset    — reset() returns a valid (obs, info) pair; obs is within the
                 declared [0, 1] bounds; calling reset() twice does not corrupt
                 state; resetting mid-episode restores the step counter so the
                 next step is not immediately terminal.

  TestStep     — step() returns a well-formed 5-tuple (obs, reward, terminated,
                 truncated, info); reward is a Python float; terminated is a
                 bool; truncated is always False (no time-limit truncation in
                 this env); info carries the three reward sub-components
                 (variance, throughput, smoothness); all 7 discrete actions are
                 accepted without raising.

  TestEpisode  — a full episode terminates in exactly the expected number of
                 steps (episode_duration // aggregation_time = 300 // 30 = 10);
                 rewards stay within a sanity range (-5, 5) at every step;
                 three back-to-back episodes each complete cleanly, confirming
                 that internal state (frame buffer, step counter, action index)
                 is properly reset between episodes.

What is NOT tested here
-----------------------
  - Any SUMO process or TraCI interaction.
  - Real detector readings or vehicle control (CAV slowDown).
  - Scenario file generation or network/detector XML parsing.
  - The training or evaluation pipelines (training/, evaluation/).
  - demand_profiles.py, rou_writer.py, scenario_generator.py.

Run
---
    # from the phd_speed_harmo_v5/ root:
    python -m pytest tests/test_env_inter.py -v
"""
from __future__ import annotations

import numpy as np
import pytest

from sar_components.discovery import discover_components
from core import (
    TrafficEnv,
    create_action_strategy,
    create_reward_function,
    create_state_representation,
)

discover_components()

# ---------------------------------------------------------------------------
# Shared configuration
# ---------------------------------------------------------------------------

_SAR_CONFIG = {
    "max_flow_vph": 4000.0,
    "max_tts_s": 5000.0,
    "reward_weights_v9": {"w_v": 0.50, "w_q": 0.35, "w_a": 0.15},
    "ref_flow_vph": 2520.0,
}

_EPISODE_DURATION = 300    # seconds
_AGGREGATION_TIME = 30     # seconds → 10 steps per episode
_EXPECTED_STEPS = _EPISODE_DURATION // _AGGREGATION_TIME


def _make_env() -> TrafficEnv:
    """Create a fresh TrafficEnv in dry-run mode."""
    return TrafficEnv(
        sumo_cfg_path=None,
        state_repr=create_state_representation("m43_state_v0", _SAR_CONFIG),
        action_strat=create_action_strategy("m43_action_v0", {}),
        reward_func=create_reward_function("m43_reward_v0", _SAR_CONFIG),
        episode_duration=_EPISODE_DURATION,
        cav_percent=0.5,
        aggregation_time=_AGGREGATION_TIME,
    )


@pytest.fixture
def env():
    e = _make_env()
    yield e
    e.close()


# ---------------------------------------------------------------------------
# Spaces
# ---------------------------------------------------------------------------

class TestSpaces:
    def test_obs_shape(self, env):
        assert env.observation_space.shape == (105,)

    def test_obs_dtype(self, env):
        assert env.observation_space.dtype == np.float32

    def test_obs_bounds(self, env):
        assert env.observation_space.low.min() == pytest.approx(0.0)
        assert env.observation_space.high.max() == pytest.approx(1.0)

    def test_action_space_size(self, env):
        assert env.action_space.n == 7


# ---------------------------------------------------------------------------
# reset()
# ---------------------------------------------------------------------------

class TestReset:
    def test_obs_shape(self, env):
        obs, _ = env.reset()
        assert obs.shape == (105,)

    def test_obs_dtype(self, env):
        obs, _ = env.reset()
        assert obs.dtype == np.float32

    def test_obs_in_unit_range(self, env):
        obs, _ = env.reset()
        assert obs.min() >= 0.0
        assert obs.max() <= 1.0

    def test_info_is_dict(self, env):
        _, info = env.reset()
        assert isinstance(info, dict)

    def test_double_reset(self, env):
        """Calling reset() twice should not raise."""
        env.reset()
        obs, _ = env.reset()
        assert obs.shape == (105,)

    def test_reset_restarts_episode(self, env):
        env.reset()
        for _ in range(5):
            env.step(6)
        env.reset()
        _, _, terminated, _, _ = env.step(6)
        assert not terminated


# ---------------------------------------------------------------------------
# step()
# ---------------------------------------------------------------------------

class TestStep:
    def test_obs_shape(self, env):
        env.reset()
        obs, _, _, _, _ = env.step(6)
        assert obs.shape == (105,)

    def test_obs_dtype(self, env):
        env.reset()
        obs, _, _, _, _ = env.step(6)
        assert obs.dtype == np.float32

    def test_reward_is_float(self, env):
        env.reset()
        _, reward, _, _, _ = env.step(6)
        assert isinstance(reward, float)

    def test_terminated_is_bool(self, env):
        env.reset()
        _, _, terminated, _, _ = env.step(6)
        assert isinstance(terminated, bool)

    def test_truncated_always_false(self, env):
        env.reset()
        _, _, _, truncated, _ = env.step(6)
        assert truncated is False

    def test_info_has_reward_components(self, env):
        env.reset()
        _, _, _, _, info = env.step(6)
        assert "reward_components" in info
        assert "variance" in info["reward_components"]
        assert "throughput" in info["reward_components"]
        assert "smoothness" in info["reward_components"]

    def test_all_actions_accepted(self, env):
        for action in range(7):
            env.reset()
            obs, _, _, _, _ = env.step(action)
            assert obs.shape == (105,)

    def test_step_before_reset_raises_or_returns(self, env):
        """step() before reset() should not hard-crash; behaviour is unspecified."""
        try:
            env.step(6)
        except Exception:
            pass  # any exception is fine; what matters is no segfault


# ---------------------------------------------------------------------------
# Episode
# ---------------------------------------------------------------------------

class TestEpisode:
    def test_terminates_after_expected_steps(self, env):
        env.reset()
        steps = 0
        terminated = False
        while not terminated:
            _, _, terminated, _, _ = env.step(6)
            steps += 1
            assert steps <= _EXPECTED_STEPS + 1, "Episode did not terminate in time"
        assert steps == _EXPECTED_STEPS

    def test_reward_within_loose_bounds(self, env):
        """Reward should stay in a reasonable range (no runaway values)."""
        env.reset()
        for _ in range(_EXPECTED_STEPS):
            _, reward, terminated, _, _ = env.step(3)
            assert -5.0 < reward < 5.0
            if terminated:
                break

    def test_three_consecutive_episodes(self, env):
        for ep in range(3):
            obs, _ = env.reset()
            assert obs.shape == (105,), f"Episode {ep}: bad obs shape after reset"
            for _ in range(_EXPECTED_STEPS):
                obs, _, terminated, _, _ = env.step(6)
                if terminated:
                    break
            assert terminated, f"Episode {ep} did not terminate"
