"""S0 trainer fixes (2026-10-04): --lr-decay reaches every algorithm; roadmap C1 convergence check. No SUMO.

Run: pytest -p no:cacheprovider tests/test_train_s0.py -v
"""
from __future__ import annotations

import argparse
import math
import pickle

import gymnasium as gym
import numpy as np
import pytest
import torch
from stable_baselines3.common.vec_env import DummyVecEnv

from vsl_lab.train import convergence as cv
from vsl_lab.train.train_sb3 import LinearDecay, build_model, n_actions_of

torch.set_num_threads(1)


class TinyEnv(gym.Env):
    """4 discrete actions, 3-d observation, episodes of 8 steps."""
    observation_space = gym.spaces.Box(-1.0, 1.0, (3,), np.float32)
    action_space = gym.spaces.Discrete(4)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.t = 0
        return np.zeros(3, np.float32), {}

    def step(self, action):
        self.t += 1
        return np.full(3, self.t / 8, np.float32), float(action == 1), self.t >= 8, False, {}


def args(algo: str) -> argparse.Namespace:
    return argparse.Namespace(algo=algo, net=[8], log_std_init=0.0, n_steps=16, batch=16, epochs=1, lr=3e-4,
                              gamma=0.99, gae=0.95, ent=0.0, seed=0)


def test_linear_decay_values_and_pickle():
    s = LinearDecay(3e-4, 100)
    assert s(1.0) == pytest.approx(3e-4)
    s.n = 50
    assert s(0.123) == pytest.approx(1.5e-4)      # ignores SB3's per-learn() progress
    s.n = 100
    assert s(1.0) == 0.0
    s.n = 150
    assert s(1.0) == 0.0
    assert pickle.loads(pickle.dumps(s))(1.0) == 0.0


@pytest.mark.parametrize("algo", ["ppo", "recurrentppo", "trpo"])
def test_decay_reaches_optimizer(algo):
    """The bug: RecurrentPPO and TRPO were built with the constant a.lr. After one update at n = half the run, the
    optimizer's learning rate must be half of lr0 for every algorithm."""
    a = args(algo)
    sched = LinearDecay(a.lr, 10)
    model = build_model(a, DummyVecEnv([TinyEnv]), sched)
    sched.n = 5
    model.learn(total_timesteps=16, reset_num_timesteps=False)
    assert [g["lr"] for g in model.policy.optimizer.param_groups] == pytest.approx([1.5e-4])


@pytest.mark.parametrize("algo", ["ppo", "recurrentppo", "trpo"])
def test_constant_lr_without_decay(algo):
    a = args(algo)
    model = build_model(a, DummyVecEnv([TinyEnv]), a.lr)
    model.learn(total_timesteps=16, reset_num_timesteps=False)
    assert [g["lr"] for g in model.policy.optimizer.param_groups] == pytest.approx([3e-4])


def test_n_actions_of():
    assert n_actions_of(gym.spaces.Discrete(4)) == 4
    assert n_actions_of(gym.spaces.MultiDiscrete([3, 2])) == [3, 2]
    assert n_actions_of(gym.spaces.Box(0, 1, (2,))) is None


# ---- C1 -------------------------------------------------------------------------------------------------------

def rows(val: dict, n_upd: int, ent: float, ev: float = 0.8, ent_prev: float | None = None, sign: float = 1.0):
    # val_return mirrors the metric with the maximisation orientation (C1a-c use the return since review fix #11)
    v = [{"update": str(u), "val_metric_value": str(m), "val_return": str(sign * m)} for u, m in val.items()]
    p = [{"update": str(u), "explained_var": str(ev),
          "entropy": str(-(ent if (ent_prev is None or u > n_upd - 100) else ent_prev))} for u in range(1, n_upd + 1)]
    return v, p


def test_c1_converged_minimisation():
    val = {0: 17.0, 100: 15.0, 200: 14.2, 300: 14.0, 325: 14.02, 350: 14.0, 375: 14.01, 400: 14.0, "final": 14.0}
    v, p = rows(val, 400, ent=0.8, sign=-1.0)
    r = cv.check(v, p, sign=-1.0, n_actions=4)
    assert r["converged"], r["pass"]
    assert r["best_score"] == -14.0


def test_c1_r6_like_failure():
    """R6 learner s3: best 13.92, final 15.41 (+10.7 %), entropy 0.22 nats with 4 actions -> not converged."""
    val = {0: 17.01, 1500: 14.5, 1600: 13.92, 1700: 15.0, 1800: 15.2, 1900: 15.3, 2000: 15.41, "final": 15.41}
    v, p = rows(val, 2000, ent=0.22, sign=-1.0)
    r = cv.check(v, p, sign=-1.0, n_actions=4)
    assert not r["converged"]
    assert r["pass"]["C1a"] is False and r["C1a_final_vs_best"] == pytest.approx((15.41 - 13.92) / 13.92)
    assert r["pass"]["C1f"] is False and r["entropy_floor"] == pytest.approx(0.25 * math.log(4))


