"""Courtesy-gap rule at the on-ramp merge (V194).

SUMO's LC2013 leaves some ramp vehicles stuck at the end of the acceleration lane in dense queues (V191, V193). Each
whole second, a ramp vehicle that has stood (speed < V_STOP) in the last END_WINDOW m of the acceleration lane for
WAIT s or more gets one courtesy gap: the nearest follower on the lane to its left opens a gap behind it with
libsumo's openGap. The merge itself stays SUMO's own lane change with its safety checks. All values are assumptions.
"""
from __future__ import annotations

import libsumo as ls

LANE = "3a_0"
END_WINDOW = 60.0
V_STOP = 2.0
WAIT = 10.0
GAP_TAU, GAP_SPACE, GAP_DURATION, GAP_RATE, GAP_DECEL = 1.5, 12.0, 10.0, 0.5, 2.0


class CourtesyGap:
    def __init__(self, lane_length: float):
        self.lane_length = lane_length
        self.since = {}      # ramp vehicle -> time it started waiting
        self.until = {}      # ramp vehicle -> time its current courtesy gap ends
        self.n_gaps = 0
        self.n_no_follower = 0

    def step(self, t: float) -> None:
        here = set(ls.lane.getLastStepVehicleIDs(LANE))
        for vid in list(self.since):
            if vid not in here:
                self.since.pop(vid)
                self.until.pop(vid, None)
        for vid in here:
            if ls.vehicle.getLanePosition(vid) < self.lane_length - END_WINDOW or ls.vehicle.getSpeed(vid) >= V_STOP:
                self.since.pop(vid, None)
                continue
            t0 = self.since.setdefault(vid, t)
            if t - t0 < WAIT or self.until.get(vid, -1.0) > t:
                continue
            fol = [x for x in ls.vehicle.getLeftFollowers(vid) if x[1] >= 0]   # behind it, not alongside
            if not fol:
                self.n_no_follower += 1
                continue
            f = min(fol, key=lambda x: x[1])[0]
            tau = max(GAP_TAU, 1.5 * ls.vehicle.getTau(f))       # openGap ignores a headway below the current one
            ls.vehicle.openGap(f, tau, GAP_SPACE, GAP_DURATION, GAP_RATE, GAP_DECEL, vid)
            self.until[vid] = t + GAP_DURATION
            self.n_gaps += 1
