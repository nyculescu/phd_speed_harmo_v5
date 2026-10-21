"""P1c meter (gate §1; actuator fixed in V141 after T0 failed in V140).

Release-tracking signal across all lanes of edge 2. The target cumulative release grows by r(t) dt / 3600; the
actuator counts vehicles crossing the stop line and keeps the crossings on the target:
  green (>= G_MIN) -> amber (AMBER, kinematic 5 s) once no vehicle is owed; amber -> red; red (>= R_MIN) -> green
  once at least one vehicle per lane is owed. The owed count is capped at OWE_CAP_PER_LANE per lane, so when demand is
  below r the signal simply stays green (natural rest in green); r = R_MAX means no metering.
Laws update every 30 s on the loop grid from period occupancy (ids):
  c<rate>                        constant rate
  a<K_R>_<o_hat>_<e4|e5>         ALINEA: r(k) = r(k-1) + K_R (o_hat - o(k))
  p<K_P>_<K_R>_<o_hat>_<e4|e5>   PI-ALINEA: r(k) = r(k-1) - K_P (o(k) - o(k-1)) + K_R (o_hat - o(k))
r is clipped to [r_min, R_MAX]. The laws are the standard ALINEA / PI-ALINEA forms; WP2 checks them against the papers.
"""
from __future__ import annotations

G_MIN, AMBER, R_MIN = 6.0, 5.0, 2.0
T_UPDATE = 30.0
OWE_CAP_PER_LANE = 2.0
R_MAX_PER_LANE = 2400.0


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


class Meter:
    def __init__(self, pid: str, read_occ, set_state, r_min: float, n_lanes: int):
        self.read_occ, self.set_state, self.r_min, self.n = read_occ, set_state, float(r_min), int(n_lanes)
        self.r_max = R_MAX_PER_LANE * self.n
        self.r = self.r_max
        self.o_prev = None
        self.t0 = self.t_prev = None
        self.state, self.t_state = "G", None
        self.target = None
        self.n_red = 0
        self.set_plan(pid)

    def set_plan(self, pid: str) -> None:
        p = parse(pid)
        self.pid, self.law = pid, p[0]
        if p[0] == "const":
            self.r = min(max(p[1], self.r_min), self.r_max)
        elif p[0] == "alinea":
            self.K_P, self.K_R, self.o_hat, self.edge = 0.0, p[1], p[2], p[3]
        else:
            self.K_P, self.K_R, self.o_hat, self.edge = p[1], p[2], p[3], p[4]
        self.o_prev = None

    def _update(self) -> None:
        if self.law == "const":
            return
        o = self.read_occ(self.edge)
        if o is None:
            return
        do = 0.0 if self.o_prev is None else o - self.o_prev
        self.r = min(max(self.r - self.K_P * do + self.K_R * (self.o_hat - o), self.r_min), self.r_max)
        self.o_prev = o

    def step(self, t: float, crossed: int) -> str:
        """One 1-s tick with the cumulative stop-line crossings so far. Returns 'G', 'y' or 'r'."""
        if self.t0 is None:
            self.t0 = self.t_prev = self.t_state = t
            self.target = float(crossed)
            self.set_state("G" * self.n)
        else:
            if (t - self.t0) % T_UPDATE < 1e-6 or T_UPDATE - (t - self.t0) % T_UPDATE < 1e-6:
                self._update()
            self.target += self.r * (t - self.t_prev) / 3600.0
            self.t_prev = t
        self.target = min(self.target, crossed + OWE_CAP_PER_LANE * self.n)
        owed = self.target - crossed
        el = t - self.t_state
        new = self.state
        if self.state == "G" and el >= G_MIN - 1e-9 and owed <= 0.0:
            new = "y"
        elif self.state == "y" and el >= AMBER - 1e-9:
            new = "r"
        elif self.state == "r" and el >= R_MIN - 1e-9 and owed >= self.n:
            new = "G"
        if new != self.state:
            if new == "r":
                self.n_red += 1
            self.state, self.t_state = new, t
            self.set_state(new * self.n)
        return self.state
