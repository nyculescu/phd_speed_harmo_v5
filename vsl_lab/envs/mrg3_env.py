"""MRG3 gymnasium environment (Track 2): posted VSL at an on-ramp merge (TM20), decisions every 60 s.

Action modes (same posted-VSL actuator and staircase as the classical MTFC job, so comparisons are fair):
  direct    Discrete(9): b in {0.2, 0.3, ..., 1.0} (|delta b| <= 0.2 per period enforced, as for MTFC)
  hybrid    Discrete(len(RHO_GRID)): MTFC density set-point rho_hat chosen every `hybrid_every` periods;
            Carlson's MTFC computes b every 60 s (the validated controller stays in the loop)
  residual  Discrete(5): b = MTFC b + {-0.2, -0.1, 0, +0.1, +0.2}, then the MTFC constraints
Observation (S-HIST): last `hist` snapshots of [per-edge 30 s flow/lane / 2400, speed / 120 km/h for up3, up2,
up1, up0a, up0b, down], merge density / 60, ramp flow / 1200, current b, time fraction; plus (optional
S-ORACLE) the hidden non-compliant share.
Reward R-TTS: -(vehicles in network + waiting to enter) averaged over the period / 500 (sums to -TTS incl. queue).
Hidden condition: non-compliant share p_nc drawn per episode from `p_nc_choices` (not observed unless oracle).
"""
from __future__ import annotations

import os
from collections import deque

import gymnasium as gym
import libsumo as ls
import numpy as np

from vsl_lab.config import WORKER_CPUS, RUNS_ROOT
from vsl_lab.controllers.mtfc import MTFC
from vsl_lab.plants import mrg3 as P
from vsl_lab.sim.runner import SumoSim

EDGES = ("up3", "up2", "up1", "up0a", "up0b", "down")
RHO_GRID = (14.0, 17.0, 20.0, 23.0, 26.0, 29.0, 32.0)


