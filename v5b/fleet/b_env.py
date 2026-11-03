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
from collections import defaultdict
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
MOVING = 1.0     # a stopped queue rests at about minGap (2.5 m), so only followers above this speed count as short gaps (V283)
V2V_RANGE = 150.0
HEADWAYS_S = (1.6, 1.2, 1.0, 0.8)
N_ZONES = 3
ZONE_UP, ZONE_MERGE, ZONE_DOWN = 0, 1, 2
ZONE_NORM = 300.0
ZONE_HOLD = 60.0
W_GAP = 2.0     # per follower-second with a bumper gap < 2.5 m; about the size of the flow and speed gains (V276)
V_FLOOR = 5.0
GAP_NORM = 100.0
COLLISION_COST = 10.0
SEED0 = 7_410_000
SEEDS_PER_WORKER = 400     # workers 0-23 stay below 7,419,600; the top of the block is validation and the V265 scan
REF_BRAKE, REF_E3, REF_N = 0.6, 0.5, 350.0     # no-control scan, V265
W_BRAKE, W_E3, W_N = 1.0, 1.0, 10.0
# No control per level (V267): braking >= 3 m/s² /s, TTC < 3 s /s, vehicles in system.
REF_LEVEL = {4090.0: (0.48, 0.249, 299.3), 4300.0: (0.672, 0.606, 321.9), 4600.0: (0.813, 0.784, 369.5),
             5300.0: (0.603, 0.64, 539.8)}
# The same with ALKS action step 0.5 s (V280 delay-only rows, seeds 7,419,910-929).
REF_DELAY = {4090.0: (0.696, 0.378, 299.6), 4600.0: (0.931, 0.857, 377.6), 5300.0: (0.807, 0.742, 530.3)}
SAFETY_TAU = 60.0
ALKS_TAU0 = fl.ALKS_TAU
CAV_LOCAL, CAV_GLOBAL = 16, 10
BIN_M = 200.0
RAMP_LEN, RAMP_R_LEN = 420.0, 392.0     # edges r + rj before the 3a start
LEN_3, LEN_4 = 1196.0, 1000.0
RAMP_ZONE_END = 295.0 + bm.MA_EDGE3_HEAD     # end of the merge zone from the 3a start
# Per-vehicle reward (V289, V292). Own level hardly moves own speed; randomised per trip, the flow term at 0.4 makes short headways pay outside the merge zone. Safety 20: at 10, run 3 kept 0.8 s through the merge zone.
W_CAV_OWN, W_CAV_NEAR, W_CAV_TTC, W_CAV_BRAKE = 0.5, 0.5, 20.0, 20.0
W_CAV_FLOW = 0.4
Q_REF = 0.6     # veh/s per lane, about 2,200 veh/h
FREE_SPACING = 200.0     # no leader within sensing range
W_MOVE = 0.01     # per move; small, the rate limit is what prevents chatter


def make(zones: bool = False, cav: bool = False, **kw):
    return CavEnv(**kw) if cav else ZoneEnv(**kw) if zones else MergeEnv(**kw)


class MergeEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, share: float = 0.5, levels: tuple = (4000.0, 4090.0), episode: float = 1500.0, warm: float = 300.0,
                 worker: int = 0, seed0: int = SEED0, step: float = 0.1, seeds: list | None = None,
                 run_dir: str | None = None, report_net: bool = False, shared: bool = False, decision: float = 1.0,
                 n_ep0: int = 0, reward: str = "safety", tau: float | None = None,
                 v2v_tau: float | None = None, alks_asl: float | None = None, ref_delay: bool = False):
        self.share, self.levels, self.episode, self.warm, self.worker = share, tuple(levels), episode, warm, worker
        self.seed0, self.dt, self.seeds, self.report_net = seed0, step, seeds, report_net
        self.run_dir = Path(run_dir) if run_dir else RUNS_ROOT / "b_train_rd"
        self.n_ep = n_ep0
        self.shared, self.decision, self.reward, self.tau = shared, decision, reward, tau
        self.v2v_tau, self.alks_asl, self.ref = v2v_tau, alks_asl, REF_DELAY if ref_delay else REF_LEVEL
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
        if self.alks_asl is not None:
            fl.ALKS_EXPLICIT["actionStepLength"] = self.alks_asl
        d = fl.build_net(self.cfg)
        self.t_end = self.warm + self.episode
        self.dem = fl.FleetDemand(s, [(0.0, self.t_end, q)], self.cfg)
        self.ramp = {v.vid for v, r in zip(self.dem.veh, self.dem.route_of) if r == "ramp"}
        self.alks = {v.vid for v in self.dem.veh if v.cls == "alks" and v.vid not in self.ramp}
        self.alks_all = {v.vid for v in self.dem.veh if v.cls == "alks"}
        self.v2v_lead, self.v2v_on, self.v2v_cur = {}, set(), {}
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
        self.contact = set()
        self.ep = {"E15": 0.0, "E30": 0.0, "brake3": 0.0, "brake45": 0.0, "N": 0.0, "collisions": 0, "contact_steps": 0, "commands": 0, "restore_mismatch": 0, "lock_mismatch": 0,
                   "out_E30": 0.0, "out_b3": 0.0, "arrived": 0, "passed": 0, "mean_v": 0.0, "gap25": 0, "stop_gap": 0, "alks_s": 0, "v2v_s": 0, "changes": 0, "reversals": 0, "ignored": 0,
                   "seed": s, "q": q, "share": self.share, "offset_s": 0.0, "steps": 0}
        per_s = int(round(1.0 / self.dt))
        k = 0
        while self.sim.t < self.warm - 1e-9:
            self._sim_step()
            k += 1
            if k % per_s == 0:
                self._v2v()
        self.q = q
        self.seen4 = set(ls.edge.getLastStepVehicleIDs("4"))
        self.ema_b3, self.ema_e30 = self._ref()[:2] if q in self.ref else (0.0, 0.0)
        return self._obs(), {"seed": s, "q": q, "share": self.share}

    def _ref(self) -> tuple:
        """Levels outside the table use the nearest one; only an evaluation reaches them, where the reward is unused."""
        return self.ref[min(self.ref, key=lambda k: abs(k - self.q))]

    def _v2v(self) -> None:
        """Short headway only behind an ALKS within V2V range, seen as the same leader on two updates; else the contract's."""
        if self.v2v_tau is None:
            return
        for v in ls.vehicle.getIDList():
            if v not in self.alks_all:
                continue
            lead = ls.vehicle.getLeader(v, V2V_RANGE)
            cur = lead[0] if lead and lead[0] in self.alks_all else None
            on = cur is not None and self.v2v_lead.get(v) == cur
            self.v2v_lead[v] = cur
            if on and v not in self.v2v_on:
                ls.vehicle.setTau(v, self.v2v_tau)
                self.v2v_on.add(v)
            elif not on and v in self.v2v_on:
                ls.vehicle.setTau(v, ALKS_TAU0)
                self.v2v_on.discard(v)
            self.ep["alks_s"] += 1
            self.ep["v2v_s"] += on

    def _sim_step(self) -> None:
        self.sim.step()
        pairs = {(c.collider, c.victim) for c in ls.simulation.getCollisions()}
        self.ep["collisions"] += len(pairs - self.contact)
        self.ep["contact_steps"] += len(pairs)
        self.contact = pairs

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
        plus moving followers with a bumper gap below 2.5 m."""
        e30 = b3 = 0
        for v in ls.vehicle.getIDList():
            b3 += ls.vehicle.getAcceleration(v) <= -HARD_BRAKE
            lead = ls.vehicle.getLeader(v, 200.0)
            if not lead or not lead[0]:
                continue
            gap = lead[1] + ls.vehicle.getMinGap(v)
            if gap < MIN_GAP:
                self.ep["gap25" if ls.vehicle.getSpeed(v) > MOVING else "stop_gap"] += 1
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
        self._v2v()
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
        ref_b3, ref_e30, ref_n = self._ref()
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


class ZoneEnv(MergeEnv):
    """V277: a central policy picks a target headway per zone every decision; the V2V rule applies it. An ALKS behind an
    ALKS within V2V range, the same leader on two updates, uses its zone's target; any other ALKS keeps the contract's
    tau. No speed or lane-change commands. Observation: the ramp vehicles and mainline slots of MergeEnv without their
    cap, plus per zone the mean speed, vehicle count, current target and remaining hold, plus the lane speed, 3a count and
    insertion queue. A zone's target changes at most once per ZONE_HOLD s and by one level (V278); other requests are ignored."""

    def __init__(self, headways: tuple = HEADWAYS_S, w_change: float = 0.0, **kw):
        kw.setdefault("reward", "efficiency")
        super().__init__(**kw)
        self.headways, self.w_change = tuple(headways), w_change
        self.action_space = gym.spaces.MultiDiscrete([len(self.headways)] * N_ZONES)
        self.observation_space = gym.spaces.Box(0.0, 1.0, shape=(R * 3 + K * 4 + N_ZONES * 4 + 3,), dtype=np.float32)
        self._clear_zones()

    def _clear_zones(self) -> None:
        self.target = np.zeros(N_ZONES, int)
        self.last_change = [-1e9] * N_ZONES
        self.last_dir = [0] * N_ZONES

    def reset(self, *, seed=None, options=None):
        self._clear_zones()
        self.v2v_tau = self.headways[0]
        return super().reset(seed=seed, options=options)

    def _zone(self, v: str) -> int:
        e = ls.vehicle.getRoadID(v)
        if e == "2":
            return ZONE_MERGE if ls.vehicle.getLanePosition(v) > self.l2 - bm.MA_EDGE2_TAIL else ZONE_UP
        if e == "3":
            return ZONE_MERGE if ls.vehicle.getLanePosition(v) < bm.MA_EDGE3_HEAD else ZONE_DOWN
        if e in ("3a", ":m", ":ae") or e.startswith((":m_", ":ae_")):
            return ZONE_MERGE
        if e in ("4", "5") or e.startswith((":d_", ":b_")):
            return ZONE_DOWN
        return ZONE_UP

    def _apply(self, action) -> None:
        t = self.sim.t
        for z, want in enumerate(np.asarray(action, int)):
            d = int(np.sign(want - self.target[z]))
            if not d:
                continue
            if t - self.last_change[z] < ZONE_HOLD - 1e-9:
                self.ep["ignored"] += 1
                continue
            self.target[z] += d
            self.last_change[z] = t
            self.ep["changes"] += 1
            self.ep["reversals"] += self.last_dir[z] == -d
            self.last_dir[z] = d

    def _taper(self) -> None:
        pass

    def step(self, action):
        c0 = self.ep["changes"]
        o, r, term, trunc, info = super().step(action)
        return o, r - self.w_change * (self.ep["changes"] - c0), term, trunc, info

    def _v2v(self) -> None:
        for v in ls.vehicle.getIDList():
            if v not in self.alks_all:
                continue
            lead = ls.vehicle.getLeader(v, V2V_RANGE)
            cur = lead[0] if lead and lead[0] in self.alks_all else None
            on = cur is not None and self.v2v_lead.get(v) == cur
            self.v2v_lead[v] = cur
            want = self.headways[self.target[self._zone(v)]] if on else ALKS_TAU0
            if self.v2v_cur.get(v, ALKS_TAU0) != want:
                ls.vehicle.setTau(v, want)
                self.v2v_cur[v] = want
                self.ep["commands"] += 1
            self.ep["alks_s"] += 1
            self.ep["v2v_s"] += want != ALKS_TAU0

    def _efficiency(self, passed: int, vbar: float, n: int, b3: int, e30: int) -> float:
        g0 = self.ep["gap25"]
        self._net_stats_gap()
        return super()._efficiency(passed, vbar, n, b3, e30) - W_GAP * (self.ep["gap25"] - g0)

    def _net_stats_gap(self) -> None:
        """Counts bumper gaps below 2.5 m unless the reporting pass has just done it."""
        if not self.report_net:
            self._net_stats()

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
                o += [min(d / CZ, 1.0), min(ls.vehicle.getSpeed(v) / fl.LIMIT, 1.0),
                      min(max(lead[1], 0.0) / GAP_NORM, 1.0) if lead and lead[0] else 1.0,
                      min(max(fol[1], 0.0) / GAP_NORM, 1.0) if fol and fol[0] else 1.0]
            else:
                o += [1.0, 0.0, 1.0, 1.0]
        sp, cnt = [0.0] * N_ZONES, [0] * N_ZONES
        for v in ls.vehicle.getIDList():
            z = self._zone(v)
            sp[z] += ls.vehicle.getSpeed(v)
            cnt[z] += 1
        for z in range(N_ZONES):
            o += [min(sp[z] / cnt[z] / fl.LIMIT, 1.0) if cnt[z] else 1.0, min(cnt[z] / ZONE_NORM, 1.0),
                  self.headways[self.target[z]] / self.headways[0],
                  min(max(ZONE_HOLD - (self.sim.t - self.last_change[z]), 0.0) / ZONE_HOLD, 1.0)]
        o += [min(max(ls.lane.getLastStepMeanSpeed("2_0"), 0.0) / fl.LIMIT, 1.0),
              min(ls.lane.getLastStepVehicleNumber("3a_0") / 40.0, 1.0),
              min(len(ls.simulation.getPendingVehicles()) / 500.0, 1.0)]
        return np.array(o, dtype=np.float32)


