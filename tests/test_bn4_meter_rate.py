"""R6+ vanilla-DRL actuator (docs/lab/t1_meter_gscan_protocol.md Addendum G): BN4Env(actuator="meter_rate").

venv314/bin/python -m pytest -p no:cacheprovider tests/test_bn4_meter_rate.py -q
Uses the T1 throw-away calibration seed 7,110,000 (roadmap §10), short episodes.
"""
import numpy as np
import pytest

pytestmark = pytest.mark.sumo


def _env(**kw):
    from vsl_lab.envs.bn4_env import BN4Env
    base = dict(inflow=(1600.0, 1600.0), eval_seeds=[7110000], warmup_s=40.0, control_s=90.0, decision_s=30.0,
                reward="tts", actuator="meter_rate", tag="test_meter_rate")
    base.update(kw)
    return BN4Env(**base)


def test_space_and_rate_hold():
    from vsl_lab.envs.bn4_env import RATE_GRID
    env = _env()
    try:
        assert env.action_space.n == len(RATE_GRID) == 14
        obs, _ = env.reset()
        assert obs.shape == env.observation_space.shape
        for k in (0, 13, 6):
            obs, r, done, trunc, info = env.step(k)
            # the rate set by the action survives FBMeter's 30-s update (K_F = 0: no feedback law)
            assert env.meter.K_F == 0.0
            assert env.meter.q == RATE_GRID[k]
            assert env.meter_active
            assert env.prev_action.argmax() == k and env.prev_action.sum() == 1.0
            assert np.isfinite(r)
        assert done
    finally:
        env.close()


def test_cycle_follows_rate():
    env = _env()
    try:
        env.reset()
        env.step(0)
        assert env.meter.cycle() == pytest.approx(2 * 4 * 3600 / 200.0)     # 144 s at 200 veh/h
        env.step(13)
        assert env.meter.cycle() == pytest.approx(max(6.0, 2 * 4 * 3600 / 4000.0))
    finally:
        env.close()


def test_restrictive_rate_holds_back_traffic():
    """T0-style binding check: 200 veh/h lets far fewer vehicles through node 3 than 4,000 veh/h."""
    out = {}
    for k in (0, 13):
        env = _env(control_s=300.0)
        try:
            env.reset()
            done, info = False, {}
            while not done:
                _, _, done, _, info = env.step(k)
            out[k] = info["episode_metrics"]["outflow_ctrl_vph"]
        finally:
            env.close()
    assert out[0] < 0.7 * out[13]
