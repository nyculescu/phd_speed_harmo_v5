"""V341: perturbations X on the frozen plant, for the phase 2 wave check. Applied inside the window only, so a run with X
and its pair without X are identical until the first event. Kinds:
brake: every `period` s a human car near the middle of edge 4 slows to `target_kmh` (or `factor` x its speed), holds, then resumes.
truck: every `period` s a truck entering edge 1 is capped at `cap_kmh` for the rest of its trip.
burst: ramp departures are grouped on a `cycle` s grid, as behind an upstream signal.
slowdown: edge 4's limit drops to `limit_kmh` for `dur` s at `times`.
outage: V2V is lost for `dur` s at `times`, so every ALKS reverts to the contract's headway.
"""
from __future__ import annotations

import math

import libsumo as ls

BRAKE_EDGE, BRAKE_LANE, BRAKE_POS, BRAKE_RANGE = "4", 1, 500.0, 200.0
DECEL = 4.0
TRUCK_ENTRY_M = 600.0
SLOW_EDGE = "4"


class Perturb:
    def __init__(self, env, spec: dict):
        self.env, self.s, self.kind = env, spec, spec["kind"]
        self.next_t = spec.get("first", env.warm)
        self.active = None
        self.slow_on = False
        self.log = []

    def demand(self) -> None:
        if self.kind != "burst":
            return
        d, cycle = self.env.dem, self.s["cycle"]
        for v, r in zip(d.veh, d.route_of):
            if r == "ramp" and v.depart >= self.env.warm:
                v.depart = math.ceil(v.depart / cycle) * cycle
        order = sorted(range(len(d.veh)), key=lambda i: d.veh[i].depart)
        d.veh[:], d.route_of[:] = [d.veh[i] for i in order], [d.route_of[i] for i in order]

    def step(self, t: float) -> None:
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
        on = any(t0 <= t < t0 + self.s["dur"] for t0 in self.s["times"])
        if on != self.slow_on:
            ls.edge.setMaxSpeed(SLOW_EDGE, self.s["limit_kmh"] / 3.6 if on else self.env.plant.get("limit", 100.0 / 3.6))
            self.slow_on = on
            self.log.append((round(t), on))

    def _outage(self, t: float) -> None:
        on = any(t0 <= t < t0 + self.s["dur"] for t0 in self.s["times"])
        if on != self.env.v2v_down:
            self.log.append((round(t), on))
        self.env.v2v_down = on
