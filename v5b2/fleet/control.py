"""E1 controllers on ramp32 (V213, docs/research/protocols/e1_headroom.md §3).

Meter at TLS 'rm': ALINEA at 'alinea_3' or PI-ALINEA at the drop loop, the 150-s queue law, the V190 bounds and
overrides, and a red-rest actuator (one short green per waiting vehicle, 5-s amber at metering onset and, after a
green, whenever a vehicle approaches within its stopping distance; V226). PI-ALINEA reads the 3-min mean occupancy
(V226). ALKS rule:
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
STOP_DECEL, STOP_MARGIN = 3.0, 5.0  # V228 kinematic amber: faster than 3 m/s within v²/(2·3.0) + 5 m (SUMO's
                                    # tls.yellow.min-decel; a 1-s amber inside that zone gives emergency braking)
APPROACH_SPEED, SKIP_SERVED = NEAR_SPEED, True   # who counts as approaching (V230 diagnostic varies them)
BLOCK_SPEED, BLOCK_TAIL = 2.0, 50.0
FREE_GAP = 120.0                   # m: SUMO's ACC is in speed control only beyond 120 m (MSCFModel_ACC.cpp; V220)
GAP_BINS = (100.0, 120.0, 150.0, 200.0)
RECOVERY_SPAN = 300.0              # m after release (§10.3)

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
        self.resting = True
        self.target, self.released, self.t_rel = 0.0, 0, 0.0
        self.override = self.backstop = False
        self.o_prev = None
        self.saturated = False
        self.p_red = self.p_dlim = self.p_ovr = self.p_starved = False
        self.p_rel = 0
        self.p_cmd = self.p_s = 0.0
        self.n = {"red_phases": 0, "red_passages": 0, "override_s": 0, "backstop_s": 0, "dlim_s": 0,
                  "metering_s": 0, "owed_s": 0, "owed_released": 0, "amber_kin": 0, "starved_s": 0}
        self.log = []

    def update(self, t: float, o: float, n_q: int, q_arr: float, o_raw: float | None = None) -> None:
        """o: the law's input; o_raw: the 60-s occupancy, logged for the RMS (default o)."""
        realised = self.p_rel * 60.0
        clean = self.p_red and not self.p_dlim           # §3.2: metered, no downstream-limited second
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
        elif not self.metering and self.r_law < R_MAX and (self.r_law < RESUME_MARGIN * q_arr or self.law.kind == "fixed"):
            self.metering = True
            if self.state == "G" and not self.override:
                self.state, self.t_state, self.amber = "y", t, AMBER_ONSET
                self.resting = False
            self.target = float(self.released)
        applied = self.p_cmd / self.p_s if self.p_s else None
        self.log.append((round(t), round(self.r_law, 1), round(realised, 1), round(o, 2), n_q, round(q_arr, 1),
                         int(self.metering), int(self.p_ovr), int(self.backstop), int(self.p_dlim),
                         None if applied is None else round(applied, 1), round(o if o_raw is None else o_raw, 2),
                         int(self.p_starved)))
        self.p_cmd = self.p_s = 0.0
        self.o_prev = o
        self.p_red = self.p_dlim = self.p_ovr = self.p_starved = False
        self.p_rel = 0

    def queue_check(self, occ: float) -> None:
        """Every 30 s: the V190 queue-at-ramp-start override on the ramp_q occupancy."""
        if not self.overrides:
            return
        if not self.override and occ >= OVR_ON:
            self.override = True
        elif self.override and occ < OVR_OFF:
            self.override = False

    def step(self, t: float, rel: int, n_near: int, dn_blocked: bool, longest_wait: float,
             n_close: int | None = None, approach: bool = False) -> str:
        """rel: vehicles that left 'r' during the last second, while the signal showed self.state. n_near: vehicles
        within 15 m of the line below 3 m/s (a green starts); n_close: within 15 m at any speed (it extends);
        approach: a vehicle that was not waiting at the green's start is within its stopping distance (5-s amber)."""
        n_close = n_near if n_close is None else n_close
        if rel and self.state == "r":
            self.n["red_passages"] += rel
        if rel:
            self.t_rel = t
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
            self.resting = True
            return self.state
        self.n["metering_s"] += 1
        self.r_cmd = R_MAX if self.backstop else self.r_law
        self.p_cmd += self.r_cmd
        self.p_s += 1
        self.target = min(self.target + self.r_cmd / 3600.0, self.released + OWED_CAP)
        owed = self.target - self.released
        if owed >= ONE:
            self.n["owed_s"] += 1
        el = t - self.t_state
        if self.resting:
            # leaving a rest green, also after an override, takes the onset amber (§3.2)
            self.resting = False
            if self.state == "G":
                self.amber = AMBER_ONSET
                self._set("y", t)
                return self.state
        if self.state == "G":
            if owed >= ONE and dn_blocked and t - max(self.t_state, self.t_rel) >= G_MIN - 1e-9:
                self.n["dlim_s"] += 1
                self.p_dlim = True
            if el >= G_MIN - 1e-9 and (owed < ONE or n_close == 0 or el >= G_MAX - 1e-9):
                self.amber = AMBER_ONSET if approach else AMBER_CAR
                self.n["amber_kin"] += approach
                self._set("y", t)
        elif self.state == "y":
            if el >= self.amber - 1e-9:
                self._set("r", t)
        elif owed >= ONE and n_near > 0:
            self._set("G", t)
        elif owed >= ONE:
            self.n["starved_s"] += 1             # V228: supply-limited, nobody waits at the line
            self.p_starved = True
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

    def occ60(self, group: str, n: int = 2) -> float:
        """Mean occupancy of the last n complete 30-s intervals (n = 2: 60 s)."""
        x = self.col(group, 1)[-n:]
        return sum(x) / len(x) if x else 0.0

    def flow5(self, group: str) -> float:
        """Mean flow of the last 10 intervals (5 min), veh/h."""
        x = self.col(group, 0)[-10:]
        return sum(x) / len(x) if x else 0.0


