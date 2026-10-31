"""E1 controllers on ramp32 (V213, docs/research/protocols/e1_headroom.md §3).

Meter at TLS 'rm': ALINEA at 'alinea_3' or PI-ALINEA at the drop loop, the 150-s queue law, the V190 bounds and
overrides, and a red-rest actuator (one short green per waiting vehicle, 5-s amber at metering onset). ALKS rule:
I-type MTFC on the drop loop, a cap profile that tapers at 1.5 m/s^2 so the cap holds over the zone, applied every
0.1-s step. MC*: a cascade when both laws use the drop loop. Meter, MTFC and the cap profile are pure; SumoMeter,
SumoALKS and LoopBank read and write libsumo.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass

import libsumo as ls

R_MIN, R_MAX = 240.0, 900.0
QUEUE_RATE = 24.0                  # veh/h per queued vehicle: the queue is served in 150 s
PI_CAP = 400.0                     # PI-ALINEA: at most the measured rate + 400 veh/h (Wang 2014)
REST_MARGIN, RESUME_MARGIN, REST_MAX_QUEUE = 1.05, 0.95, 2
OVR_ON, OVR_OFF = 30.0, 15.0       # queue override on the ramp_q occupancy, %
WAIT_ON, WAIT_OFF = 210.0, 150.0   # backstop on the longest wait at the meter, s
G_MIN, G_MAX, AMBER_CAR, AMBER_ONSET = 2.0, 4.0, 1.0, 5.0
OWED_CAP = 2.0
NEAR_LINE, NEAR_SPEED = 15.0, 3.0  # a vehicle waits at the line: within 15 m of it, below 3 m/s
BLOCK_SPEED, BLOCK_TAIL = 2.0, 50.0

V_ALKS = 100.0 / 3.6               # ALKS desired speed (sf 1.0)
A_CAP = 1.5
B_MIN, DB_MAX = 0.3, 0.2
ZONE_END = 892.0
TAPER = (V_ALKS ** 2 - (B_MIN * V_ALKS) ** 2) / (2 * A_CAP)
ZONES = {"short": (592.0 - TAPER, 592.0), "long": (150.0, 150.0 + TAPER)}   # (commands from, cap holds from)
STEP = 0.1
ONE = 1.0 - 1e-9                   # one owed vehicle, robust to float sums


def clip(x: float, lo: float, hi: float) -> float:
    return min(max(x, lo), hi)


def pi_gains(k_p: float, k_i: float, l_bar: float) -> tuple:
    """PI-ALINEA gains from km·lane/h to veh/h per % occupancy: rho = 10 o / L_bar (veh/km/lane, L_bar in m)."""
    return k_p * 10.0 / l_bar, k_i * 10.0 / l_bar


@dataclass
class MeterLaw:
    kind: str                      # "alinea", "pi" or "fixed" (T0 test mode)
    setpoint: float = 0.0          # occupancy %
    k_r: float = 70.0              # ALINEA, veh/h per %
    k_p: float = 0.0               # PI-ALINEA, veh/h per %
    k_i: float = 0.0
    rate: float = R_MAX            # fixed

    def __call__(self, r_s: float, o: float, o_prev: float, r_meas: float) -> float:
        if self.kind == "fixed":
            return self.rate
        if self.kind == "alinea":
            return r_s + self.k_r * (self.setpoint - o)
        return min(r_s - self.k_p * (o - o_prev) + self.k_i * (self.setpoint - o), r_meas + PI_CAP)


class Meter:
    """Rate law and red-rest actuator, one call per whole second; no SUMO.

    update() every 60 s sets the law's rate and the mode (rest green or metering); step() every second runs the
    signal. 'metering' is the red-rest mode; a period counts as metered if it had at least one red phase."""

    def __init__(self, law: MeterLaw, overrides: bool = True):
        self.law, self.overrides = law, overrides
        self.r_law = self.r_cmd = R_MAX
        self.metering = False
        self.state, self.t_state, self.amber = "G", 0.0, AMBER_CAR
        self.target, self.released = 0.0, 0
        self.override = self.backstop = False
        self.o_prev = None
        self.saturated = False
        self.p_red = self.p_dlim = self.p_ovr = False
        self.p_rel = 0
        self.n = {"red_phases": 0, "red_passages": 0, "override_s": 0, "backstop_s": 0, "dlim_s": 0,
                  "metering_s": 0, "owed_s": 0, "owed_released": 0}
        self.log = []

    def update(self, t: float, o: float, n_q: int, q_arr: float) -> None:
        realised = self.p_rel * 60.0
        clean = self.p_red and not (self.p_dlim or self.p_ovr)
        r_s = self.r_law if clean else clip(realised, R_MIN, R_MAX)
        o_prev = o if self.o_prev is None else self.o_prev
        r = self.law(r_s, o, o_prev, realised)
        r_q = QUEUE_RATE * n_q
        r_bound = clip(max(r, r_q), R_MIN, R_MAX)
        self.saturated = self.law.kind != "fixed" and (r_q > r or r <= R_MIN or self.p_ovr)
        self.r_law = r_bound if self.law.kind != "fixed" else self.law.rate
        if self.metering and self.law.kind != "fixed":
            if self.r_law >= R_MAX or (self.r_law >= REST_MARGIN * q_arr and n_q <= REST_MAX_QUEUE):
                self.metering = False
        elif self.r_law < R_MAX and (self.r_law < RESUME_MARGIN * q_arr or self.law.kind == "fixed"):
            self.metering = True
            if self.state == "G" and not self.override:
                self.state, self.t_state, self.amber = "y", t, AMBER_ONSET
            self.target = float(self.released)
        self.log.append((round(t), round(self.r_law, 1), round(realised, 1), round(o, 2), n_q, round(q_arr, 1),
                         int(self.metering), int(self.p_ovr), int(self.backstop), int(self.p_dlim)))
        self.o_prev = o
        self.p_red = self.p_dlim = self.p_ovr = False
        self.p_rel = 0

    def queue_check(self, occ: float) -> None:
        """Every 30 s: the V190 queue-at-ramp-start override on the ramp_q occupancy."""
        if not self.overrides:
            return
        if not self.override and occ >= OVR_ON:
            self.override = True
        elif self.override and occ < OVR_OFF:
            self.override = False

    def step(self, t: float, rel: int, n_near: int, dn_blocked: bool, longest_wait: float) -> str:
        """rel: vehicles that left 'r' during the last second, while the signal showed self.state."""
        if rel and self.state == "r":
            self.n["red_passages"] += rel
        self.released += rel
        self.p_rel += rel
        if self.overrides:
            if not self.backstop and longest_wait >= WAIT_ON:
                self.backstop = True
            elif self.backstop and longest_wait < WAIT_OFF:
                self.backstop = False
        self.n["override_s"] += self.override
        self.n["backstop_s"] += self.backstop
        self.p_ovr |= self.override or self.backstop
        if self.override or not self.metering:
            self.target = float(self.released)
            self._set("G", t)
            return self.state
        self.n["metering_s"] += 1
        self.r_cmd = R_MAX if self.backstop else self.r_law
        self.target = min(self.target + self.r_cmd / 3600.0, self.released + OWED_CAP)
        owed = self.target - self.released
        if owed >= ONE:
            self.n["owed_s"] += 1
        el = t - self.t_state
        if self.state == "G":
            if owed >= ONE and dn_blocked:
                self.n["dlim_s"] += 1
                self.p_dlim = True
            elif el >= G_MIN - 1e-9 and (owed < ONE or n_near == 0 or el >= G_MAX - 1e-9):
                self.amber = AMBER_CAR
                self._set("y", t)
        elif self.state == "y":
            if el >= self.amber - 1e-9:
                self._set("r", t)
        elif owed >= ONE and n_near > 0:
            self._set("G", t)
        return self.state

    def _set(self, s: str, t: float) -> None:
        if s != self.state:
            if s == "r":
                self.n["red_phases"] += 1
                self.p_red = True
            self.state, self.t_state = s, t

    def summary(self) -> dict:
        return {"law": vars(self.law), "overrides": self.overrides, **self.n, "log": self.log}


class MTFC:
    """I-type mainstream traffic flow control: b(k) = clip(b(k-1) + clip(K_I (o_hat - o), -0.2, 0.2), b_min, 1)."""

    def __init__(self, setpoint: float, k_i: float, b_min: float = B_MIN, fixed_b: float | None = None):
        self.setpoint, self.k_i, self.b_min, self.fixed_b = setpoint, k_i, b_min, fixed_b
        self.b = 1.0 if fixed_b is None else fixed_b
        self.log = []

    def update(self, t: float, o: float, release: bool = True) -> float:
        """release = False holds the integrator back (cascade): b returns to 1 at the rate limit."""
        if self.fixed_b is None:
            db = clip(self.k_i * (self.setpoint - o), -DB_MAX, DB_MAX) if release else DB_MAX
            self.b = clip(self.b + db, self.b_min, 1.0)
        self.log.append((round(t), round(self.b, 4), round(o, 2), int(release)))
        return self.b


class Cascade:
    """MC* gate (Carlson et al. 2014 form [VERIFY]): C acts only after the meter saturated in one of the last 2
    minutes, and stops after 5 minutes without saturation."""

    def __init__(self):
        self.hist = deque(maxlen=5)
        self.active = False

    def update(self, saturated: bool) -> bool:
        self.hist.append(saturated)
        if any(list(self.hist)[-2:]):
            self.active = True
        elif self.active and len(self.hist) == 5 and not any(self.hist):
            self.active = False
        return self.active


def cap_at(x: float, c: float, x_hold: float, a: float = A_CAP, v_top: float = V_ALKS) -> float:
    """Cap at position x: c from x_hold on; upstream a deceleration profile that reaches c at x_hold."""
    if x >= x_hold:
        return c
    return min(v_top, math.sqrt(c * c + 2.0 * a * (x_hold - x)))


def command(cap: float, v: float, own_max: float, a: float = A_CAP, dt: float = STEP) -> float:
    """maxSpeed to set: never more than a·dt below the current speed, never above the vehicle's own maxSpeed."""
    return min(max(cap, v - a * dt), own_max)


