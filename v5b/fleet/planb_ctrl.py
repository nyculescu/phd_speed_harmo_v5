"""Plan B controllers (planb.md §3.4-§3.5): ASCH, the cell-agnostic two-regime gain scheduler, and MPC-F, the fitted-model MPC.
Both switch between whole tuned rules corridor-wide. Every member rule is called at every decision and only the chosen one's
action is applied, so stateful rules (RoadLevels, AdaptiveOn4a) stay current. Neither reads the speed limit, the event time, the
demand or the insertion queue (PR-15): ASCH reads zone speeds from the roadside bins; MPC-F also reads zone counts, the
accelerating-lane counts and the ramp queues (vehicles below 1 m/s on the ramp roads)."""
from __future__ import annotations

import numpy as np

from v5b.fleet import b_env as be

ZONES = (("1", "2"), ("3a", "3"), ("4a", "4", "5"))     # before merge 1, between the merges, after merge 2
RAMP_ROADS = (("r", "rj"), ("r2", "rj2"))
QUEUE_V = 1.0     # m/s, as measure.QUEUE_V
RULE_KEYS = ("cav_rule", "local_rule", "pattern", "adaptive_4a", "own_state", "road_levels", "zone_own_state")


def build_rule(env, ctrl: dict, fix: bool):
    """A member rule from its controller dict, exactly as plant_sweep.run_one builds the same key."""
    k = [x for x in RULE_KEYS if x in ctrl]
    if len(k) != 1:
        raise ValueError(f"a member rule needs exactly one of {RULE_KEYS}: {ctrl}")
    k, p = k[0], ctrl[k[0]]
    if k == "cav_rule":
        return be.CavRule(p, speed=ctrl.get("speed", 0))
    if k == "local_rule":
        return be.LocalRule(env, **p)
    if k == "pattern":
        return be.ZonePattern(p, fix=fix)
    if k == "adaptive_4a":
        return be.AdaptiveOn4a(env, **p)
    if k == "own_state":
        return be.OwnState(**p)
    if k == "road_levels":
        return be.RoadLevels(p)
    return be.ZoneOwnState(p["zones"])


def zone_speeds(bins: dict) -> list:
    """Mean of the occupied 200-m bins' mean speeds per zone (m/s); None for a zone with no vehicle."""
    out = []
    for roads in ZONES:
        v = [s for (road, _), s in bins.items() if road in roads]
        out.append(float(np.mean(v)) if v else None)
    return out


class Asch:
    """Steady rule while undisturbed; R_dist after any zone stays below theta for tau s; back after every zone stays at or above
    theta + h for tau s. Conditions are read at the decisions (every 5 s); a zone without vehicles counts as fast."""

    def __init__(self, env, steady, dist, theta_kmh: float, tau_s: float, h_kmh: float):
        self.env, self.rules = env, (steady, dist)
        self.theta, self.tau, self.h = theta_kmh / 3.6, tau_s, h_kmh / 3.6
        self.mode, self.since, self.log = 0, None, []

    def _cond(self) -> bool:
        z = zone_speeds(getattr(self.env, "bins", {}) or {})
        if self.mode == 0:
            return any(s is not None and s < self.theta for s in z)
        return all(s is None or s >= self.theta + self.h for s in z)

    def __call__(self, o: tuple) -> dict:
        t = self.env.sim.t
        if self._cond():
            self.since = t if self.since is None else self.since
            if t - self.since >= self.tau - 1e-9:
                self.mode, self.since = 1 - self.mode, None
                self.log.append((round(t), self.mode))
        else:
            self.since = None
        acts = [r(o) for r in self.rules]
        return acts[self.mode]


REF_SPEED = 100.0 / 3.6
W_CF = 10.0     # cost = delay vehicle-seconds + W_CF x close-following vehicle-seconds; chosen, not derived (planb.md §3.5)
HORIZON, REPICK, DATA_STEP = 300.0, 30.0, 5.0     # s: predicted and held horizon, re-pick interval, data-offset grid
N_FEAT = 10


def cost_now(env) -> float:
    """The running cost counter; its difference over an interval is that interval's cost."""
    ep = env.ep
    return ep["N"] - ep["dist_s"] / REF_SPEED + W_CF * (ep["E30"] + ep["out_E30"])


