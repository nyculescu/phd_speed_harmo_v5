"""RING22 gymnasium environment (Track 3): one AV among 21 noisy IDM humans on a ring.

mode="hybrid": every `decision_s` the policy sets FollowerStopper's command speed U in [0, 10] m/s; the
               field-tested FollowerStopper (Stern et al. 2018) drives the AV every 0.1 s (the shield).
mode="direct": every `decision_s` the policy sets the AV acceleration in [-1, 1] m/s^2 (Flow ring style).
Observation (local, CIRCLES-like + memory): [v_av, v_lead - v_av, gap, 38 s mean AV speed, previous action]
with fixed scaling. Reward: mean speed of all vehicles over the decision interval / 5 - 0.1 |a_AV| (Flow's
Eq. 2 form; mean speed is the primary metric, on a closed ring it equals throughput * L / N).
Ring length is drawn per episode from L_range (the hidden density condition); each reset is a fresh SUMO.
"""
from __future__ import annotations

import os
from collections import deque

import gymnasium as gym
import numpy as np

from vsl_lab.config import E_CORES, RUNS_ROOT
from vsl_lab.plants import ring as R


class RingEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, mode: str = "hybrid", L_range=(220.0, 270.0), decision_s: float = 1.0, warm_s: float = 75.0,
                 control_s: float = 300.0, noise: str = "sqrt_dt", seed_pool=(7230000, 7239999), eval_seeds=None,
                 eval_L=None, reward: str = "speed", alpha: float = 0.1, tag: str = "train", pin_ecores: bool = True):
        super().__init__()
        if pin_ecores:
            try:
                os.sched_setaffinity(0, set(E_CORES))
            except OSError:
                pass
        self.mode, self.L_range, self.decision_s = mode, L_range, decision_s
        self.warm_s, self.control_s, self.noise = warm_s, control_s, noise
        self.seed_pool = seed_pool
        self.eval_seeds = list(eval_seeds) if eval_seeds is not None else None
        self.eval_L = eval_L
        self._eval_i = 0
        self.reward_kind, self.alpha, self.tag = reward, alpha, tag
        self.observation_space = gym.spaces.Box(-5.0, 5.0, shape=(5,), dtype=np.float32)
        self.action_space = gym.spaces.Box(-1.0, 1.0, shape=(1,), dtype=np.float32)
        self.plant = None
        self.n_sub = int(round(decision_s / R.DT))
        self.hist = deque(maxlen=int(round(38.0 / R.DT)))
        self.prev = 0.0
        self.fs = R.FollowerStopper(5.0)

    def _obs(self, st) -> np.ndarray:
        v, vl, gap = st[R.AV_ID]
        m38 = sum(self.hist) / len(self.hist) if self.hist else v
        return np.array([v / 10.0, (vl - v) / 10.0, min(gap, 60.0) / 30.0, m38 / 10.0, self.prev],
                        dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if self.plant is not None:
            self.plant.close()
            self.plant = None
        if self.eval_seeds is not None:
            ep_seed = self.eval_seeds[self._eval_i % len(self.eval_seeds)]
            L = self.eval_L if self.eval_L is not None else self.L_range[0]
            self._eval_i += 1
        else:
            ep_seed = int(self.np_random.integers(self.seed_pool[0], self.seed_pool[1] + 1))
            L = float(self.np_random.uniform(*self.L_range))
            L = round(L)                        # integer lengths keep the net cache small
        run_dir = RUNS_ROOT / "t3" / "envs" / self.tag / f"pid{os.getpid()}"
        self.plant = R.RingPlant(L, ep_seed, noise=self.noise, run_dir=run_dir)
        self.plant.start()
        self.hist.clear()
        self.prev = 0.0
        self.metrics = {"speeds": [], "stds": [], "mins": [], "av": [], "gaps": [], "seed": ep_seed, "L": self.plant.L,
                        "ret": 0.0}
        while self.plant.t < self.warm_s - 1e-9:   # warm-up: the AV drives as a noisy human
            self.plant.step_all(None)
        st = self.plant.state()
        self.hist.append(st[R.AV_ID][0])
        self.t_ctrl0 = self.plant.t
        return self._obs(st), {}

    def step(self, action):
        a = float(np.clip(np.asarray(action, dtype=np.float32).reshape(-1)[0], -1.0, 1.0))
        if self.mode == "hybrid":
            self.fs.U = 5.0 * (a + 1.0)          # [0, 10] m/s
        speeds, accs = [], []
        st = None
        for _ in range(self.n_sub):
            st = self.plant.state()
            v, vl, gap = st[R.AV_ID]
            if self.mode == "hybrid":
                acc = float(np.clip((self.fs.v_cmd(v, vl, gap) - v) / R.DT, -3.0, 1.5))
            else:
                acc = a                            # [-1, 1] m/s^2
            self.plant.step_all(acc, st)
            sp = np.array([st[x][0] for x in self.plant.ids])
            speeds.append(sp.mean())
            accs.append(abs(acc))
            self.hist.append(v)
            self.metrics["speeds"].append(sp.mean())
            self.metrics["stds"].append(sp.std())
            self.metrics["mins"].append(sp.min())
            self.metrics["av"].append(v)
            self.metrics["gaps"].append(min(st[x][2] for x in self.plant.ids))
        r = float(np.mean(speeds)) / 5.0 - self.alpha * float(np.mean(accs))
        self.prev = a
        self.metrics["ret"] += r
        st = self.plant.state()
        obs = self._obs(st)
        if not np.all(np.isfinite(obs)):
            obs = np.nan_to_num(obs)
            r = 0.0
        done = self.plant.t >= self.t_ctrl0 + self.control_s - 1e-9
        info = {}
        if done:
            h = self.plant.close()
            self.plant = None
            m = self.metrics
            info["episode_metrics"] = {
                "mean_speed": float(np.mean(m["speeds"])), "mean_across_std": float(np.mean(m["stds"])),
                "stop_share": float(np.mean(np.array(m["mins"]) < 1.0)), "av_mean_speed": float(np.mean(m["av"])),
                "min_gap": float(np.min(m["gaps"])), "L": m["L"], "seed": m["seed"], "return": m["ret"]}
            info["health"] = h["status"]
            info["health_codes"] = [i[1] for i in h["issues"]]
        return obs, r, bool(done), False, info

    def close(self):
        if self.plant is not None:
            try:
                self.plant.close()
            except Exception:
                pass
            self.plant = None
