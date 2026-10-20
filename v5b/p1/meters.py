"""P1 meters, VSL and switch schedules (page §2, §3 TV, §4, §7). Pure apart from the injectable signal / lane setters.

- PIMeter: the PI-ALINEA-style law of page §2 on the edge-4 or edge-5 count (n(k-1) at the first update = n(k): no
  proportional kick at the first update).
- ADMeter: FB with the adaptive set point of page §2. phi = vehicles that left edge 5 (= arrivals; BN4's route ends on
  edge 5) since the previous 30-s update, from the runner's cumulative arrival counter (equal to the sum of the three
  10-s runner arrival bins, since updates are on the 10-s grid). The first update has no previous (phi, n): n_hat
  does not move there.
- PostedVSL: archive apply_vsl_rates (claude/vsl-lab-core@2a79e5e vsl_lab/envs/bn4_env.py) on the gantry edges 2 and 3,
  b x 23 m/s, b clipped to [0.2, 1]; per page §3 TV it runs from onset to clearance with |delta b| <= 0.2 per 10 s:
  the first update at the onset tick, target b while the incident is on, then target 1 (ramping back up at the same
  rate) after clearance; the 23 m/s limit is restored before the drain.
- Schedules on the 1-s control tick grid t_ctrl0 + k (the tick rule of v5b/d2/incidents.Incident.tick).
- The meter signal (addendum 2026-10-19, R3; the mode is an author decision, passed explicitly, no default):
  'd2'         green iff (t - t_cycle0) mod c(q) < green, with the CURRENT c (D1/D2's FBMeter). When q changes the
               phase jumps, so greens can be skipped and a red can exceed c(q_min) - green (smoke: 322 s);
  'continuous' green iff (t - g) mod c(q) < green, where g, the anchor, is the start of the last green: when c changes,
               the time since that green start carries over (a new green starts at once if it already reaches the
               new c). With a constant c both modes give the same signal; a red is at most c(q_min) - green.
"""
from __future__ import annotations

import math

import numpy as np

from v5b.d1.episode import FBMeter
from v5b.d1.meter_signal import SIGNALS, SignalClock
from v5b.p1 import family as fam

T_CTRL0, CONTROL_S = 40.0, 900.0
REP_OFFSET = 10_000_000   # page §7: replicate k uses evaluation seed + k x 10,000,000 (SUMO and demand, A3(a))
FA_SALT = 5113            # page §4 false alarm: own salt (incident 3301; D1 2027, 4049)
FA_DURATION_S = 240.0
VSL_GANTRIES = ("2", "3")
VSL_LANES = {"2": 4, "3": 4}
VSL_SPEED = 23.0
VSL_DB, VSL_PERIOD_S, VSL_B_MIN = 0.2, 10.0, 0.2


def sgn(x: float) -> int:
    return (x > 0) - (x < 0)


class _Signal:
    def _init_signal(self, signal: str, set_state) -> None:
        if signal not in SIGNALS:
            raise ValueError(f"meter signal must be one of {SIGNALS} (no default: author decision): {signal!r}")
        self.signal = signal
        self._clock = SignalClock(signal)   # shared with D1/D2's FBMeter (V100)
        self.set_state = set_state or _default_setter()

    def _signal(self, t: float) -> None:
        phase_t = self._clock.phase(t, self.t_cycle0, self.cycle())
        self.set_state("GGGG" if phase_t < self.green else "rrrr")


def _default_setter():
    import libsumo as ls
    from v5b.d1 import plant
    return lambda s: ls.trafficlight.setRedYellowGreenState(plant.TLS_ID, s)


class FBSignalMeter(FBMeter, _Signal):
    """D1's FBMeter (constant rate: K_F = 0) with the selectable signal. The control law is FBMeter.step's, unchanged;
    with signal 'd2' the signal is FBMeter's too (tested: identical states)."""

    def __init__(self, *, signal: str, set_state=None, **kw):
        super().__init__(**kw)
        self._init_signal(signal, set_state)

    def step(self, t: float) -> None:
        if self.t_update is None:
            self.t_update, self.t_cycle0 = t, t
        if t - self.t_update >= self.T - 1e-9:
            n_hat = self.read(t)
            if n_hat is not None:
                self.q = float(np.clip(self.q + self.K_F * (self.n_crit - n_hat), self.q_min, self.q_max))
            self.t_update = t
        self._signal(t)