class SumoMeter:
    """Meter on TLS 'rm' and lane 'r_0': releases, waits, red exposure and the downstream test from libsumo."""

    def __init__(self, meter: Meter, bank: LoopBank, loop: str, tls: str = "rm", lane: str = "r_0",
                 window: float = 60.0):
        self.m, self.bank, self.loop, self.tls, self.lane = meter, bank, loop, tls, lane
        self.n_win = int(round(window / 30.0))
        self.served = set()
        self.len = ls.lane.getLength(lane)
        self.free = self.len / ls.lane.getMaxSpeed(lane)
        self.prev, self.enter, self.red_exp, self.left_at = set(), {}, {}, {}
        self.max_red_exposure = 0.0
        self.waits, self.red_list = [], []
        self.tail = ls.lane.getLength("3a_0") - BLOCK_TAIL
        self.exit_lanes = ["rj_0"] + [k[2] for links in ls.trafficlight.getControlledLinks(tls) for k in links if k[2]]

    def _dn_blocked(self, t: float) -> bool:
        """A vehicle below 2 m/s on rj, the meter link or the end of 3a_0; vehicles released in the last 5 s are
        still pulling away from the line and do not count."""
        if any(ls.vehicle.getSpeed(v) < BLOCK_SPEED and t - self.left_at.get(v, -1e9) >= 5.0
               for ln in self.exit_lanes for v in ls.lane.getLastStepVehicleIDs(ln)):
            return True
        return any(ls.vehicle.getLanePosition(v) >= self.tail and ls.vehicle.getSpeed(v) < BLOCK_SPEED
                   for v in ls.lane.getLastStepVehicleIDs("3a_0"))

    def step(self, t: float) -> None:
        cur = set(ls.lane.getLastStepVehicleIDs(self.lane))
        left = self.prev - cur
        for v in left:
            self.waits.append(round(t - self.enter.pop(v, t) - self.free, 1))
            self.red_list.append(self.red_exp.pop(v, 0.0))
            self.left_at[v] = t
        if len(self.left_at) > 200:
            self.left_at = {v: x for v, x in self.left_at.items() if t - x < 5.0}
        shown = self.m.state
        for v in cur:
            self.enter.setdefault(v, t)
            if shown != "G":
                self.red_exp[v] = self.red_exp.get(v, 0.0) + 1.0
                self.max_red_exposure = max(self.max_red_exposure, self.red_exp[v])
        self.prev = cur
        close = [v for v in cur if self.len - ls.vehicle.getLanePosition(v) <= NEAR_LINE]
        n_near = sum(1 for v in close if ls.vehicle.getSpeed(v) < NEAR_SPEED)
        approach = shown == "G" and any(sp > APPROACH_SPEED and self.len - ls.vehicle.getLanePosition(v)
                                        <= sp * sp / (2.0 * STOP_DECEL) + STOP_MARGIN
                                        for v in (cur - self.served if SKIP_SERVED else cur)
                                        for sp in (ls.vehicle.getSpeed(v),))
        wait = max((t - self.enter[v] - self.free for v in cur), default=0.0)
        if abs(t / 30.0 - round(t / 30.0)) < 1e-6:
            self.m.queue_check(ls.inductionloop.getLastIntervalOccupancy("ramp_q_r_0"))
        if abs(t / 60.0 - round(t / 60.0)) < 1e-6:
            self.m.update(t, self.bank.occ60(self.loop, self.n_win), len(cur), self.bank.flow5("ramp_q"),
                          self.bank.occ60(self.loop))
        s = self.m.step(t, len(left), n_near, self._dn_blocked(t) if self.m.metering else False, wait, len(close),
                        approach)
        if s == "G" and shown != "G":
            self.served = set(close)
        ls.trafficlight.setRedYellowGreenState(self.tls, s)

    def summary(self) -> dict:
        w = sorted(self.waits)
        return {**self.m.summary(), "loop": self.loop, "window": self.n_win * 30.0,
                "constants": {"STOP_DECEL": STOP_DECEL, "STOP_MARGIN": STOP_MARGIN, "AMBER_CAR": AMBER_CAR,
                              "AMBER_ONSET": AMBER_ONSET, "G_MIN": G_MIN, "G_MAX": G_MAX, "NEAR_SPEED": NEAR_SPEED,
                              "APPROACH_SPEED": APPROACH_SPEED, "SKIP_SERVED": SKIP_SERVED},
                "max_red_exposure_s": self.max_red_exposure,
                "wait_max_s": w[-1] if w else None, "wait_p95_s": w[int(0.95 * (len(w) - 1))] if w else None,
                "waits_over_240": sum(1 for x in w if x > 240.0), "n_waits": len(w), "waits": self.waits,
                "red_exposure": self.red_list}


