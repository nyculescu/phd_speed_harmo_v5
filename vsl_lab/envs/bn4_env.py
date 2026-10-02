"""BN4 gymnasium environment: Lagrangian AV speed-cap control (Vinitsky et al. 2018 reproduction, v1 SAR).

Observation (S-VIN): for every observed lane-piece (edge 1: 1 piece; edges 2, 3, 4: 3 pieces; edge 5: 1 piece;
per lane) -> [human count / piece capacity, human mean speed / 23, AV count / capacity, AV mean speed / 23],
plus outflow over the last 20 s / 2000 veh/h, plus the previous action. Fixed normalisation (no VecNormalize).

Action (A-VIN): AV maximum speed per controlled lane-piece (edges 2 and 3: 2 pieces x 4 lanes; edge 4: 3 pieces
x 2 lanes = 22 values) in [-1, 1] -> [V_MIN, 23] m/s. AVs on edges 1 and 5 are uncapped.

Reward:
  R-OUT  outflow over the last 20 s / 2000 (Vinitsky: "the outflow over the past 20 seconds")
  R-TTS  -(vehicles in network + vehicles waiting to enter) / 200 per decision (sums to -TTS incl. origin queue)
Each reset starts a fresh SUMO with a freshly seeded demand: no state can leak between episodes.
"""
from __future__ import annotations

import os
from collections import deque

import gymnasium as gym
import libsumo as ls
import numpy as np

from vsl_lab.config import E_CORES, RUNS_ROOT
from vsl_lab.plants import bn4
from vsl_lab.sim.runner import SumoSim

SPEED = 23.0
V_MIN = 1.0
OBS_PIECES = {"1": 1, "2": 3, "3": 3, "4": 3, "5": 1}
ACT_PIECES = {"2": 2, "3": 2, "4": 3}


class FBMeter:
    """Vinitsky et al. (2018) Sec. III-E feedback ramp meter at node 3 (140 m before the bottleneck):
    q(k+1) = q(k) + K_F (n_crit - n_hat), n_hat = vehicles on segment 4, updated every T s; cycle =
    fixed 6 s green + variable red, c = 2 M 3600 / q (2 vehicles per lane per green, M = 4 lanes).
    Paper values T = 30, K_F = 20, n_crit = 8 ("tuned empirically ... there may be better values")."""

    def __init__(self, K_F=20.0, n_crit=8.0, T=30.0, green=6.0, q0=1500.0, q_min=200.0, q_max=4000.0, M=4):
        self.K_F, self.n_crit, self.T, self.green, self.M = K_F, n_crit, T, green, M
        self.q, self.q_min, self.q_max = q0, q_min, q_max
        self.t_update = None
        self.t_cycle0 = None

    def cycle(self) -> float:
        return max(self.green, 2.0 * self.M * 3600.0 / self.q)

    def step(self, t: float) -> None:
        if self.t_update is None:
            self.t_update, self.t_cycle0 = t, t
        if t - self.t_update >= self.T - 1e-9:
            n_hat = ls.edge.getLastStepVehicleNumber("4")
            self.q = float(np.clip(self.q + self.K_F * (self.n_crit - n_hat), self.q_min, self.q_max))
            self.t_update = t
        c = self.cycle()
        phase_t = (t - self.t_cycle0) % c
        ls.trafficlight.setRedYellowGreenState(bn4.TLS_ID, "GGGG" if phase_t < self.green else "rrrr")


