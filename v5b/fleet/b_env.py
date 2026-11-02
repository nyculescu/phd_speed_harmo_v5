"""B training environment on m32 (V263): one central merge coordinator capping the mainline ALKS nearest the merge.

Every 1 s it picks a cap offset for each of the K mainline-origin ALKS on road lane 0 closest to the 3a start (within
CZ m). Actuator as in the CAV contract (bind_B_core_v2 §3): control.command with the run step, lane-change lock 1537
while capped, exact restore at release; no changeLane, openGap or setSpeed. The observation holds current states only,
no schedule and no lane-change wishes. Reward per second: minus hard braking (>= 3 m/s²) and TTC < 3 s exposure on the
merge lanes inside MA and the vehicles in the system (network + insertion queue, so delay moved to the ramp or the entry
counts), each against a no-control reference; a SUMO collision event costs COLLISION_COST. TTC < 1.5 s (the bind
check's E_MA) is too sparse to train on (V265: 0.002-0.11 /s under no control) and stays an evaluation metric.
"""
from __future__ import annotations

import os
from pathlib import Path

import gymnasium as gym
import libsumo as ls
import numpy as np

from v5b.d1.config import RUNS_ROOT
from v5b.fleet import b_merge as bm, control as ct, fleet as fl
from v5b.fleet.day import CrashSim

K, R = 6, 4
OFFSETS_KMH = (0.0, 5.0, 10.0, 15.0, 20.0, 30.0)
SHARED_OFFSETS_KMH = (0.0, 10.0, 20.0, 30.0, 40.0, 50.0)
CZ = 1500.0
TTC_EVAL, TTC_REWARD = 1.5, 3.0
HARD_BRAKE, EMERG_BRAKE = 3.0, 4.5
LOCK = 1537
MIN_GAP = 2.5
V_FLOOR = 5.0
GAP_NORM = 100.0
COLLISION_COST = 10.0
SEED0 = 7_410_000
SEEDS_PER_WORKER = 400     # workers 0-23 stay below 7,419,600; the top of the block is validation and the V265 scan
REF_BRAKE, REF_E3, REF_N = 0.6, 0.5, 350.0     # no-control scan, V265
W_BRAKE, W_E3, W_N = 1.0, 1.0, 10.0
# No control per level (V267): braking >= 3 m/s² /s, TTC < 3 s /s, vehicles in system.
REF_LEVEL = {4090.0: (0.48, 0.249, 299.3), 4300.0: (0.672, 0.606, 321.9), 4600.0: (0.813, 0.784, 369.5)}
SAFETY_TAU = 60.0
ALKS_TAU0 = fl.ALKS_TAU


class MergeEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, share: float = 0.5, levels: tuple = (4000.0, 4090.0), episode: float = 1500.0, warm: float = 300.0,
                 worker: int = 0, seed0: int = SEED0, step: float = 0.1, seeds: list | None = None,
                 run_dir: str | None = None, report_net: bool = False, shared: bool = False, decision: float = 1.0,
                 n_ep0: int = 0, reward: str = "safety", tau: float | None = None):
        self.share, self.levels, self.episode, self.warm, self.worker = share, tuple(levels), episode, warm, worker
        self.seed0, self.dt, self.seeds, self.report_net = seed0, step, seeds, report_net
        self.run_dir = Path(run_dir) if run_dir else RUNS_ROOT / "b_train_rd"
        self.n_ep = n_ep0
        self.shared, self.decision, self.reward, self.tau = shared, decision, reward, tau
        self.offsets = SHARED_OFFSETS_KMH if shared else OFFSETS_KMH
        self.sim = None
        self.action_space = gym.spaces.Discrete(len(self.offsets)) if shared else gym.spaces.MultiDiscrete([len(self.offsets)] * K)
        self.observation_space = gym.spaces.Box(0.0, 1.0, shape=(R * 3 + K * 5 + 4,), dtype=np.float32)

    def _close(self) -> None:
        if self.sim is not None:
            self.sim.close(drained=False)
            for f in (self.rou, self.sim.stat_file, self.sim.log_file):
                f.unlink(missing_ok=True)
            self.sim = None

    def close(self) -> None:
        self._close()

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self._close()
        opt = options or {}
        if self.seeds is not None:
            s = self.seeds[self.n_ep % len(self.seeds)]
        else:
            if self.n_ep >= SEEDS_PER_WORKER:
                raise ValueError("worker out of training seeds")
            s = self.seed0 + self.worker * SEEDS_PER_WORKER + self.n_ep
        q = opt.get("q", self.levels[self.n_ep % len(self.levels)])
        self.n_ep += 1
        self.cfg = bm.setup(self.share, self.dt)
        fl.ALKS_TAU = ALKS_TAU0 if self.tau is None else self.tau
        d = fl.build_net(self.cfg)
        self.t_end = self.warm + self.episode
        self.dem = fl.FleetDemand(s, [(0.0, self.t_end, q)], self.cfg)
        self.ramp = {v.vid for v, r in zip(self.dem.veh, self.dem.route_of) if r == "ramp"}
        self.alks = {v.vid for v in self.dem.veh if v.cls == "alks" and v.vid not in self.ramp}
        self.desired = {v.vid: v.desired for v in self.dem.veh}
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.rou = self.run_dir / f"r_{os.getpid()}_{s}.rou.xml"
        self.dem.write(self.rou)
        self.sim = CrashSim(d / "net.xml", self.rou, self.run_dir, self.dem, additional=[d / "add.xml"],
                            step_length=self.dt, seed=s)
        self.sim.start()
        fl.all_green(bm.PLANT)
        self.l1, self.l2 = ls.lane.getLength("1_0"), ls.lane.getLength("2_0")
        self.held = {}
        self.ep = {"E15": 0.0, "E30": 0.0, "brake3": 0.0, "brake45": 0.0, "N": 0.0, "collisions": 0, "commands": 0, "restore_mismatch": 0, "lock_mismatch": 0,
                   "out_E30": 0.0, "out_b3": 0.0, "arrived": 0, "passed": 0, "mean_v": 0.0, "gap25": 0,
                   "seed": s, "q": q, "share": self.share, "offset_s": 0.0, "steps": 0}
        while self.sim.t < self.warm - 1e-9:
            self._sim_step()
        self.q = q
        self.seen4 = set(ls.edge.getLastStepVehicleIDs("4"))
        self.ema_b3, self.ema_e30 = REF_LEVEL[q][:2] if q in REF_LEVEL else (0.0, 0.0)
        return self._obs(), {"seed": s, "q": q, "share": self.share}

    def _sim_step(self) -> None:
        self.sim.step()
        self.ep["collisions"] += len(ls.simulation.getCollisions())

    def _dist(self, v: str, lane: str) -> float:
        """Distance to the 3a start along road lane 0."""
        x = ls.vehicle.getLanePosition(v)
        return self.l2 - x if lane == "2_0" else self.l2 + self.l1 - x

    def _slots(self) -> list:
        out = []
        for lane in ("2_0", "1_0"):
            for v in ls.lane.getLastStepVehicleIDs(lane):
                if v in self.alks:
                    d = self._dist(v, lane)
                    if d <= CZ:
                        out.append((d, v))
        return sorted(out)[:K]

    def _release(self, v: str, live: set) -> None:
        h = self.held.pop(v)
        if v in live:
            ls.vehicle.setMaxSpeed(v, h["own"])
            ls.vehicle.setLaneChangeMode(v, h["mode"])
            self.ep["restore_mismatch"] += abs(ls.vehicle.getMaxSpeed(v) - h["own"]) > 1e-9
            self.ep["lock_mismatch"] += ls.vehicle.getLaneChangeMode(v) != h["mode"]

    def _apply(self, action) -> None:
        slots = self._slots()
        if self.shared:
            action = [action] * K
        live = set(ls.vehicle.getIDList())
        keep = set()
        for (_, v), a in zip(slots, action):
            off = self.offsets[int(a)] / 3.6
            if off <= 0:
                continue
            des = self.desired[v]
            cap = max(des - off, 0.5 * des, V_FLOOR)
            if v not in self.held:
                self.held[v] = {"own": ls.vehicle.getMaxSpeed(v), "mode": ls.vehicle.getLaneChangeMode(v)}
                ls.vehicle.setLaneChangeMode(v, LOCK)
                self.ep["commands"] += 1
            self.held[v]["cap"] = cap
            self.ep["offset_s"] += off * 3.6
            keep.add(v)
        for v in list(self.held):
            if v not in keep:
                self._release(v, live)

    def _taper(self) -> None:
        live = set(ls.vehicle.getIDList())
        for v, h in list(self.held.items()):
            if v not in live:
                self.held.pop(v)
                continue
            sp = ls.vehicle.getSpeed(v)
            ls.vehicle.setMaxSpeed(v, ct.command(h["cap"], sp, h["own"], dt=self.dt))

    def _merge_stats(self) -> tuple:
        """On the merge lanes inside MA: followers with closing rear TTC below 1.5 s and 3 s (the day.py sampler), and
        vehicles braking at >= 3 and >= 4.5 m/s²."""
        ids = [v for v in ls.lane.getLastStepVehicleIDs("2_0") if ls.vehicle.getLanePosition(v) > self.l2 - bm.MA_EDGE2_TAIL]
        ids += list(ls.lane.getLastStepVehicleIDs("3a_0")) + list(ls.lane.getLastStepVehicleIDs("3a_1"))
        ids += [v for v in ls.lane.getLastStepVehicleIDs("3_0") if ls.vehicle.getLanePosition(v) < bm.MA_EDGE3_HEAD]
        e15 = e30 = b3 = b45 = 0
        for v in ids:
            ac = ls.vehicle.getAcceleration(v)
            b3 += ac <= -HARD_BRAKE
            b45 += ac <= -EMERG_BRAKE
            lead = ls.vehicle.getLeader(v, 200.0)
            if not lead or not lead[0]:
                continue
            dv = ls.vehicle.getSpeed(v) - ls.vehicle.getSpeed(lead[0])
            if dv > 0:
                ttc = (lead[1] + ls.vehicle.getMinGap(v)) / dv
                e15 += ttc < TTC_EVAL
                e30 += ttc < TTC_REWARD
        return e15, e30, b3, b45

    def _net_stats(self) -> tuple:
        """The same counts over every vehicle on the network (report-only, to see exposure moved out of the merge area),
        plus followers with a bumper gap below 2.5 m."""
        e30 = b3 = 0
        for v in ls.vehicle.getIDList():
            b3 += ls.vehicle.getAcceleration(v) <= -HARD_BRAKE
            lead = ls.vehicle.getLeader(v, 200.0)
            if not lead or not lead[0]:
                continue
            gap = lead[1] + ls.vehicle.getMinGap(v)
            self.ep["gap25"] += gap < MIN_GAP
            dv = ls.vehicle.getSpeed(v) - ls.vehicle.getSpeed(lead[0])
            e30 += dv > 0 and gap / dv < TTC_REWARD
        return e30, b3

    def _obs(self) -> np.ndarray:
        o = []
        ramp = []
        for lane, base in (("3a_0", 0.0), ("rj_0", ls.lane.getLength("3a_0")),
                           ("r_0", ls.lane.getLength("3a_0") + ls.lane.getLength("rj_0"))):
            ln = ls.lane.getLength(lane)
            for v in ls.lane.getLastStepVehicleIDs(lane):
                if v in self.ramp:
                    ramp.append((base + ln - ls.vehicle.getLanePosition(v), v, lane == "3a_0"))
        ramp.sort()
        for i in range(R):
            if i < len(ramp):
                d, v, on = ramp[i]
                o += [min(d / 750.0, 1.0), min(ls.vehicle.getSpeed(v) / fl.LIMIT, 1.0), float(on)]
            else:
                o += [1.0, 0.0, 0.0]
        slots = self._slots()
        for i in range(K):
            if i < len(slots):
                d, v = slots[i]
                lead = ls.vehicle.getLeader(v, GAP_NORM)
                fol = ls.vehicle.getFollower(v, GAP_NORM)
                des = self.desired[v]
                cap = self.held.get(v, {}).get("cap", des)
                o += [min(d / CZ, 1.0), min(ls.vehicle.getSpeed(v) / fl.LIMIT, 1.0),
                      min(max(lead[1], 0.0) / GAP_NORM, 1.0) if lead and lead[0] else 1.0,
                      min(max(fol[1], 0.0) / GAP_NORM, 1.0) if fol and fol[0] else 1.0,
                      min((des - cap) * 3.6 / self.offsets[-1], 1.0)]
            else:
                o += [1.0, 0.0, 1.0, 1.0, 0.0]
        pend = len(ls.simulation.getPendingVehicles())
        o += [min(max(ls.lane.getLastStepMeanSpeed("2_0"), 0.0) / fl.LIMIT, 1.0),
              min(ls.lane.getLastStepVehicleNumber("3a_0") / 40.0, 1.0), min(pend / 500.0, 1.0),
              min(self.sim.t / self.t_end, 1.0)]
        return np.array(o, dtype=np.float32)

    def _second(self) -> float:
        for _ in range(int(round(1.0 / self.dt))):
            self._taper()
            self._sim_step()
            self.ep["arrived"] += ls.simulation.getArrivedNumber()
        e15, e30, b3, b45 = self._merge_stats()
        if self.report_net:
            ne30, nb3 = self._net_stats()
            self.ep["out_E30"] += ne30 - e30
            self.ep["out_b3"] += nb3 - b3
        n = ls.vehicle.getIDCount() + len(ls.simulation.getPendingVehicles())
        for k, x in (("E15", e15), ("E30", e30), ("brake3", b3), ("brake45", b45), ("N", n)):
            self.ep[k] += x
        self.ep["steps"] += 1
        c0 = self.ep.setdefault("_c", 0)
        new_c = self.ep["collisions"] - c0
        self.ep["_c"] = self.ep["collisions"]
        ids4 = set(ls.edge.getLastStepVehicleIDs("4"))
        passed = len(ids4 - self.seen4)
        self.seen4 |= ids4
        live = ls.vehicle.getIDList()
        vbar = sum(ls.vehicle.getSpeed(v) for v in live) / len(live) if live else fl.LIMIT
        self.ep["passed"] += passed
        self.ep["mean_v"] += vbar
        if self.reward == "safety":
            return -W_BRAKE * b3 / REF_BRAKE - W_E3 * e30 / REF_E3 - W_N * (n / REF_N - 1.0) - COLLISION_COST * new_c
        return self._efficiency(passed, vbar, n, b3, e30) - COLLISION_COST * new_c

    def _efficiency(self, passed: int, vbar: float, n: int, b3: int, e30: int) -> float:
        """Past-merge flow against demand, mean speed and vehicles in system; safety only as a limit: a smoothed exposure
        above its no-control level costs, below it earns nothing."""
        ref_b3, ref_e30, ref_n = REF_LEVEL[self.q]
        w = 1.0 / SAFETY_TAU
        self.ema_b3 += w * (b3 - self.ema_b3)
        self.ema_e30 += w * (e30 - self.ema_e30)
        over = max(self.ema_b3 / ref_b3 - 1.0, 0.0) + max(self.ema_e30 / ref_e30 - 1.0, 0.0)
        return passed / (self.q / 3600.0) - 1.0 + vbar / fl.LIMIT - 1.0 - (n / ref_n - 1.0) - over

    def step(self, action):
        self._apply(action)
        secs = int(round(self.decision))
        r = sum(self._second() for _ in range(secs)) / secs
        trunc = self.sim.t >= self.t_end - 1e-9
        info = {}
        if trunc:
            live = set(ls.vehicle.getIDList())
            for v in list(self.held):
                self._release(v, live)
            info["ep"] = {k: v for k, v in self.ep.items() if not k.startswith("_")}
        return self._obs(), float(r), False, trunc, info