class SumoALKS:
    """Per-step caps for the ALKS on edge 3 (V213 Q1); the law updates every 60 s."""

    def __init__(self, law: MTFC, bank: LoopBank, loop: str, zone: str, alks: set, desired: dict, blocked,
                 edge: str = "3"):
        self.law, self.bank, self.loop, self.alks, self.desired, self.blocked = law, bank, loop, alks, desired, blocked
        self.x_cmd, self.x_hold = ZONES[zone]
        self.zone, self.edge = zone, edge
        self.own, self.last, self.v_prev, self.over = {}, {}, {}, {}
        self.n = {"cmd_steps": 0, "cap_violations": 0, "restore_mismatch": 0, "allowed_mismatch": 0, "restores": 0,
                  "compliant_steps": 0}
        self.max_decel = self.max_decel_all = self.allowed_dev = 0.0
        self.at_hold = {}                  # speed minus c when first seen in the held stretch
        self.hold_free = []                # (t, speed minus c) per second in the held stretch, no leader within 120 m
        self.hold_bins = {}                # leader-gap bin -> (sum of speed minus c, seconds), report-only
        self.ever, self.released, self.recovery = set(), {}, []   # released: vid -> [odometer, gap, best ratio]

    def update(self, t: float, release: bool = True) -> float:
        return self.law.update(t, self.bank.occ60(self.loop), release)

    def step(self, t: float) -> None:
        b = self.law.b
        if b >= 1.0 and not self.own:
            if self.released and abs(t - round(t)) < 1e-6:
                self._recovery()
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
                dec = (self.v_prev[v] - sp) / STEP
                self.max_decel_all = max(self.max_decel_all, dec)
                if abs(sp - self.last.get(v, -9.0)) < 0.005:         # the cap bound this step, not a leader
                    self.max_decel = max(self.max_decel, dec)
            self.v_prev[v] = sp
            cmd = command(cap, sp, self.own[v])
            if abs(cmd - self.last.get(v, -1.0)) > 0.01:
                ls.vehicle.setMaxSpeed(v, cmd)
                self.last[v] = cmd
            self.n["cmd_steps"] += 1
            self.n["compliant_steps"] += sp <= cap + 1.0
            if x >= self.x_hold and v not in self.at_hold:
                self.at_hold[v] = sp - c
            self.ever.add(v)
            if abs(t - round(t)) < 1e-6:
                if x >= self.x_hold:
                    lead = ls.vehicle.getLeader(v, GAP_BINS[-1])
                    gap = lead[1] if lead and lead[0] else math.inf
                    if gap > FREE_GAP:
                        self.hold_free.append((round(t), round(sp - c, 3)))
                    k = sum(gap > g for g in GAP_BINS)
                    s_, n_ = self.hold_bins.get(k, (0.0, 0))
                    self.hold_bins[k] = (s_ + sp - c, n_ + 1)
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
            dev = abs(ls.vehicle.getAllowedSpeed(v) - min(own, self.desired[v]))
            self.allowed_dev = max(self.allowed_dev, dev)
            if dev > 0.01:                   # the net file rounds lane speeds to 0.01 m/s (27.78 for 100 km/h)
                self.n["allowed_mismatch"] += 1
            lead = ls.vehicle.getLeader(v, 200.0)
            self.released[v] = [ls.vehicle.getDistance(v), round(lead[1], 1) if lead and lead[0] else None, 0.0]
        if self.released and abs(t - round(t)) < 1e-6:
            self._recovery()

    def _recovery(self) -> None:
        """T0 (§10.3, V226, report-only): the best speed / desired of a released ALKS within 300 m of its release,
        with its leader gap at release."""
        for v, r in list(self.released.items()):
            try:
                d = ls.vehicle.getDistance(v) - r[0]
                r[2] = max(r[2], ls.vehicle.getSpeed(v) / self.desired[v])
            except ls.TraCIException:
                d = math.inf
            if d >= RECOVERY_SPAN:
                self.recovery.append((round(r[2], 3), r[1]))
                self.released.pop(v)

    def summary(self) -> dict:
        return {"setpoint": self.law.setpoint, "k_i": self.law.k_i, "b_min": self.law.b_min, "fixed_b": self.law.fixed_b,
                "zone": self.zone, "x_cmd": round(self.x_cmd, 1), "x_hold": round(self.x_hold, 1), "loop": self.loop,
                "constants": {"A_CAP": A_CAP, "V_ALKS": V_ALKS, "ZONE_END": ZONE_END, "FREE_GAP": FREE_GAP},
                "alks_seconds": round(self.n["cmd_steps"] * STEP, 1), **self.n, "max_decel": round(self.max_decel, 3),
                "max_decel_any_cause": round(self.max_decel_all, 3), "allowed_max_dev": round(self.allowed_dev, 4), "compliance": round(self.n["compliant_steps"] / self.n["cmd_steps"], 4) if self.n["cmd_steps"] else None,
                "hold_excess_p95": (round(float(sorted(max(0.0, x) for x in self.at_hold.values())
                                             [int(0.95 * (len(self.at_hold) - 1))]), 3) if self.at_hold else None),
                "hold_free_mean": (round(sum(x for _, x in self.hold_free) / len(self.hold_free), 3)
                                   if self.hold_free else None),
                "hold_free_n": len(self.hold_free), "hold_free": self.hold_free,
                "hold_by_gap": {f">{([0.0] + list(GAP_BINS))[k]:g} m": (round(s_ / n_, 3), n_)
                                for k, (s_, n_) in sorted(self.hold_bins.items())},
                "recovery": self.recovery, "commanded_ids": sorted(self.ever), "log": self.law.log}