class LoopBank:
    """30-s readings of every loop group (flow veh/h, occupancy %, vehicle-weighted speed m/s)."""

    def __init__(self, groups: dict):
        self.groups = groups
        self.rows = []

    def read(self, t: float) -> None:
        row = [round(t)]
        for ids in self.groups.values():
            n = [ls.inductionloop.getLastIntervalVehicleNumber(i) for i in ids]
            occ = sum(ls.inductionloop.getLastIntervalOccupancy(i) for i in ids) / len(ids)
            sp = (sum(k * ls.inductionloop.getLastIntervalMeanSpeed(i) for k, i in zip(n, ids) if k) / sum(n)
                  if sum(n) else None)
            row += [sum(n) * 120, round(occ, 3), None if sp is None else round(sp, 2)]
        self.rows.append(row)

    def col(self, group: str, field: int) -> list:
        j = 1 + 3 * list(self.groups).index(group) + field
        return [r[j] for r in self.rows]

    def occ60(self, group: str) -> float:
        """Mean occupancy of the last two complete 30-s intervals."""
        x = self.col(group, 1)[-2:]
        return sum(x) / len(x) if x else 0.0

    def flow5(self, group: str) -> float:
        """Mean flow of the last 10 intervals (5 min), veh/h."""
        x = self.col(group, 0)[-10:]
        return sum(x) / len(x) if x else 0.0


