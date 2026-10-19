"""Screen D2 Rule 2: incidents on the BN4 bottleneck (docs/research/protocols/screen_D2_incidents.md).

Kinds come from the archive's perturbations (claude/vsl-lab-core@2a79e5e vsl_lab/envs/bn4_env.py, _perturb_tick):
- slow:  the speed limit of the final bottleneck edge 5 (1 lane; the archive's lane 5_0) drops to 5 m/s;
- block: lane 1 of the 2-lane bottleneck edge 4 (the archive's block lane 4_1) is closed to a crawl: its speed
  limit drops to BLOCK_MPS. The archive blocked it with a stopped vehicle, which caused teleports. A permission
  closure (lane.setAllowed) is not usable on this plant: lane changing is disabled for every vehicle (BN4, as in
  the paper), so the feeders 3_2 / 3_3 have no way out; a build probe on smoke seed 7,400,000 (q = 2000, NC,
  480 s) gave 54 teleports, an undrained network, and stuck vehicles even after the permission was restored.
  The crawl keeps the lane physically passable at walking pace (0 teleports in the probes, 4 smoke seeds x 2 q).
  It is NOT a closure (page Addendum D2-A2): each vehicle applies its speedFactor to BLOCK_MPS, the lane keeps
  admitting traffic, and vehicles on the lanes that feed 4_1 must cross it at a crawl (no lane changing). The
  review's probes found it more severe than a closure; a near-zero speed closure with --time-to-teleport above
  the block duration ran without teleports in those probes (an author option, not implemented).

Timing (Rule 2): onset ~ U(t_ctrl0, t_ctrl0 + control_s / 3), duration ~ U(120, 480) s, from one seeded stream
rng(seed + INCIDENT_SALT). They depend on the seed only, so every arm and both incident types of a seed share the
same window (paired). Every incident ends inside the control period (300 + 480 < 900 s).
Pure Python apart from the injectable libsumo handle `api` (tests pass a fake).
"""
from __future__ import annotations

import numpy as np

INCIDENTS = ("slow", "block")
NONE = "none"
CONDITIONS = (NONE,) + INCIDENTS
SLOW_EDGE, SLOW_LANES, SLOW_MPS = "5", ("5_0",), 5.0
BLOCK_LANE, BLOCK_MPS = "4_1", 1.0
DUR_MIN_S, DUR_MAX_S = 120.0, 480.0
INCIDENT_SALT = 3301   # independent of SUMO / demand rng(seed) and of D1's salts (2027, 4049)


def incident_window(seed: int, t_ctrl0: float, control_s: float) -> tuple:
    """(onset, duration) of this seed's incident; the same for both incident types and for every arm."""
    rng = np.random.default_rng(seed + INCIDENT_SALT)
    onset = float(rng.uniform(t_ctrl0, t_ctrl0 + control_s / 3.0))
    duration = float(rng.uniform(DUR_MIN_S, DUR_MAX_S))
    return onset, duration


class Incident:
    """kind in CONDITIONS. tick(t) is called once per 1-s control decision, before the controller acts:
    it applies the incident at the first tick t >= onset ('on') and removes it at the first tick
    t >= onset + duration ('off'), restoring the speed limits read just before it was applied."""

    def __init__(self, kind: str, onset: float, duration: float, api=None):
        if kind not in CONDITIONS:
            raise ValueError(kind)
        self.kind, self.onset, self.duration = kind, float(onset), float(duration)
        self.api = api
        self.on = self.done = False
        self.t_on = self.t_off = None
        self.saved = {}
        self.log = []   # (t, 'on' | 'off', {lane: max speed read back after the change})

    @property
    def lanes(self) -> tuple:
        return SLOW_LANES if self.kind == "slow" else (BLOCK_LANE,) if self.kind == "block" else ()

    def _read(self) -> dict:
        return {ln: float(self.api.lane.getMaxSpeed(ln)) for ln in self.lanes}

    def _apply(self) -> None:
        self.saved = self._read()
        if self.kind == "slow":
            self.api.edge.setMaxSpeed(SLOW_EDGE, SLOW_MPS)
        else:
            self.api.lane.setMaxSpeed(BLOCK_LANE, BLOCK_MPS)

    def _remove(self) -> None:
        for ln, v in self.saved.items():
            self.api.lane.setMaxSpeed(ln, v)

    def tick(self, t: float):
        if self.kind == NONE or self.done:
            return None
        if not self.on and t >= self.onset - 1e-9:
            self._apply()
            self.on, self.t_on = True, float(t)
            self.log.append((round(t, 2), "on", self._read()))
            return "on"
        if self.on and t >= self.onset + self.duration - 1e-9:
            return self.clear(t)
        return None

    def clear(self, t: float):
        """Remove the incident now if it is on (also used before the drain as a safety net)."""
        if not self.on:
            return None
        self._remove()
        self.on, self.done, self.t_off = False, True, float(t)
        self.log.append((round(t, 2), "off", self._read()))
        return "off"

    def expected(self) -> dict:
        """Speed limit each incident lane must have right now (health assertion H-I1)."""
        if self.on:
            return {ln: (SLOW_MPS if self.kind == "slow" else BLOCK_MPS) for ln in self.lanes}
        return dict(self.saved)

    def assert_state(self, t: float):
        """SumoSim checkpoint assertion: (ok, code, message)."""
        exp = self.expected()
        got = self._read() if exp else {}
        bad = {ln: (got[ln], v) for ln, v in exp.items() if abs(got[ln] - v) > 1e-6}
        return (not bad, "H-I1", f"incident {self.kind} lane speeds (got, expected) {bad}")
