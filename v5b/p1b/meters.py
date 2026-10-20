"""P1b meter (docs/research/protocols/p1b_addendum.md, approved V108): amber and minimum red (B1, R2) and PI-law
plans with switch carry-over (B3, R1, R3). Pure apart from the injectable reader and signal setter.

One object runs every P1b law, so a plan can switch between laws mid-run:
- 'const' c<rate>: q = rate (P1: FBMeter with K_F = 0);
- 'fb' f<K_F>_<n_crit>: q(k) = q(k-1) + K_F (n_crit - n(k)) on the edge-4 count (P1 FB / D1 FBMeter);
- 'pi' p<K_P>_<K_I>_<n_crit>_e4|e5: q(k) = q(k-1) - K_P (n(k) - n(k-1)) + K_I (n_crit - n(k)) (P1 PIMeter);
- 'ad' ad<eta>_f<K>_<n>: FB with the adaptive set point of P1 page §2 (P1 ADMeter, unchanged rule and I3).
Every law updates on the 30-s grid anchored at the first control tick and clips q to [Q_MIN, Q_CAP] = [200, 2618]
veh/h after each update (R2, anti-windup by clipping).

Signal (B1, R2): c(q) = max(11, 2 M 3600 / q) = max(11, 28,800 / q) s; phase from P1's 'continuous' clock
(v5b/d1/meter_signal.py: the time since the last green start carries over when c changes); state G if phase < 6,
y if 6 <= phase < 9, otherwise r. Because c >= 11 > 9, a change of c never cuts an amber, and a new green can start
early only at phase >= c_new >= 11, so every red lasts >= 2 s (tested on the 1-s tick grid). The state is set every
1-s control tick (as P1).

Switches (R3): to 'const' sets q = rate; to 'fb' sets K_F, n_crit and keeps q (P1 / D2-A4 d); to 'pi' sets
K_P, K_I, n_crit and the detector edge, keeps q, and sets n(k-1) = n(k) at the plan's first update (no P kick). The
signal anchor and the 30-s update grid always carry over (same object).
"""
from __future__ import annotations

import numpy as np

from v5b.d1.meter_signal import SignalClock
from v5b.p1 import family as fam

GREEN, AMBER, RED_MIN = 6.0, 3.0, 2.0
C_MIN = GREEN + AMBER + RED_MIN          # 11 s (R2)
Q_MIN, Q_CAP = 200.0, 2618.0             # R2: every law clips q to [q_min, 2618]
M_LANES, T_UPDATE, Q0 = 4, 30.0, 1500.0
SIGNAL = "amber"                         # recorded in every run (P1's 'continuous' clock + G/y/r)
STATES = {"G": "GGGG", "y": "yyyy", "r": "rrrr"}


def cycle_s(q: float, M: int = M_LANES) -> float:
    return max(C_MIN, 2.0 * M * 3600.0 / q)


def state_of(phase: float) -> str:
    return "G" if phase < GREEN else "y" if phase < GREEN + AMBER else "r"


def _default_setter():
    import libsumo as ls
    from v5b.d1 import plant
    return lambda s: ls.trafficlight.setRedYellowGreenState(plant.TLS_ID, s)


class P1bMeter:
    def __init__(self, cid: str, read, cum_out=None, set_state=None, q0: float = Q0):
        """read(edge, t) -> vehicle count on that edge (float) or None (hold q); cum_out(t) -> cumulative arrivals
        (AD only)."""
        self.read, self.cum_out = read, cum_out
        self.set_state = set_state or _default_setter()
        self.q = float(q0)
        self.t_update = self.t_cycle0 = None
        self._clock = SignalClock("continuous")
        self.state = None
        self.law, self.cid = None, None
        self.K_F = self.K_P = self.K_I = 0.0
        self.n_crit, self.edge = 8.0, "4"
        self.n_prev = None
        self.eta = None
        self.nhat_log = None
        self.set_law(cid)
        if self.law == "ad":
            self.cum_prev, self.prev, self.nhat_log = None, None, []

    # ------------------------------------------------------------ laws and switches
    def set_law(self, cid: str) -> None:
        p = fam.parse(cid)
        if p[0] == "const":
            self.law, self.q, self.K_F, self.edge = "fb", p[1], 0.0, "4"
        elif p[0] == "fb":
            self.law, self.K_F, self.n_crit, self.edge = "fb", p[1], p[2], "4"
        elif p[0] == "pi":
            self.law, self.K_P, self.K_I, self.n_crit, self.edge = "pi", p[1], p[2], p[3], p[4]
            self.n_prev = None                     # R3: n(k-1) = n(k) at the plan's first update
        else:
            if self.law is not None:
                raise ValueError(f"AD is an always-on arm, not a plan: {cid}")
            self.law, self.eta, self.K_F, self.n_crit, self.edge = "ad", p[1], p[2], p[3], "4"
        self.cid = cid

    def _clip(self, q: float) -> float:
        return float(np.clip(q, Q_MIN, Q_CAP))

    def _update(self, t: float) -> None:
        if self.law == "ad":
            n = self.read(self.edge, t)
            cum = self.cum_out(t)
            phi = cum - self.cum_prev
            self.cum_prev = cum
            if n is not None:
                if self.prev is not None:
                    s = fam_sgn(phi - self.prev[0]) * fam_sgn(n - self.prev[1])
                    self.n_crit = float(np.clip(self.n_crit + self.eta * s, fam.AD_NHAT_MIN, fam.AD_NHAT_MAX))
                self.prev = (phi, n)
                self.q = self._clip(self.q + self.K_F * (self.n_crit - n))
                self.nhat_log.append((round(t, 2), self.n_crit))
            return
        n = self.read(self.edge, t)
        if n is None:
            return
        if self.law == "fb":
            self.q = self._clip(self.q + self.K_F * (self.n_crit - n))
        else:
            dn = 0.0 if self.n_prev is None else n - self.n_prev
            self.q = self._clip(self.q - self.K_P * dn + self.K_I * (self.n_crit - n))
            self.n_prev = n

    def cycle(self) -> float:
        return cycle_s(self.q)

    def step(self, t: float) -> str:
        """One 1-s control tick: law update on the 30-s grid, then the signal. Returns the state set ('G'/'y'/'r')."""
        if self.t_update is None:
            self.t_update, self.t_cycle0 = t, t
            if self.law == "ad":
                self.cum_prev = self.cum_out(t)
                self.nhat_log.append((round(t, 2), self.n_crit))
        if t - self.t_update >= T_UPDATE - 1e-9:
            self._update(t)
            self.t_update = t
        self.state = state_of(self._clock.phase(t, self.t_cycle0, self.cycle()))
        self.set_state(STATES[self.state])
        return self.state


def fam_sgn(x: float) -> int:
    return (x > 0) - (x < 0)