def features(env, ls) -> np.ndarray:
    """Roadside state: zone speeds and counts, accelerating-lane counts on 3a_0 and 4a_0, ramp queues (below 1 m/s)."""
    z = [REF_SPEED if s is None else s for s in zone_speeds(getattr(env, "bins", {}) or {})]
    n = [sum(ls.edge.getLastStepVehicleNumber(e) for e in roads) for roads in ZONES]
    acc = [ls.lane.getLastStepVehicleNumber(x) for x in ("3a_0", "4a_0")]
    q = [sum(ls.vehicle.getSpeed(v) < QUEUE_V for e in roads for v in ls.edge.getLastStepVehicleIDs(e)) for roads in RAMP_ROADS]
    return np.array(z + n + acc + q, np.float32)


def onehot_features(x: np.ndarray, a: int, n_act: int) -> np.ndarray:
    oh = np.zeros(n_act, np.float32)
    oh[a] = 1.0
    return np.concatenate([x.astype(np.float32), oh])


class Net:
    def __init__(self, n_in: int):
        import torch
        self.m = torch.nn.Sequential(torch.nn.Linear(n_in, 64), torch.nn.Tanh(), torch.nn.Linear(64, 64), torch.nn.Tanh(),
                                     torch.nn.Linear(64, 1))


class MpcF:
    """Port of claude/v5b-core:vsl_lab/jobs/mpcf.py (MPCF, gen_one) to per-CAV rules. Control mode ({"actions", "model"}): every
    30 s predict the 300-s cost of holding each action from the roadside state and apply the cheapest. Data mode ({"actions",
    "data": rng seed}): each action held for 300 s, chosen at random, after a random initial offset on a 5-s grid; each full
    hold logs (state at its start, action, cost over the hold). The model never sees the event, the limit or the demand."""

    def __init__(self, env, spec: dict, fix: bool):
        import libsumo as ls
        self.env, self.ls = env, ls
        self.rules = [build_rule(env, c, fix) for c in spec["actions"]]
        self.n_act, self.log, self.a, self.t_pick = len(self.rules), [], 0, None
        self.data = spec.get("data")
        if self.data is not None:
            self.rng = np.random.default_rng(int(self.data))
            self.a = int(self.rng.integers(0, self.n_act))
            self.next_hold = env.warm + DATA_STEP * int(self.rng.integers(0, int(HORIZON / DATA_STEP)))
            self.open = None
        else:
            import torch
            torch.set_num_threads(1)
            ck = torch.load(spec["model"], map_location="cpu", weights_only=False)
            if ck["n_act"] != self.n_act:
                raise ValueError("model and action list differ")
            self.mu, self.sd = np.asarray(ck["mu"], np.float32), np.asarray(ck["sd"], np.float32)
            self.net = Net(len(self.mu)).m
            self.net.load_state_dict(ck["state"])
            self.net.eval()
            self.torch = torch

    def _pick(self, t: float) -> None:
        x = features(self.env, self.ls)
        F = np.stack([onehot_features(x, a, self.n_act) for a in range(self.n_act)])
        with self.torch.no_grad():
            y = self.net(self.torch.from_numpy((F - self.mu) / self.sd)).numpy().reshape(-1)
        a = int(np.argmin(y))
        if a != self.a or not self.log:
            self.log.append((round(t), a))
        self.a, self.t_pick = a, t

    def _data(self, t: float) -> None:
        if t + 1e-9 < self.next_hold:
            return
        c = cost_now(self.env)
        if self.open is not None:
            x, a, c0 = self.open
            self.log.append({"x": x.tolist(), "a": a, "y": c - c0, "t": round(t - HORIZON)})
        if t + HORIZON <= self.env.t_end - DATA_STEP + 1e-9:     # the last decision is one step before the end, so a hold must end by then
            self.a = int(self.rng.integers(0, self.n_act))
            self.open = (features(self.env, self.ls), self.a, c)
            self.next_hold = t + HORIZON
        else:
            self.open, self.next_hold = None, float("inf")

    def __call__(self, o: tuple) -> dict:
        t = self.env.sim.t
        if self.data is not None:
            self._data(t)
        elif self.t_pick is None or t - self.t_pick >= REPICK - 1e-9:
            self._pick(t)
        acts = [r(o) for r in self.rules]
        return acts[self.a]
