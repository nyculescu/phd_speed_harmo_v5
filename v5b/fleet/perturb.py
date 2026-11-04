"""V341: perturbations X on the frozen plant, for the phase 2 wave check. Applied inside the window only, so a run with X
and its pair without X are identical until the first event. Kinds:
brake: every `period` s a human car near the middle of edge 4 slows to `target_kmh` (or `factor` x its speed), holds, then resumes.
truck: every `period` s a truck entering edge 1 is capped at `cap_kmh` for the rest of its trip.
burst: ramp departures are grouped on a `cycle` s grid, as behind an upstream signal.
slowdown: edge 4's limit drops to `limit_kmh` for `dur` s at `times`.
outage: V2V is lost for `dur` s at `times`, so every ALKS reverts to the contract's headway.
A slowdown with `oracle` {d, cap_kmh} also caps every ALKS within d m upstream of edge 4, from d / ORACLE_SPEED s before the
event until it ends (V343): the upper bound of what a controller that knows the event in advance can do with a speed cap.
With `hw_oracle` {d, level, after} every ALKS from d m upstream of edge 4 to its end uses at most that headway level, from
d / ORACLE_SPEED s before the event until `after` s past its end (V346). `taper` lowers the limit gradually, because vehicles
already on the edge must obey a new limit at once (V345).
Kind random: for training (V358), each episode draws no perturbation (one third) or a tapered slowdown on edge 3, 4 or 5, from
the episode's seed, so the draw repeats. `edge` selects a slowdown's edge, 4 by default.
"""
from __future__ import annotations

import math

import libsumo as ls
import numpy as np

BRAKE_EDGE, BRAKE_LANE, BRAKE_POS, BRAKE_RANGE = "4", 1, 500.0, 200.0
DECEL = 4.0
TRUCK_ENTRY_M = 600.0
SLOW_EDGE = "4"
FREE_LIMIT = 100.0 / 3.6
EDGE4_LEN = 1000.0
EDGE4_X = 4989.02
ORACLE_SPEED = 25.0


class Perturb:
    def __init__(self, env, spec: dict, seed: int = 0):
        if spec["kind"] == "random":
            r = np.random.default_rng(seed + 910_000)
            spec = {"kind": "none"}
            if r.random() >= 1.0 / 3.0:
                spec = {"kind": "slowdown", "edge": str(r.choice(("3", "4", "5"))), "limit_kmh": float(r.uniform(25.0, 60.0)), "dur": float(r.uniform(60.0, 180.0)), "times": [float(r.uniform(400.0, 1200.0))], "taper": 20.0}
        self.env, self.s, self.kind = env, spec, spec["kind"]
        self.next_t = spec.get("first", env.warm)
        self.active = None
        self.slow_on = False
        self.log = []
        self.oracle_now = self.hw_now = None
        self.slow_v = env.plant.get("limit", FREE_LIMIT)

    def demand(self) -> None:
        if self.kind != "burst":
            return
        d, cycle = self.env.dem, self.s["cycle"]
        for v, r in zip(d.veh, d.route_of):
            if r.startswith("ramp") and v.depart >= self.env.warm:
                v.depart = math.ceil(v.depart / cycle) * cycle
        order = sorted(range(len(d.veh)), key=lambda i: d.veh[i].depart)
        d.veh[:], d.route_of[:] = [d.veh[i] for i in order], [d.route_of[i] for i in order]

    def step(self, t: float) -> None:
        o = self.s.get("oracle")
        if o:
            lead = o["d"] / ORACLE_SPEED
            on = any(t0 - lead <= t < t0 + self.s["dur"] for t0 in self.s["times"])
            self.oracle_now = (EDGE4_X - o["d"], o["cap_kmh"] / 3.6) if on else None
        h = self.s.get("hw_oracle")
        if h:
            lead = h["d"] / ORACLE_SPEED
            on = any(t0 - lead <= t < t0 + self.s["dur"] + h["after"] for t0 in self.s["times"])
            self.hw_now = (EDGE4_X - h["d"], EDGE4_X + EDGE4_LEN, h["level"]) if on else None
        getattr(self, "_" + self.kind, lambda _: None)(t)

    def _brake(self, t: float) -> None:
        if self.active:
            v, target, t_hold, t_end, phase = self.active
            if v not in ls.vehicle.getIDList():
                self.active = None
            elif phase == 0 and t >= t_hold:
                ls.vehicle.setSpeed(v, target)
                self.active = (v, target, t_hold, t_end, 1)
            elif phase == 1 and t >= t_end:
                ls.vehicle.setSpeed(v, -1)
                self.active = None
            return
        if t < self.next_t:
            return
        near = [v for v in ls.lane.getLastStepVehicleIDs(f"{BRAKE_EDGE}_{BRAKE_LANE}")
                if v not in self.env.alks_all and ls.vehicle.getVehicleClass(v) != "trailer" and abs(ls.vehicle.getLanePosition(v) - BRAKE_POS) < BRAKE_RANGE]
        if not near:
            return
        v = min(near, key=lambda x: abs(ls.vehicle.getLanePosition(x) - BRAKE_POS))
        s = ls.vehicle.getSpeed(v)
        target = min(s, self.s["target_kmh"] / 3.6) if "target_kmh" in self.s else self.s["factor"] * s
        down = max((s - target) / DECEL, 0.1)
        ls.vehicle.slowDown(v, target, down)
        self.active = (v, target, t + down, t + down + self.s["hold"], 0)
        self.log.append((round(t), v, round(s, 1), round(target, 1)))
        self.next_t += self.s["period"]

    def _truck(self, t: float) -> None:
        if t < self.next_t:
            return
        for v in ls.edge.getLastStepVehicleIDs("1"):
            if ls.vehicle.getVehicleClass(v) == "trailer" and ls.vehicle.getLanePosition(v) < TRUCK_ENTRY_M:
                ls.vehicle.setMaxSpeed(v, self.s["cap_kmh"] / 3.6)
                self.log.append((round(t), v))
                self.next_t += self.s["period"]
                return

    def _slowdown(self, t: float) -> None:
        free, lim, taper = self.env.plant.get("limit", FREE_LIMIT), self.s["limit_kmh"] / 3.6, self.s.get("taper", 0.0)
        v = free
        for t0 in self.s["times"]:
            if t0 <= t < t0 + self.s["dur"]:
                v = free + (lim - free) * (t - t0) / taper if t < t0 + taper else lim
        if v != self.slow_v:
            ls.edge.setMaxSpeed(self.s.get("edge", SLOW_EDGE), v)
            self.slow_v = v
        on = v != free
        if on != self.slow_on:
            self.slow_on = on
            self.log.append((round(t), on))

    def _outage(self, t: float) -> None:
        on = any(t0 <= t < t0 + self.s["dur"] for t0 in self.s["times"])
        if on != self.env.v2v_down:
            self.log.append((round(t), on))
        self.env.v2v_down = on