def test_c1_slope_and_entropy_drift_fail():
    val = {0: 1.0, 300: 0.90, 325: 0.95, 350: 0.98, 375: 0.99, 400: 1.00, "final": 1.00}   # maximisation, rising
    v, p = rows(val, 400, ent=0.6, ent_prev=1.0)
    r = cv.check(v, p, sign=1.0, n_actions=4)
    assert r["pass"]["C1a"] is True
    assert r["pass"]["C1c"] is False        # still climbing
    assert r["pass"]["C1e"] is False        # entropy fell 40 % between windows
    assert not r["converged"]


def test_c1_low_ev_and_na_for_continuous():
    val = {0: 1.0, 300: 1.0, 350: 1.0, 400: 1.0, "final": 1.0}
    v, p = rows(val, 400, ent=0.5, ev=0.3)
    r = cv.check(v, p, sign=1.0, n_actions=None, action_dim=1)
    assert r["pass"]["C1d"] is False and r["pass"]["C1f"] is None and not r["converged"]


# ---- review fixes 2026-10-05 (#8-#11) ---------------------------------------------------------------------------

def test_final_row_not_double_counted():
    """#8: 'final' at update 400 repeats the periodic row at 400; it must count once in the window."""
    val = {0: 1.0, 310: 1.00, 340: 1.02, 370: 1.04, 400: 1.06, "final": 1.06}
    v, p = rows(val, 400, ent=0.8)
    r = cv.check(v, p, sign=1.0, n_actions=4)
    assert r["n_val_points"] == 4
    # slope of 0.02 per 30 updates -> 6.7 % of best per 100 updates -> FAIL either way, but computed on 4 points
    assert r["pass"]["C1c"] is False


def test_trpo_missing_entropy_blocks_converged():
    """#9: a run with no entropy logged (TRPO) must not be reported as converged for discrete actions."""
    val = {0: 17.0, 300: 14.0, 325: 14.0, 350: 14.0, 375: 14.0, 400: 14.0, "final": 14.0}
    v, p = rows(val, 400, ent=0.8, sign=-1.0)
    for r_ in p:
        r_["entropy"] = ""
    r = cv.check(v, p, sign=-1.0, n_actions=4)
    assert r["pass"]["C1e"] is False and r["pass"]["C1f"] is False and not r["converged"]


def test_continuous_entropy_absolute_tolerance():
    """#10: differential entropy -0.036 -> -0.124 (|delta| 0.088 nats, 1 dim) passes the 0.1-nat rule."""
    val = {0: 1.0, 300: 1.0, 350: 1.0, 400: 1.0, "final": 1.0}
    v, p = rows(val, 400, ent=-0.124, ent_prev=-0.036)
    r = cv.check(v, p, sign=1.0, n_actions=None, action_dim=1)
    assert r["pass"]["C1e"] is True
    v, p = rows(val, 400, ent=-0.5, ent_prev=-0.036)
    assert cv.check(v, p, sign=1.0, n_actions=None, action_dim=1)["pass"]["C1e"] is False


def test_c1_uses_return_not_metric():
    """#11: return converged while the selection metric drifts -> C1a on the return passes, metric_C1a reported."""
    val_m = {0: 1.0, 300: 1.0, 350: 1.0, 400: 0.8, "final": 0.8}
    v, p = rows(val_m, 400, ent=0.8)
    for r_ in v:
        r_["val_return"] = "1.0"
    r = cv.check(v, p, sign=1.0, n_actions=4)
    assert r["pass"]["C1a"] is True and r["metric_C1a"] == pytest.approx(0.2)


def test_action_dim_of():
    from vsl_lab.train.train_sb3 import action_dim_of
    assert action_dim_of(gym.spaces.Box(0, 1, (2, 3))) == 6 and action_dim_of(gym.spaces.Discrete(4)) is None


def test_trpo_entropy_logged_from_buffer():
    """#9: TRPO logs no entropy_loss; the trainer computes it from the rollout buffer (negative = -entropy)."""
    from stable_baselines3.common.vec_env import DummyVecEnv
    from vsl_lab.train.train_sb3 import _entropy_loss_from_buffer, build_model
    a = args("trpo")
    model = build_model(a, DummyVecEnv([TinyEnv]), a.lr)
    model.learn(total_timesteps=16, reset_num_timesteps=False)
    e = _entropy_loss_from_buffer(model)
    assert isinstance(e, float) and -math.log(4) - 1e-6 <= e < 0.0   # TinyEnv Discrete(4): entropy in (0, ln 4]