class BN4Env(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, inflow=(2300.0, 2300.0), av_share: float = 0.1, warmup_s: float = 40.0,
                 control_s: float = 900.0, decision_s: float = 1.0, reward: str = "out",
                 seed_pool=(7210000, 7219999), tag: str = "train", pin_ecores: bool = True,
                 eval_seeds=None, drain_after: bool = False, meter: bool = False, t_drain_max: float = 7200.0,
                 quiet: bool = True, check_actuator: bool = True):
        super().__init__()
        if quiet:   # SUMO prints warnings to stderr; they are kept in the per-run --log file and parsed by health
            try:
                fd = os.open(os.devnull, os.O_WRONLY)
                os.dup2(fd, 2)
            except OSError:
                pass
        if pin_ecores:
            try:
                os.sched_setaffinity(0, set(E_CORES))
            except OSError:
                pass
        self.inflow = inflow
        self.av_share = av_share
        self.warmup_s, self.control_s, self.decision_s = warmup_s, control_s, decision_s
        self.reward_kind = reward
        self.seed_pool = seed_pool
        self.eval_seeds = list(eval_seeds) if eval_seeds is not None else None
        self._eval_i = 0
        self.tag = tag
        self.drain_after = drain_after
        self.meter_on = meter
        self.check_actuator = check_actuator
        self.t_drain_max = t_drain_max
        self.meter = None
        self.files = bn4.files()
        self.lane_len = bn4.net.lane_lengths_from_net(self.files["net"])
        self.obs_slots = [(e, ln, p) for e, k in OBS_PIECES.items() for ln in range(bn4.net.EDGE_LANES[e])
                          for p in range(k)]
        self.act_slots = [(e, ln, p) for e, k in ACT_PIECES.items() for ln in range(bn4.net.EDGE_LANES[e])
                          for p in range(k)]
        n_obs = 4 * len(self.obs_slots) + 1 + len(self.act_slots)
        self.observation_space = gym.spaces.Box(-1.0, 5.0, shape=(n_obs,), dtype=np.float32)
        self.action_space = gym.spaces.Box(-1.0, 1.0, shape=(len(self.act_slots),), dtype=np.float32)
        self.sim = None
        self.rng = np.random.default_rng()
        self.prev_action = np.zeros(len(self.act_slots), dtype=np.float32)
        self.arrivals_20s = deque()
        self.ep_info = {}

    # ------------------------------------------------------------------ helpers
    def _piece(self, edge: str, pos: float, k: int) -> int:
        L = self.lane_len[f"{edge}_0"]
        return min(int(pos / L * k), k - 1)

    def _observe(self) -> np.ndarray:
        nh = {s: 0 for s in self.obs_slots}
        vh = {s: 0.0 for s in self.obs_slots}
        na = {s: 0 for s in self.obs_slots}
        va = {s: 0.0 for s in self.obs_slots}
        for e, k in OBS_PIECES.items():
            for vid in ls.edge.getLastStepVehicleIDs(e):
                ln = ls.vehicle.getLaneIndex(vid)
                p = self._piece(e, ls.vehicle.getLanePosition(vid), k)
                s = (e, ln, p)
                v = ls.vehicle.getSpeed(vid)
                if vid in self.av_ids:
                    na[s] += 1
                    va[s] += v
                else:
                    nh[s] += 1
                    vh[s] += v
        feats = []
        for s in self.obs_slots:
            e, ln, p = s
            cap = self.lane_len[f"{e}_{ln}"] / OBS_PIECES[e] / 7.0   # jam capacity of the piece
            feats += [nh[s] / cap, (vh[s] / nh[s] / SPEED) if nh[s] else 0.0,
                      na[s] / cap, (va[s] / na[s] / SPEED) if na[s] else 0.0]
        feats.append(self._outflow_20s() / 2000.0)
        feats += list(self.prev_action)
        return np.asarray(feats, dtype=np.float32)

    def _outflow_20s(self) -> float:
        while self.arrivals_20s and self.arrivals_20s[0][0] < self.sim.t - 20.0 + 1e-9:
            self.arrivals_20s.popleft()
        return sum(n for _, n in self.arrivals_20s) * 3600.0 / 20.0

    def _apply(self, action: np.ndarray) -> None:
        """AV caps per lane-piece with Vinitsky's physical bounds: each slot's cap moves by at most
        -1.5 m/s^2 * dt / +1.0 m/s^2 * dt per decision, and no AV is asked to brake harder than 1.5 m/s^2
        (applied cap >= v_current - 1.5 dt). Avoids the emergency braking caught in the first smoke run."""
        a = np.clip(action, -1.0, 1.0)
        target = V_MIN + (a + 1.0) * 0.5 * (SPEED - V_MIN)
        dt = self.decision_s
        self.slot_caps = np.clip(target, self.slot_caps - 1.5 * dt, self.slot_caps + 1.0 * dt)
        capmap = {s: float(c) for s, c in zip(self.act_slots, self.slot_caps)}
        for e in ("1", "2", "3", "4", "5"):
            for vid in ls.edge.getLastStepVehicleIDs(e):
                if vid not in self.av_ids:
                    continue
                if e in ACT_PIECES:
                    s = (e, ls.vehicle.getLaneIndex(vid), self._piece(e, ls.vehicle.getLanePosition(vid), ACT_PIECES[e]))
                    v = ls.vehicle.getSpeed(vid)
                    ls.vehicle.setMaxSpeed(vid, max(capmap[s], v - 1.5 * dt, 0.5))
                else:
                    ls.vehicle.setMaxSpeed(vid, 30.0)

    def _check_actuator(self) -> None:
        bad = 0
        capmap = {sl: float(c) for sl, c in zip(self.act_slots, self.slot_caps)}
        for e, k in ACT_PIECES.items():
            for vid in ls.edge.getLastStepVehicleIDs(e):
                if vid not in self.av_ids:
                    continue
                sl = (e, ls.vehicle.getLaneIndex(vid), self._piece(e, ls.vehicle.getLanePosition(vid), k))
                ms = ls.vehicle.getMaxSpeed(vid)
                # applied cap = max(slot cap, v - 1.5 dt, 0.5) at the last decision; allow 2 m/s slack for motion
                if ms > max(capmap[sl], ls.vehicle.getSpeed(vid) + 2.0, 0.5) + 1e-6:
                    bad += 1
        self.n_actuator_checks += 1
        if bad:
            self.sim.health.add("FAIL", "H-R7", self.sim.t, f"{bad} AVs on controlled edges without their cap")

    def _advance(self, seconds: float) -> int:
        a0 = self.sim.arrived
        self.sim.run_until(self.sim.t + seconds)
        n = self.sim.arrived - a0
        if n:
            self.arrivals_20s.append((self.sim.t, n))
        return n

    def _n_system(self) -> int:
        return ls.vehicle.getIDCount() + len(ls.simulation.getPendingVehicles())

    # ------------------------------------------------------------------ gym API
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if self.sim is not None:
            self._close_sim()
        if self.eval_seeds is not None:
            ep_seed = self.eval_seeds[self._eval_i % len(self.eval_seeds)]
            self._eval_i += 1
        else:
            ep_seed = int(self.np_random.integers(self.seed_pool[0], self.seed_pool[1] + 1))
        q = float(self.np_random.uniform(*self.inflow)) if self.inflow[0] != self.inflow[1] else float(self.inflow[0])
        t_total = self.warmup_s + self.control_s
        dem = bn4.demand(ep_seed, [(0.0, t_total, q)], av_share=self.av_share)
        run_dir = RUNS_ROOT / "t1" / "envs" / self.tag / f"pid{os.getpid()}"
        rou = run_dir / f"routes_q{int(q)}_s{ep_seed}_pid{os.getpid()}.rou.xml"
        run_dir.mkdir(parents=True, exist_ok=True)
        dem.write(rou)
        # AVs by id: after the first setMaxSpeed SUMO gives a vehicle its own type 'av@<vid>', so getTypeID
        # cannot identify AVs (this silently disabled the actuator in R2 v1)
        self.av_ids = {vid for _, vid, _, vt in dem.vehicles if vt == "av"}
        self.sim = SumoSim(self.files["net"], rou, run_dir, dem, additional=[self.files["add"]],
                           step_length=bn4.STEP_LENGTH, checkpoint_s=300.0, seed=ep_seed)
        self.sim.start()
        bn4.set_all_green()
        self.sim.asserts.append(bn4.assert_all_green)
        self.arrivals_20s.clear()
        self.prev_action = np.zeros(len(self.act_slots), dtype=np.float32)
        self.slot_caps = np.full(len(self.act_slots), SPEED, dtype=np.float64)
        self.n_actuator_checks = 0
        self.ep_info = {"seed": ep_seed, "inflow": q, "ret": 0.0}
        self.meter = FBMeter() if self.meter_on else None
        if self.meter is not None:   # the TLS is now driven by the meter, not held at all-green
            self.sim.asserts.remove(bn4.assert_all_green)
        self._advance(self.warmup_s)   # uncontrolled warm-up (AVs follow IDM)
        self._t_ctrl0 = self.sim.t
        self._arr_ctrl0 = self.sim.arrived
        return self._observe(), {}

    def step(self, action):
        if self.meter is not None:
            self.meter.step(self.sim.t)
        self._apply(np.asarray(action, dtype=np.float32))
        if self.check_actuator and int(self.sim.t) % 60 == 0:
            self._check_actuator()
        self.prev_action = np.clip(np.asarray(action, dtype=np.float32), -1, 1)
        n0_tts = self.sim.tts_system
        self._advance(self.decision_s)
        if self.reward_kind == "out":
            r = self._outflow_20s() / 2000.0
        elif self.reward_kind == "tts":
            r = -(self.sim.tts_system - n0_tts) / self.decision_s / 200.0
        else:
            raise ValueError(self.reward_kind)
        obs = self._observe()
        if not np.all(np.isfinite(obs)) or not np.isfinite(r):
            self.sim.health.add("FAIL", "H-R6", self.sim.t, "non-finite obs/reward")
            obs = np.nan_to_num(obs)
            r = 0.0
        self.ep_info["ret"] += r
        done = self.sim.t >= self._t_ctrl0 + self.control_s - 1e-9
        info = {}
        if done:
            ctrl_s = self.sim.t - self._t_ctrl0
            info["episode_metrics"] = {
                "outflow_ctrl_vph": (self.sim.arrived - self._arr_ctrl0) * 3600.0 / ctrl_s,
                "served_ctrl_end": self.sim.arrived,
                "tts_system_ctrl_vehh": self.sim.tts_system / 3600.0,
                "n_system_end": self._n_system(),
                "seed": self.ep_info["seed"], "inflow": self.ep_info["inflow"], "return": self.ep_info["ret"],
            }
            drained = None
            if self.drain_after:   # uncontrolled drain: release AV caps, all-green, run until empty
                for vid in ls.vehicle.getIDList():
                    if vid in self.av_ids:
                        ls.vehicle.setMaxSpeed(vid, 30.0)
                if self.meter is not None:
                    bn4.set_all_green()
                    self.meter = None
                self.sim.demand_end_t = self.sim.t
                drained = self.sim.drain(self.t_drain_max)
                gen = self.sim._total
                info["episode_metrics"].update({
                    "tts_system_full_vehh": self.sim.tts_system / 3600.0,
                    "mean_time_in_system_s": self.sim.tts_system / max(gen, 1),
                    "generated": gen, "drained": drained, "t_drained": self.sim.t})
            res = self._close_sim(drained=drained)
            info["health"] = res["health"]["status"]
            info["health_codes"] = list(res["health"]["by_code"].keys())
        return obs, float(r), bool(done), False, info

    def _close_sim(self, drained=None) -> dict:
        res = self.sim.close(drained=drained)
        self.sim = None
        return res

    def close(self):
        if self.sim is not None:
            try:
                self._close_sim()
            except Exception:
                pass
