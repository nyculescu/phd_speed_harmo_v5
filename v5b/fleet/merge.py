"""Rules for ramp vehicles stuck at the end of the acceleration lane (V191, V193): courtesy gap (V194, failed) and
squeeze-in (V196), plus wait counters.

SUMO's LC2013 leaves some ramp vehicles stuck there in dense queues. A ramp vehicle waits while it stands
(speed < V_STOP) in the last END_WINDOW m of the acceleration lane. All values are assumptions.
"""
from __future__ import annotations

import libsumo as ls

LANE = "3a_0"
END_WINDOW = 60.0
V_STOP = 2.0
WAIT = 10.0
GAP_TAU, GAP_SPACE, GAP_DURATION, GAP_RATE, GAP_DECEL = 1.5, 12.0, 10.0, 0.5, 2.0


class CourtesyGap:
    """Each whole second, a vehicle waiting WAIT s or more gets one courtesy gap: its nearest left follower opens a gap
    behind it with libsumo's openGap. The merge stays SUMO's own lane change with its safety checks."""

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


SQ_V_CRAWL = 3.0
SQ_HOLD = 2.0
TRACI_GAPS = 0b1100000000   # lane-change mode bits 8-9: how TraCI lane-change requests treat other vehicles
TRACI_NO_OVERLAP = 0b0100000000


class RampMerge:
    """Wait counters for the acceleration lane and, with squeeze=True, the squeeze-in rule (V196).

    Squeeze-in, checked each whole second: a vehicle waiting WAIT s or more changes to the lane on its left with SUMO's
    safe-gap check skipped (TraCI requests only avoid overlaps) when the left follower crawls (< SQ_V_CRAWL) and the
    vehicle fits where it stands: its own minGap clear ahead, and behind it the follower's minGap plus the follower's
    stopping distance at its normal deceleration, so the follower needs no emergency braking. libsumo neighbour
    distances already exclude the minGap, so these are d >= 0 ahead and d >= stopping distance behind.
    """

    def __init__(self, lane_length: float, squeeze: bool = False):
        self.lane_length = lane_length
        self.squeeze = squeeze
        self.since = {}
        self.wait = {}       # vehicle -> longest wait so far
        self.pending = {}    # squeezing vehicle -> (saved lane-change mode, request end)
        self.n_squeeze = self.n_failed = 0

    def _fits(self, vid: str) -> bool:
        if any(d < 0 for _, d in ls.vehicle.getLeftLeaders(vid)):
            return False
        for f, d in ls.vehicle.getLeftFollowers(vid):
            v = ls.vehicle.getSpeed(f)
            if v >= SQ_V_CRAWL or d < v * v / (2 * ls.vehicle.getDecel(f)):
                return False
        return True

    def step(self, t: float, skip=lambda vid: False) -> None:
        here = set(ls.lane.getLastStepVehicleIDs(LANE))
        for vid, (mode, t_end) in list(self.pending.items()):
            if vid in here and t < t_end:
                continue
            if vid in here:
                self.n_failed += 1
            if not skip(vid) and vid in ls.vehicle.getIDList():
                ls.vehicle.setLaneChangeMode(vid, mode)
            self.pending.pop(vid)
        for vid in list(self.since):
            if vid not in here:
                self.since.pop(vid)
        for vid in here:
            if ls.vehicle.getLanePosition(vid) < self.lane_length - END_WINDOW or ls.vehicle.getSpeed(vid) >= V_STOP:
                self.since.pop(vid, None)
                continue
            t0 = self.since.setdefault(vid, t)
            self.wait[vid] = max(self.wait.get(vid, 0.0), t - t0)
            if not self.squeeze or t - t0 < WAIT or vid in self.pending or skip(vid) or not self._fits(vid):
                continue
            mode = ls.vehicle.getLaneChangeMode(vid)
            ls.vehicle.setLaneChangeMode(vid, mode & ~TRACI_GAPS | TRACI_NO_OVERLAP)
            ls.vehicle.changeLane(vid, ls.vehicle.getLaneIndex(vid) + 1, SQ_HOLD)
            self.pending[vid] = (mode, t + SQ_HOLD)
            self.n_squeeze += 1

    def summary(self) -> dict:
        w = list(self.wait.values())
        return {"waits_over_s": {str(x): sum(v > x for v in w) for x in (10, 60, 300)},
                "wait_max_s": max(w, default=0.0), "squeezes": self.n_squeeze if self.squeeze else None,
                "squeezes_failed": self.n_failed if self.squeeze else None}