class ZoneRule:
    """Non-learning opponent for ZoneEnv: the short level in the given zones while the merge zone's mean speed is below
    `on` (share of the limit), back to the first level above `on` + HYST. It reads only the policy's observation."""
    HYST = 0.1

    def __init__(self, level: int, on: float, zones: tuple):
        self.level, self.on, self.zones = level, on, tuple(zones)
        self.active = False

    def __call__(self, o: np.ndarray) -> np.ndarray:
        v = float(o[R * 3 + K * 4 + ZONE_MERGE * 4])
        self.active = v < self.on + (self.HYST if self.active else 0.0)
        a = np.zeros(N_ZONES, int)
        if self.active:
            a[list(self.zones)] = self.level
        return a


class CavEnv(ZoneEnv):
    """V285: one shared policy picks each ALKS's target headway every decision. The V2V rule is unchanged: the target
    applies only behind an ALKS within V2V range, the same leader on two updates, else the contract's tau. A vehicle's
    target moves one level at most once per `hold` s. Reset, step and rewards hold per-vehicle values keyed by vehicle id;
    an action is a dict {vehicle: level}. Everything observed is on board or a short broadcast from the roadside. The
    observation's mask marks the vehicles whose own `hold`-s clock is due: the policy decides only for them (V290)."""

    def __init__(self, hold: float = 30.0, **kw):
        kw.setdefault("decision", 5.0)
        super().__init__(**kw)
        self.hold = hold
        self._clear_cav()

    def _clear_cav(self) -> None:
        self.lvl, self.moved, self.ldir, self.xlast, self.bins, self.acc = {}, {}, {}, {}, {}, defaultdict(float)
        self.ids, self.on, self.stats, self.asked = [], set(), {}, {}

    def reset(self, *, seed=None, options=None):
        self._clear_cav()
        o, info = super().reset(seed=seed, options=options)
        self.flow_ema = self.q / 3600.0
        self.ep["lv"] = [0] * (N_ZONES * len(self.headways))
        self.acc = defaultdict(float)
        return o, info

    def _apply(self, action: dict) -> None:
        t = self.sim.t
        for v, want in action.items():
            cur = self.lvl.get(v, 0)
            d = int(np.sign(int(want) - cur))
            if not d:
                continue
            if t - self.moved.get(v, -1e9) < self.hold - 1e-9:
                self.ep["ignored"] += 1
                continue
            self.lvl[v] = cur + d
            self.moved[v] = t
            self.ep["changes"] += 1
            self.ep["reversals"] += self.ldir.get(v, 0) == -d
            self.ldir[v] = d
            self.acc[v] -= W_MOVE * self.decision

    def _v2v(self) -> None:
        lv = self.ep.get("lv")
        for v in ls.vehicle.getIDList():
            if v not in self.alks_all:
                continue
            lead = ls.vehicle.getLeader(v, V2V_RANGE)
            cur = lead[0] if lead and lead[0] in self.alks_all else None
            on = cur is not None and self.v2v_lead.get(v) == cur
            self.v2v_lead[v] = cur
            lev = self.lvl.get(v, 0)
            want = self.headways[lev] if on else ALKS_TAU0
            (self.on.add if on else self.on.discard)(v)
            if self.v2v_cur.get(v, ALKS_TAU0) != want:
                ls.vehicle.setTau(v, want)
                self.v2v_cur[v] = want
                self.ep["commands"] += 1
            self.ep["alks_s"] += 1
            self.ep["v2v_s"] += want != ALKS_TAU0
            if on and lv is not None:
                lv[self._zone(v) * len(self.headways) + lev] += 1

    def _net_stats(self) -> tuple:
        """The parent's counts, plus each ALKS's values this second: speed, speed around it, flow contribution (speed over its
        spacing, which pays the vehicle directly for what it adds to flow), its TTC < 3 s and hard braking, and its direct
        follower's."""
        e30 = b3 = 0
        bins, st = defaultdict(list), {}
        for v in ls.vehicle.getIDList():
            sp = ls.vehicle.getSpeed(v)
            hard = ls.vehicle.getAcceleration(v) <= -HARD_BRAKE
            b3 += hard
            ttc = False
            spacing = FREE_SPACING
            lead = ls.vehicle.getLeader(v, 200.0)
            if lead and lead[0]:
                gap = lead[1] + ls.vehicle.getMinGap(v)
                if gap < MIN_GAP:
                    self.ep["gap25" if sp > MOVING else "stop_gap"] += 1
                dv = sp - ls.vehicle.getSpeed(lead[0])
                ttc = bool(dv > 0 and gap / dv < TTC_REWARD)
                e30 += ttc
                spacing = gap + ls.vehicle.getLength(v)
                if lead[0] in self.alks_all:
                    f = st.setdefault(lead[0], [0.0, 0.0, 0.0, 0, 0, 0, 0])
                    f[4] += ttc
                    f[5] += hard
            if v in self.alks_all:
                x = st.setdefault(v, [0.0, 0.0, 0.0, 0, 0, 0, 0])
                x[0], x[2], x[3], x[6] = sp, sp / spacing, ttc, hard
            bins[self._bin(v)].append(sp)
        self.bins = {b: sum(x) / len(x) for b, x in bins.items()}
        live = set(ls.vehicle.getIDList())
        for v, x in st.items():
            if v in live:
                x[1] = self.bins[self._bin(v)]
        self.stats = st
        for v, (sp, near, q, ttc, ft, fh, hard) in st.items():
            self.acc[v] += (W_CAV_OWN * (min(sp / fl.LIMIT, 1.0) - 1.0) + W_CAV_NEAR * (min(near / fl.LIMIT, 1.0) - 1.0) + W_CAV_FLOW * min(q / Q_REF, 1.5)
                            - W_CAV_TTC * (ttc + 0.5 * ft) - W_CAV_BRAKE * (hard + 0.5 * fh))
        return e30, b3

    def _bin(self, v: str) -> tuple:
        return ls.vehicle.getRoadID(v), int(ls.vehicle.getLanePosition(v) // BIN_M)

    def _efficiency(self, passed: int, vbar: float, n: int, b3: int, e30: int) -> float:
        """Flow, speed and vehicles in system, shared by all; flow smoothed, no excess-exposure term. V286: that term's noise
        outweighed everything else, and one vehicle barely moves it. Safety is charged per vehicle in _net_stats."""
        self.flow_ema += (passed - self.flow_ema) / SAFETY_TAU
        ref_n = self._ref()[2]
        return self.flow_ema / (self.q / 3600.0) - 1.0 + vbar / fl.LIMIT - 1.0 - (n / ref_n - 1.0)

    def _x(self, v: str) -> float:
        """Position along the route, 0 at the 3a start; a vehicle inside a junction keeps its last value."""
        e = ls.vehicle.getRoadID(v)
        base = {"1": -self.l1 - self.l2, "2": -self.l2, "3a": 0.0, "3": self.l3a, "r": -RAMP_LEN, "rj": -RAMP_LEN + RAMP_R_LEN}.get(e)
        if base is None:
            if e == "4":
                base = self.l3a + LEN_3
            elif e == "5":
                base = self.l3a + LEN_3 + LEN_4
            else:
                return self.xlast.get(v, 0.0)
        x = base + ls.vehicle.getLanePosition(v)
        self.xlast[v] = x
        return x

    def _obs(self) -> tuple:
        self.l3a = ls.lane.getLength("3a_0")
        sp, cnt = [0.0] * N_ZONES, [0] * N_ZONES
        ids = []
        for v in ls.vehicle.getIDList():
            z = self._zone(v)
            sp[z] += ls.vehicle.getSpeed(v)
            cnt[z] += 1
            if v in self.alks_all:
                ids.append(v)
        vz = [min(sp[z] / cnt[z] / fl.LIMIT, 1.0) if cnt[z] else 1.0 for z in range(N_ZONES)]
        n3a = ls.lane.getLastStepVehicleNumber("3a_0")
        ramp = sorted(self._x(v) for v in ls.lane.getLastStepVehicleIDs("3a_0"))
        rows = []
        for v in ids:
            x = self._x(v)
            s = ls.vehicle.getSpeed(v)
            lead = ls.vehicle.getLeader(v, GAP_NORM)
            fol = ls.vehicle.getFollower(v, GAP_NORM)
            has_lead, has_fol = lead and lead[0], fol and fol[0]
            on_ramp = ls.vehicle.getRoadID(v) in ("r", "rj") or (v in self.ramp and ls.vehicle.getLaneID(v) == "3a_0")
            near = min(ramp, key=lambda r: abs(r - x)) - x if ramp else GAP_NORM
            rows.append([np.clip(x / 1000.0, -3.5, 3.0), np.clip(x / 300.0, -1.0, 1.0), float(on_ramp), ls.vehicle.getLaneIndex(v) / 3.0,
                         s / fl.LIMIT,
                         min(max(lead[1], 0.0) / GAP_NORM, 1.0) if has_lead else 1.0,
                         np.clip((s - ls.vehicle.getSpeed(lead[0])) / 10.0, -1.0, 1.0) if has_lead else 0.0,
                         float(bool(has_lead) and lead[0] in self.alks_all),
                         min(max(fol[1], 0.0) / GAP_NORM, 1.0) if has_fol else 1.0,
                         np.clip((ls.vehicle.getSpeed(fol[0]) - s) / 10.0, -1.0, 1.0) if has_fol else 0.0,
                         self.lvl.get(v, 0) / (len(self.headways) - 1),
                         min(max(self.hold - (self.sim.t - self.moved.get(v, -1e9)), 0.0) / self.hold, 1.0),
                         min(self.bins.get(self._bin(v), fl.LIMIT) / fl.LIMIT, 1.0),
                         vz[ZONE_MERGE], np.clip(near / GAP_NORM, -1.0, 1.0), min(n3a / 40.0, 1.0)])
        self.ids = ids
        t = self.sim.t
        due = np.array([t - self.asked.get(v, -1e9) >= self.hold - 1e-9 for v in ids], dtype=bool)
        for v, d in zip(ids, due):
            if d:
                self.asked[v] = t
        glob = vz + [min(c / ZONE_NORM, 1.0) for c in cnt] + [min(n3a / 40.0, 1.0),
                                                              min(len(ls.simulation.getPendingVehicles()) / 500.0, 1.0),
                                                              min(self.sim.t / self.t_end, 1.0),
                                                              getattr(self, "flow_ema", 0.0) / (self.q / 3600.0) / 1.5]
        return ids, np.array(rows, dtype=np.float32).reshape(-1, CAV_LOCAL), np.array(glob, dtype=np.float32), due

    def step(self, action: dict):
        before = self.ids
        self.acc = defaultdict(float)
        o, g, term, trunc, info = super().step(action)
        secs = self.decision
        return o, {v: g + self.acc[v] / secs for v in before}, term, trunc, info


class CavRule:
    """Non-learning opponent for CavEnv: a fixed level per zone, read from the policy's own observation (position, on-ramp
    flag), so each vehicle moves toward its zone's level at the allowed rate."""

    def __init__(self, levels: tuple):
        self.levels = np.array(levels, int)

    def __call__(self, o: tuple) -> dict:
        ids, lo = o[:2]
        x = lo[:, 0] * 1000.0
        ramp = (lo[:, 2] > 0.5) & (x < 0.0)
        up = (x < -bm.MA_EDGE2_TAIL) | ramp
        z = np.where(up, ZONE_UP, np.where(x < RAMP_ZONE_END, ZONE_MERGE, ZONE_DOWN))
        return dict(zip(ids, self.levels[z].tolist()))