class SumoMeter:
    """Meter on TLS 'rm' and lane 'r_0': releases, waits, red exposure and the downstream test from libsumo."""

    def __init__(self, meter: Meter, bank: LoopBank, loop: str, tls: str = "rm", lane: str = "r_0"):
        self.m, self.bank, self.loop, self.tls, self.lane = meter, bank, loop, tls, lane
        self.len = ls.lane.getLength(lane)
        self.free = self.len / ls.lane.getMaxSpeed(lane)
        self.prev, self.enter, self.red_exp = set(), {}, {}
        self.max_red_exposure = 0.0
        self.waits = []
        self.tail = ls.lane.getLength("3a_0") - BLOCK_TAIL
        self.exit_lanes = ["rj_0"] + [k[2] for links in ls.trafficlight.getControlledLinks(tls) for k in links if k[2]]

    def _dn_blocked(self) -> bool:
        if any(ls.vehicle.getSpeed(v) < BLOCK_SPEED for ln in self.exit_lanes for v in ls.lane.getLastStepVehicleIDs(ln)):
            return True
        return any(ls.vehicle.getLanePosition(v) >= self.tail and ls.vehicle.getSpeed(v) < BLOCK_SPEED
                   for v in ls.lane.getLastStepVehicleIDs("3a_0"))

    def step(self, t: float) -> None:
        cur = set(ls.lane.getLastStepVehicleIDs(self.lane))
        left = self.prev - cur
        for v in left:
            self.waits.append(round(t - self.enter.pop(v, t) - self.free, 1))
            self.red_exp.pop(v, None)
        shown = self.m.state
        for v in cur:
            self.enter.setdefault(v, t)
            if shown != "G":
                self.red_exp[v] = self.red_exp.get(v, 0.0) + 1.0
                self.max_red_exposure = max(self.max_red_exposure, self.red_exp[v])
        self.prev = cur
        n_near = sum(1 for v in cur if self.len - ls.vehicle.getLanePosition(v) <= NEAR_LINE
                     and ls.vehicle.getSpeed(v) < NEAR_SPEED)
        wait = max((t - self.enter[v] - self.free for v in cur), default=0.0)
        if abs(t / 30.0 - round(t / 30.0)) < 1e-6:
            self.m.queue_check(ls.inductionloop.getLastIntervalOccupancy("ramp_q_r_0"))
        if abs(t / 60.0 - round(t / 60.0)) < 1e-6:
            self.m.update(t, self.bank.occ60(self.loop), len(cur), self.bank.flow5("ramp_q"))
        s = self.m.step(t, len(left), n_near, self._dn_blocked() if self.m.metering else False, wait)
        ls.trafficlight.setRedYellowGreenState(self.tls, s)

    def summary(self) -> dict:
        w = sorted(self.waits)
        return {**self.m.summary(), "loop": self.loop, "max_red_exposure_s": self.max_red_exposure,
                "wait_max_s": w[-1] if w else None, "wait_p95_s": w[int(0.95 * (len(w) - 1))] if w else None,
                "waits_over_240": sum(1 for x in w if x > 240.0), "n_waits": len(w)}