class PIMeter(FBMeter, _Signal):
    def __init__(self, K_P: float, K_I: float, n_crit: float, read, *, signal: str, set_state=None, **kw):
        super().__init__(K_F=K_I, n_crit=n_crit, read=read, **kw)
        self.K_P, self.K_I = float(K_P), float(K_I)
        self.n_prev = None
        self._init_signal(signal, set_state)

    def step(self, t: float) -> None:
        if self.t_update is None:
            self.t_update, self.t_cycle0 = t, t
        if t - self.t_update >= self.T - 1e-9:
            n = self.read(t)
            if n is not None:
                dn = 0.0 if self.n_prev is None else n - self.n_prev
                self.q = float(np.clip(self.q - self.K_P * dn + self.K_I * (self.n_crit - n), self.q_min, self.q_max))
                self.n_prev = n
            self.t_update = t
        self._signal(t)


class ADMeter(FBMeter, _Signal):
    def __init__(self, eta: float, K_F: float, n_crit: float, read, cum_out, *, signal: str, set_state=None, **kw):
        super().__init__(K_F=K_F, n_crit=n_crit, read=read, **kw)
        self.eta, self.n_hat0 = float(eta), float(n_crit)
        self.cum_out = cum_out
        self.cum_prev = None
        self.prev = None          # (phi, n) at the previous update
        self.nhat_log = []        # (t, n_hat) at control start and after every update
        self._init_signal(signal, set_state)

    def step(self, t: float) -> None:
        if self.t_update is None:
            self.t_update, self.t_cycle0 = t, t
            self.cum_prev = self.cum_out(t)
            self.nhat_log.append((round(t, 2), self.n_crit))
        if t - self.t_update >= self.T - 1e-9:
            n = self.read(t)
            cum = self.cum_out(t)
            phi = cum - self.cum_prev
            self.cum_prev = cum
            if n is not None:
                if self.prev is not None:
                    s = sgn(phi - self.prev[0]) * sgn(n - self.prev[1])
                    self.n_crit = float(np.clip(self.n_crit + self.eta * s, fam.AD_NHAT_MIN, fam.AD_NHAT_MAX))
                self.prev = (phi, n)
                self.q = float(np.clip(self.q + self.K_F * (self.n_crit - n), self.q_min, self.q_max))
                self.nhat_log.append((round(t, 2), self.n_crit))
            self.t_update = t
        self._signal(t)


def ad_max_dev(nhat_log, t_on, t_off) -> float:
    """T-AD: max |n_hat - n_hat(0)| over the set points in effect during [t_on, t_off) (the one in effect at t_on and
    every update before t_off). n_hat(0) = the first log entry. NaN without an incident."""
    if not nhat_log or t_on is None or t_off is None:
        return float("nan")
    n0 = nhat_log[0][1]
    at_on = [v for t, v in nhat_log if t <= t_on + 1e-9]
    vals = ([at_on[-1]] if at_on else []) + [v for t, v in nhat_log if t_on + 1e-9 < t < t_off - 1e-9]
    return float(max(abs(v - n0) for v in vals)) if vals else 0.0


