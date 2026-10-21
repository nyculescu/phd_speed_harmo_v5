"""P1c meter (gate §1): green 6 s, kinematic amber 5 s, red >= 2 s; c(r) = max(13, 2*4*3600 / r) with r the commanded
rate; the signal rests in green whenever r >= R_CAP; laws update every 30 s on the loop grid, from period occupancy.

Arms / plans (ids):
  c<rate>                        constant rate
  a<K_R>_<o_hat>_<e4|e5>         ALINEA: r(k) = r(k-1) + K_R (o_hat - o(k))
  p<K_P>_<K_R>_<o_hat>_<e4|e5>   PI-ALINEA: r(k) = r(k-1) - K_P (o(k) - o(k-1)) + K_R (o_hat - o(k))
o = mean over the lanes of the chosen edge of the last 30-s loop occupancy (%). r is clipped to [r_min, R_CAP].
The published forms are the standard ALINEA / PI-ALINEA ones; WP2 checks them against the papers' equations.
"""
from __future__ import annotations

from v5b.d1.meter_signal import SignalClock

GREEN, AMBER, RED_MIN = 6.0, 5.0, 2.0
C_MIN = GREEN + AMBER + RED_MIN
M_LANES = 4
R_CAP = 2.0 * M_LANES * 3600.0 / C_MIN       # about 2,215 veh/h: at or above it the meter rests in green
T_UPDATE = 30.0


def parse(pid: str) -> tuple:
    if pid.startswith("c"):
        return ("const", float(pid[1:]))
    if pid.startswith("a"):
        kr, oh, e = pid[1:].split("_")
        return ("alinea", float(kr), float(oh), e)
    if pid.startswith("p"):
        kp, kr, oh, e = pid[1:].split("_")
        return ("pi", float(kp), float(kr), float(oh), e)
    raise ValueError(pid)


def cycle_s(r: float) -> float:
    return max(C_MIN, 2.0 * M_LANES * 3600.0 / r)


class Meter:
    def __init__(self, pid: str, read_occ, set_state, r_min: float, q0: float = R_CAP):
        self.read_occ, self.set_state, self.r_min = read_occ, set_state, float(r_min)
        self.r = float(q0)
        self.o_prev = None
        self.t0 = None
        self.clock = None
        self.state = None
        self.set_plan(pid)

    def set_plan(self, pid: str) -> None:
        p = parse(pid)
        self.pid, self.law = pid, p[0]
        if p[0] == "const":
            self.r = min(max(p[1], self.r_min), R_CAP)
        elif p[0] == "alinea":
            self.K_P, self.K_R, self.o_hat, self.edge = 0.0, p[1], p[2], p[3]
        else:
            self.K_P, self.K_R, self.o_hat, self.edge = p[1], p[2], p[3], p[4]
        self.o_prev = None

    def _update(self, t: float) -> None:
        if self.law == "const":
            return
        o = self.read_occ(self.edge)
        if o is None:
            return
        do = 0.0 if self.o_prev is None else o - self.o_prev
        self.r = min(max(self.r - self.K_P * do + self.K_R * (self.o_hat - o), self.r_min), R_CAP)
        self.o_prev = o

    def step(self, t: float) -> str:
        """One 1-s tick. Returns 'G' (incl. rest), 'y' or 'r'."""
        if self.t0 is None:
            self.t0 = t
        elif (t - self.t0) % T_UPDATE < 1e-6 or T_UPDATE - (t - self.t0) % T_UPDATE < 1e-6:
            self._update(t)
        if self.r >= R_CAP - 1e-9:
            self.clock = None
            s = "G"
        else:
            if self.clock is None:
                self.clock, self.t_cyc0 = SignalClock("continuous"), t
            ph = self.clock.phase(t, self.t_cyc0, cycle_s(self.r))
            s = "G" if ph < GREEN else "y" if ph < GREEN + AMBER else "r"
        if s != self.state:
            self.set_state({"G": "GGGG", "y": "yyyy", "r": "rrrr"}[s])
        self.state = s
        return s