class SumoALKS:
    """Per-step caps for the ALKS on edge 3 (V213 Q1); the law updates every 60 s."""

    def __init__(self, law: MTFC, bank: LoopBank, loop: str, zone: str, alks: set, desired: dict, blocked,
                 edge: str = "3"):
        self.law, self.bank, self.loop, self.alks, self.desired, self.blocked = law, bank, loop, alks, desired, blocked
        self.x_cmd, self.x_hold = ZONES[zone]
        self.zone, self.edge = zone, edge
        self.own, self.last, self.v_prev, self.over = {}, {}, {}, {}
        self.n = {"cmd_steps": 0, "cap_violations": 0, "restore_mismatch": 0, "restores": 0}
        self.max_decel = 0.0

    def update(self, t: float, release: bool = True) -> float:
        return self.law.update(t, self.bank.occ60(self.loop), release)

    def step(self, t: float) -> None:
        b = self.law.b
        if b >= 1.0 and not self.own:
            return
        c = b * V_ALKS
        seen = set()
        for v in ls.edge.getLastStepVehicleIDs(self.edge):
            if v not in self.alks:
                continue
            x = ls.vehicle.getLanePosition(v)
            if not self.x_cmd <= x <= ZONE_END or self.blocked(v):
                continue
            cap = cap_at(x, c, self.x_hold)
            if cap >= self.desired[v] - 1e-6:
                continue                     # no constraint here: a commanded vehicle is restored below
            seen.add(v)
            sp = ls.vehicle.getSpeed(v)
            if v not in self.own:
                self.own[v] = ls.vehicle.getMaxSpeed(v)
            if v in self.v_prev:
                self.max_decel = max(self.max_decel, (self.v_prev[v] - sp) / STEP)
            self.v_prev[v] = sp
            cmd = command(cap, sp, self.own[v])
            if abs(cmd - self.last.get(v, -1.0)) > 0.01:
                ls.vehicle.setMaxSpeed(v, cmd)
                self.last[v] = cmd
            self.n["cmd_steps"] += 1
            if abs(t - round(t)) < 1e-6:
                self.over[v] = self.over.get(v, 0) + 1 if sp > cap + 0.5 else 0
                if self.over[v] == 21:
                    self.n["cap_violations"] += 1
        for v in list(self.own):
            if v in seen:
                continue
            own = self.own.pop(v)
            self.last.pop(v, None)
            self.v_prev.pop(v, None)
            self.over.pop(v, None)
            if self.blocked(v) or v not in self.desired:
                continue
            try:
                ls.vehicle.setMaxSpeed(v, own)
            except ls.TraCIException:
                continue                     # left the network in this step
            self.n["restores"] += 1
            if abs(ls.vehicle.getMaxSpeed(v) - own) > 1e-9:
                self.n["restore_mismatch"] += 1

    def summary(self) -> dict:
        return {"setpoint": self.law.setpoint, "k_i": self.law.k_i, "b_min": self.law.b_min, "fixed_b": self.law.fixed_b,
                "zone": self.zone, "x_cmd": round(self.x_cmd, 1), "x_hold": round(self.x_hold, 1), "loop": self.loop,
                "alks_seconds": round(self.n["cmd_steps"] * STEP, 1), **self.n, "max_decel": round(self.max_decel, 3),
                "log": self.law.log}
