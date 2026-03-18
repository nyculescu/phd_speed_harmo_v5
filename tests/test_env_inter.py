# tests/test_env_inter.py
"""
Dry-run integration tests for the r44 v1 SAR components on ramps_v1.

These tests use dry-run mode (sumo_cfg_path=None) — no SUMO installation
needed. All metrics stay at zero; the tests verify observation shape,
action space, reward structure, and episode termination.

Run:
    pytest tests/test_env_inter.py -v
"""
from __future__ import annotations

import math

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
# Config
# ---------------------------------------------------------------------------

_SAR_CONFIG = {
    "max_flow_vph": 8000.0,
    "max_ramp_flow_vph": 2000.0,
    "ref_flow_vph": 6000.0,
    "speed_floor_kph": 50.0,
    "harmo_spatial_blend": 0.5,
    "reward_weights": {"w_h": 0.55, "w_q": 0.30, "w_a": 0.15},
}

_EPISODE_DURATION = 300   # seconds → 10 steps at 30s
_AGGREGATION_TIME = 30

_OBS_DIM = 56    # 18 features × 3 frames + 2 action features
_ACTION_DIM = 2


def _make_env() -> TrafficEnv:
    state_repr = create_state_representation("r44_state_v1", _SAR_CONFIG)
    action_strat = create_action_strategy("r44_action_v1", {})
    reward_func = create_reward_function("r44_reward_v2", _SAR_CONFIG)

    return TrafficEnv(
        sumo_cfg_path=None,  # dry-run
        state_repr=state_repr,
        action_strat=action_strat,
        reward_func=reward_func,
        episode_duration=_EPISODE_DURATION,
        cav_percent=0.5,
        aggregation_time=_AGGREGATION_TIME,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSpaces:
    def test_observation_space(self):
        env = _make_env()
        assert env.observation_space.shape == (_OBS_DIM,)
        assert env.observation_space.dtype == np.float32

    def test_action_space(self):
        env = _make_env()
        assert env.action_space.shape == (_ACTION_DIM,)
        assert env.action_space.dtype == np.float32
        np.testing.assert_array_equal(env.action_space.low, [60.0, 40.0])
        np.testing.assert_array_equal(env.action_space.high, [120.0, 90.0])


class TestReset:
    def test_obs_shape_and_dtype(self):
        env = _make_env()
        obs, info = env.reset()
        assert obs.shape == (_OBS_DIM,), f"obs shape: {obs.shape}"
        assert obs.dtype == np.float32
        assert obs.min() >= 0.0
        assert obs.max() <= 1.0
        assert isinstance(info, dict)

    def test_double_reset(self):
        env = _make_env()
        obs1, _ = env.reset()
        obs2, _ = env.reset()
        assert obs1.shape == obs2.shape


class TestStep:
    def test_basic_step(self):
        env = _make_env()
        env.reset()
        action = np.array([90.0, 60.0], dtype=np.float32)
        obs, reward, terminated, truncated, info = env.step(action)

        assert obs.shape == (_OBS_DIM,)
        assert obs.dtype == np.float32
        assert obs.min() >= 0.0
        assert obs.max() <= 1.0
        assert isinstance(reward, float)
        assert math.isfinite(reward)
        assert isinstance(terminated, bool)
        assert truncated is False
        assert "reward_components" in info
        for key in ("harmonization", "spatial", "temporal", "throughput", "smoothness"):
            assert key in info["reward_components"], f"missing component '{key}'"

    def test_all_corners(self):
        """Test actions at all four corners of the Box."""
        env = _make_env()
        env.reset()
        corners = [
            [60.0, 40.0],   # min, min
            [120.0, 90.0],  # max, max
            [60.0, 90.0],   # min, max
            [120.0, 40.0],  # max, min
        ]
        for corner in corners:
            obs, reward, _, _, _ = env.step(np.array(corner, dtype=np.float32))
            assert obs.shape == (_OBS_DIM,)
            assert math.isfinite(reward)


class TestEpisode:
    def test_full_episode(self):
        env = _make_env()
        obs, _ = env.reset()
        expected_steps = _EPISODE_DURATION // _AGGREGATION_TIME
        steps = 0
        terminated = False

        while not terminated:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            steps += 1
            assert obs.shape == (_OBS_DIM,)
            assert math.isfinite(reward)
            assert truncated is False
            assert steps <= expected_steps

        assert steps == expected_steps
        assert terminated is True

    def test_three_episodes(self):
        """Back-to-back episodes terminate correctly."""
        env = _make_env()
        for _ in range(3):
            obs, _ = env.reset()
            terminated = False
            while not terminated:
                obs, _, terminated, _, _ = env.step(env.action_space.sample())
            assert terminated is True