class MRG3Env(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, mode: str = "direct", main_peak=(5400.0, 5400.0), ramp_peak=(900.0, 900.0),
                 p_nc_choices=(0.1, 0.3, 0.5), truck: float = 0.1, t_ctrl0: float = 300.0, t_end: float = 3900.0,
                 hist: int = 4, oracle: bool = False, hybrid_every: int = 5, mtfc_kwargs: dict | None = None,
                 seed_pool=(7220000, 7229999), eval_seeds=None, eval_p_nc=None, drain_after: bool = False,
                 tag: str = "train", pin_ecores: bool = True, quiet: bool = True, reward: str = "tts",
                 plant: str = "v1", driver: str | None = None, geom: str = "merge", step: float | None = None,
                 stop_weight: float = 0.0, val_cond: str = "p_nc", trip_stops: bool = False):
        """Round 4 (round4_harmonisation_protocol.md): geom 'lanedrop' (LD3, no ramp demand), step (e.g. 0.2 s),
        stop_weight w (s per new stop) -> reward -(veh-s in system + w * new stops) / (60 * 500); val_cond 'main_peak'
        makes eval_p_nc carry the validation main-peak instead of the compliance share."""
        super().__init__()
        if pin_ecores:
            try:
                os.sched_setaffinity(0, set(WORKER_CPUS))
            except OSError:
                pass
        if quiet:
            try:   # stderr to a per-process file, NOT /dev/null: Python tracebacks must stay visible
                d = RUNS_ROOT / "stderr"
                d.mkdir(parents=True, exist_ok=True)
                os.dup2(os.open(str(d / f"stderr_pid{os.getpid()}.log"), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644), 2)
            except OSError:
                pass
        self.mode, self.main_peak, self.ramp_peak = mode, main_peak, ramp_peak
        self.p_nc_choices, self.truck = tuple(p_nc_choices), truck
        self.t_ctrl0, self.t_end, self.hist_n, self.oracle = t_ctrl0, t_end, hist, oracle
        self.hybrid_every = hybrid_every
        self.mtfc_kwargs = mtfc_kwargs or {}
        self.seed_pool = seed_pool
        self.eval_seeds = list(eval_seeds) if eval_seeds is not None else None
        self.eval_p_nc = eval_p_nc
        self._eval_i = 0
        self.drain_after, self.tag, self.reward_kind = drain_after, tag, reward
        self.model, self.depart_speed = P.PLANTS[plant]
        self.driver = driver   # realism-gate variant (docs/lab/t2_realism_protocol.md); None = plant default
        self.geom, self.dt, self.stop_weight, self.val_cond = geom, (step or P.STEP_LENGTH), float(stop_weight), val_cond
        self.files = P.files(geom)
        self.nd = self.files["n_lanes"]["down"]
        self.sens = P.Sensors(self.files["lanes"])
        self._halting, self.new_stops, self.ep_stops = set(), 0, 0
        self.trip_stops, self._trip = trip_stops, None   # evaluation: SUMO tripinfo stops, as in jobs/mrg3_run.py
        n_snap = 2 * len(EDGES) + 4
        self.observation_space = gym.spaces.Box(-1.0, 5.0, shape=(n_snap * hist + (1 if oracle else 0),), dtype=np.float32)
        self.action_space = {"direct": gym.spaces.Discrete(9), "hybrid": gym.spaces.Discrete(len(RHO_GRID)),
                             "residual": gym.spaces.Discrete(5), "direct_fine": gym.spaces.Discrete(11),
                             "residual_c": gym.spaces.Box(-1.0, 1.0, shape=(1,), dtype=np.float32)}[mode]
        self.b_base = 0.75   # P-H3 (round4 Addendum D): the frozen tuned classical const:0.75
        self.sim = None

    # --------------------------------------------------------------- helpers
    def _post(self, b_app: float, b_acc: float) -> None:
        v = P.V_LIMIT
        P.set_vsl(("up1", "up0a"), b_app * v)
        P.set_vsl(("up2",), min(1.0, b_app + 0.2) * v)
        P.set_vsl(("up3",), min(1.0, b_app + 0.4) * v)
        P.set_vsl(("up0b",), b_acc * v)

    def _snapshot(self) -> list:
        s = []
        for e in EDGES:
            ne = self.nd if e == "down" else 3
            s.append(P.Sensors.flow_vph_per_lane(e, ne) / 2400.0)
            sp = P.Sensors.speed_kmh(e, ne)
            s.append((sp if sp >= 0 else 120.0) / 120.0)
        s.append(self.sens.density_merge_vkl() / 60.0)
        s.append(ls.inductionloop.getLastIntervalVehicleNumber("e1_ramp_0") * 120.0 / 1200.0)
        s.append(self.b)
        s.append((self.sim.t - self.t_ctrl0) / (self.t_end - self.t_ctrl0))
        return s

    def _obs(self) -> np.ndarray:
        o = [x for snap in self.hist for x in snap]
        if self.oracle:
            o.append(self.p_nc)
        return np.asarray(o, dtype=np.float32)

    def _period(self) -> float:
        """Advance 60 s; return mean number of vehicles in system (network + origin queue)."""
        n0 = self.sim.tts_system
        dens = []
        self.new_stops = 0
        for _ in range(6):
            if self.stop_weight > 0:   # count new stops (speed <= 0.1 m/s, as SUMO tripinfo waitingCount) per step
                t_next = self.sim.t + 10.0
                n_sub = max(1, int(round(1.0 / self.dt)))   # sample stops every 1 s (P-H2; training reward only)
                while self.sim.t < t_next - 1e-9:
                    self.sim.step(n_sub)
                    ids = ls.vehicle.getIDList()
                    halting = {v for v in ids if ls.vehicle.getSpeed(v) <= 0.1}
                    self.new_stops += len(halting - self._halting)
                    self._halting = halting
            else:
                self.sim.run_until(self.sim.t + 10.0)
            dens.append(self.sens.density_merge_vkl())
        self.rho_avg = float(np.mean(dens))
        self.ep_stops += self.new_stops
        return (self.sim.tts_system - n0) / 60.0

    # --------------------------------------------------------------- gym API
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if self.sim is not None:
            self.sim.close()
            self.sim = None
        if self.eval_seeds is not None:
            ep_seed = self.eval_seeds[self._eval_i % len(self.eval_seeds)]
            self._eval_i += 1
            if self.val_cond == "main_peak" and self.eval_p_nc is not None:
                self.main_peak = (float(self.eval_p_nc), float(self.eval_p_nc))
                self.p_nc = self.p_nc_choices[0]
            else:
                self.p_nc = self.eval_p_nc if self.eval_p_nc is not None else self.p_nc_choices[0]
        else:
            ep_seed = int(self.np_random.integers(self.seed_pool[0], self.seed_pool[1] + 1))
            self.p_nc = float(self.p_nc_choices[int(self.np_random.integers(0, len(self.p_nc_choices)))])
        rng = np.random.default_rng(ep_seed)
        mp = float(rng.uniform(*self.main_peak))
        rp = float(rng.uniform(*self.ramp_peak))
        mprof = P.profile(2500.0, mp, 600.0, 1200.0, 3000.0, self.t_end)
        rprof = P.profile(300.0, rp, 600.0, 1200.0, 3000.0, self.t_end) if self.geom == "merge" else []
        dem = P.demand(ep_seed, mprof, rprof, p_noncompliant=self.p_nc, truck_share=self.truck, model=self.model,
                       depart_speed=self.depart_speed, driver=self.driver, step_length=self.dt)
        run_dir = RUNS_ROOT / "t2" / "envs" / self.tag / f"pid{os.getpid()}"
        run_dir.mkdir(parents=True, exist_ok=True)
        rou = run_dir / f"routes_s{ep_seed}_pid{os.getpid()}.rou.xml"
        dem.write(rou)
        self._rou = rou
        extra = list(P.DRIVERS[self.driver]["args"] if self.driver else [])
        self._trip = run_dir / f"tripinfo_s{ep_seed}_pid{os.getpid()}.xml" if self.trip_stops else None
        if self._trip is not None:
            extra += ["--tripinfo-output", str(self._trip)]
        self.sim = SumoSim(self.files["net"], rou, run_dir, dem, additional=[self.files["add"]],
                           step_length=self.dt, checkpoint_s=300.0, seed=ep_seed, stuck_wait_s=180.0, extra_args=extra)
        self.sim.start()
        self.b = self.b_base if self.mode == "residual_c" else 1.0
        self.mtfc = MTFC(**self.mtfc_kwargs)
        self.k = 0
        self._halting, self.new_stops, self.ep_stops = set(), 0, 0
        self.ep = {"seed": ep_seed, "p_nc": self.p_nc, "main_peak": mp, "ramp_peak": rp, "ret": 0.0, "min_b": 1.0}
        self.sim.run_until(self.t_ctrl0)
        snap = self._snapshot()
        self.hist = deque([snap] * self.hist_n, maxlen=self.hist_n)
        self.rho_avg = self.sens.density_merge_vkl()
        return self._obs(), {}

    def step(self, action):
        if self.mode == "residual_c":   # P-H3: b = clip(0.75 + 0.25 a, 0.5, 1.0), |delta b| <= 0.2 per period
            a_c = float(np.clip(np.asarray(action, dtype=np.float64).reshape(-1)[0], -1.0, 1.0))
            target = min(max(self.b_base + 0.25 * a_c, 0.5), 1.0)
            self.b = float(np.clip(target, self.b - 0.2, self.b + 0.2))
            b_acc = 0.9 if self.b < 1.0 - 1e-9 else 1.0
            return self._advance(b_acc)
        a = int(np.asarray(action).reshape(-1)[0])
        qc = P.Sensors.flow_vph_per_lane("up0a")
        if self.mode == "direct_fine":   # P-H2: b in {0.5, 0.55, ..., 1.0}, |delta b| <= 0.2 per period
            target = 0.5 + 0.05 * a
            self.b = float(np.clip(target, self.b - 0.2, self.b + 0.2))
            b_acc = 0.9 if self.b < 1.0 - 1e-9 else 1.0
        elif self.mode == "direct":
            target = 0.2 + 0.1 * a
            self.b = float(np.clip(target, self.b - 0.2, self.b + 0.2))
            b_acc = 0.9 if self.b < 1.0 - 1e-9 else 1.0
        elif self.mode == "hybrid":
            if self.k % self.hybrid_every == 0:
                self.mtfc.rho_set = RHO_GRID[a]
            self.b, b_acc = self.mtfc.step(self.rho_avg, qc)
        else:  # residual
            b_m, _ = self.mtfc.step(self.rho_avg, qc)
            target = round((b_m + (a - 2) * 0.1) * 10.0) / 10.0
            self.b = float(np.clip(target, max(0.2, self.b - 0.2), min(1.0, self.b + 0.2)))
            b_acc = 0.9 if self.b < 1.0 - 1e-9 else 1.0
        return self._advance(b_acc)

    def _advance(self, b_acc):
        self._post(self.b, b_acc)
        self.ep["min_b"] = min(self.ep["min_b"], self.b)
        n_sys = self._period()
        r = -(n_sys * 60.0 + self.stop_weight * self.new_stops) / (60.0 * 500.0)
        self.k += 1
        self.hist.append(self._snapshot())
        obs = self._obs()
        if not np.all(np.isfinite(obs)):
            self.sim.health.add("FAIL", "H-R6", self.sim.t, "non-finite observation")
            obs = np.nan_to_num(obs)
        self.ep["ret"] += r
        done = self.sim.t >= self.t_end - 1e-9
        info = {}
        if done:
            self._post(1.0, 1.0)
            m = {"tts_ctrl_vehh": self.sim.tts_system / 3600.0, "seed": self.ep["seed"], "p_nc": self.ep["p_nc"],
                 "main_peak": self.ep["main_peak"], "return": self.ep["ret"], "min_b": self.ep["min_b"],
                 "stops_ctrl": self.ep_stops,
                 "score_h": self.sim.tts_system + self.stop_weight * self.ep_stops}   # s; lower is better
            drained = None
            if self.drain_after:
                drained = self.sim.drain(10800.0)
                br = self.sim.time_in_system_by_route()
                m.update({"mean_time_in_system_s": self.sim.tts_system / max(self.sim._total, 1),
                          "time_main_s": br.get("main", {}).get("mean_s"), "time_ramp_s": br.get("ramp", {}).get("mean_s"),
                          "drained": drained})
            res = self.sim.close(drained=drained)
            self.sim = None
            if self._trip is not None and self._trip.exists():
                import xml.etree.ElementTree as _ET
                wc = [int(el.get("waitingCount", 0)) for _, el in _ET.iterparse(self._trip) if el.tag == "tripinfo"]
                m["stops_per_veh"] = float(np.mean(wc)) if wc else None
                m["n_tripinfo"] = len(wc)
                self._trip.unlink()
            try:
                self._rou.unlink()
            except OSError:
                pass
            info["episode_metrics"] = m
            info["health"] = res["health"]["status"]
            info["health_codes"] = list(res["health"]["by_code"].keys())
        return obs, float(r), bool(done), False, info

    def close(self):
        if self.sim is not None:
            try:
                self.sim.close()
            except Exception:
                pass
            self.sim = None
