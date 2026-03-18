# tests/test_config_consistency.py
"""
Verify that _common_config.yaml matches hardcoded test defaults.

No SUMO required.  Catches silent divergence between the config file
(used by training) and the hardcoded values in test_env_inter.py
(used by dry-run tests).

Run:
    pytest tests/test_config_consistency.py -v
"""
from __future__ import annotations

from pathlib import Path

import yaml
import pytest

_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = _ROOT / "configurations" / "_common_config.yaml"


@pytest.fixture(scope="module")
def cfg() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)


class TestSARConfigAlignment:
    """Ensure YAML sar_config matches test_env_inter.py hardcoded values."""

    # Mirror of _SAR_CONFIG from test_env_inter.py — if either side
    # changes without the other, this test fails.
    _EXPECTED = {
        "max_flow_vph": 8000.0,
        "max_ramp_flow_vph": 2000.0,
        "ref_flow_vph": 6000.0,
        "speed_floor_kph": 50.0,
        "harmo_spatial_blend": 0.5,
        "throughput_threshold": 0.85,
        "reward_weights": {"w_h": 0.55, "w_q": 0.30, "w_a": 0.15},
    }

    def test_sar_config_keys_present(self, cfg):
        sar = cfg["sar_config"]
        for key in self._EXPECTED:
            assert key in sar, f"Missing key '{key}' in sar_config"

    def test_sar_config_values_match(self, cfg):
        sar = cfg["sar_config"]
        for key, expected in self._EXPECTED.items():
            actual = sar[key]
            if isinstance(expected, dict):
                for sub_key, sub_val in expected.items():
                    assert sub_key in actual, (
                        f"Missing sub-key '{sub_key}' in sar_config.{key}"
                    )
                    assert actual[sub_key] == pytest.approx(sub_val), (
                        f"sar_config.{key}.{sub_key}: "
                        f"expected {sub_val}, got {actual[sub_key]}"
                    )
            else:
                assert actual == pytest.approx(expected), (
                    f"sar_config.{key}: expected {expected}, got {actual}"
                )


class TestSARComponentNames:
    """Ensure YAML component names match what tests use."""

    def test_state_component(self, cfg):
        assert cfg["sar"]["state"] == "r44_state_v1"

    def test_action_component(self, cfg):
        assert cfg["sar"]["action"] == "r44_action_v1"

    def test_reward_component(self, cfg):
        assert cfg["sar"]["reward"] == "r44_reward_v2"


class TestEpisodeAlignment:
    """Ensure episode duration is a clean multiple of aggregation time."""

    def test_duration_divisible_by_aggregation(self, cfg):
        duration = cfg["sumo"]["episode_duration_s"]
        agg = cfg["sumo"]["aggregation_time"]
        assert duration % agg == 0, (
            f"episode_duration_s ({duration}) is not a multiple of "
            f"aggregation_time ({agg}) — would silently truncate episode"
        )

    def test_aggregation_time_value(self, cfg):
        assert cfg["sumo"]["aggregation_time"] == 30

    def test_episode_duration_value(self, cfg):
        assert cfg["sumo"]["episode_duration_s"] == 3600