class PostedVSL:
    def __init__(self, b: float, set_lane=None, get_lane=None):
        if not VSL_B_MIN <= b <= 1.0:
            raise ValueError(b)
        self.target_b, self.b = float(b), 1.0
        self.active = self.done = False
        self.next_t = None
        self.log = []   # (t, posted b)
        if set_lane is None or get_lane is None:
            import libsumo as ls
            set_lane, get_lane = ls.lane.setMaxSpeed, ls.lane.getMaxSpeed
        self.set_lane, self.get_lane = set_lane, get_lane

    def _apply(self) -> None:
        for e in VSL_GANTRIES:
            for i in range(VSL_LANES[e]):
                self.set_lane(f"{e}_{i}", self.b * VSL_SPEED)

    def tick(self, t: float, incident_on: bool) -> None:
        if self.done:
            return
        if not self.active:
            if not incident_on:
                return
            self.active, self.next_t = True, t
        if t >= self.next_t - 1e-9:
            tgt = self.target_b if incident_on else 1.0
            b = float(np.clip(tgt, self.b - VSL_DB, self.b + VSL_DB))
            self.b = round(float(np.clip(b, VSL_B_MIN, 1.0)), 9)
            self._apply()
            self.log.append((round(t, 2), self.b))
            self.next_t += VSL_PERIOD_S
            if not incident_on and self.b >= 1.0:
                self.done = True

    def restore(self) -> None:
        if self.active and self.b != 1.0:
            self.b = 1.0
            self._apply()
        self.done = True

    def assert_state(self, t: float):
        bad = [f"{e}_{i}" for e in VSL_GANTRIES for i in range(VSL_LANES[e])
               if abs(self.get_lane(f"{e}_{i}") - self.b * VSL_SPEED) > 1e-6]
        return (not bad, "H-V1", f"posted VSL b={self.b} not applied on {bad}")


# ---------------------------------------------------------------- schedules (1-s tick grid)
def first_tick(x: float, t_ctrl0: float = T_CTRL0) -> float:
    """The first control tick t_ctrl0 + k (k integer >= 0) with t >= x - 1e-9 (the Incident.tick rule)."""
    k = max(0, math.ceil(x - t_ctrl0 - 1e-9))
    return t_ctrl0 + k


def incident_ticks(onset: float, duration: float, t_ctrl0: float = T_CTRL0) -> tuple:
    return first_tick(onset, t_ctrl0), first_tick(onset + duration, t_ctrl0)


def switch_schedule(onset: float, duration: float, d: float = 0.0, c: float = 0.0, back: bool = False,
                    t_ctrl0: float = T_CTRL0, control_s: float = CONTROL_S) -> tuple:
    """(t_switch, t_back) for a plan with detection delay d and clearance detection delay c (page §4).
    The plan starts at the first tick >= t_on + d; if that is not before the clearance tick there is no switch
    (IP = N): (None, None). A back plan returns to N at the first tick >= t_off + c, or never (None) if that is past
    the last control tick (then it equals the stay plan). A stay plan never returns (c has no effect)."""
    t_on, t_off = incident_ticks(onset, duration, t_ctrl0)
    t_sw = first_tick(t_on + d, t_ctrl0)
    if t_sw >= t_off - 1e-9:
        return None, None
    if not back:
        return t_sw, None
    t_bk = first_tick(t_off + c, t_ctrl0)
    last = t_ctrl0 + control_s - 1.0
    return t_sw, (t_bk if t_bk <= last + 1e-9 else None)


def fa_window(seed: int, t_ctrl0: float = T_CTRL0, control_s: float = CONTROL_S) -> tuple:
    """False alarm (page §4): the alarm time is drawn like an onset (U over the first third of control) from its
    own stream rng(seed + FA_SALT); the plan runs for FA_DURATION_S, then N."""
    rng = np.random.default_rng(seed + FA_SALT)
    return float(rng.uniform(t_ctrl0, t_ctrl0 + control_s / 3.0)), FA_DURATION_S


def fa_schedule(seed: int, t_ctrl0: float = T_CTRL0, control_s: float = CONTROL_S) -> tuple:
    t_fa, dur = fa_window(seed, t_ctrl0, control_s)
    t_sw = first_tick(t_fa, t_ctrl0)
    return t_sw, first_tick(t_sw + dur, t_ctrl0)


def replicate_seeds(seed: int, k: int) -> dict:
    """Page §7 with A3(a): replicate k >= 1 redraws the SUMO seed AND the demand (arrival) seed, both
    seed + k x REP_OFFSET; the incident window (and a false alarm's time) always come from `seed`."""
    if k < 0:
        raise ValueError(k)
    s = seed + k * REP_OFFSET
    return {"sumo_seed": s, "demand_seed": s, "window_seed": seed}
