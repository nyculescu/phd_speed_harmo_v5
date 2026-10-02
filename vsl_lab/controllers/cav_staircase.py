"""CAV set-speed staircase (Round 3, docs/lab/round3_tm21_protocol.md; author specification 2026-10-02).

Each CAV's ACC/CACC set speed (`vehicle.setMaxSpeed`; CAVs tracked by ID because SUMO renames the vType to
`av@<id>` after setMaxSpeed) moves toward its target in 1 km/h steps. A step is allowed only when
  * at least X s have passed since the CAV's last step, and
  * the CAV has reached its current set speed: |v - v_set| <= 0.5 km/h, or v has gone beyond v_set in the
    direction of the last change.
The vehicle's own ACC/CACC speed controller does the tracking. Targets come from the caller each step:
None = "uncontrolled" (the set speed jumps to the lane limit at once, e.g. ramp -> merge), a float = staircase
target. A CAV that was under control and gets None is released through the staircase (pre-registered).
"""
from __future__ import annotations

import libsumo as ls

STEP = 1.0 / 3.6          # 1 km/h
TOL = 0.5 / 3.6           # 'reached' tolerance


class CavStaircase:
    def __init__(self, x_s: float):
        self.x_s = float(x_s)
        self.st = {}          # vid -> {"v_set", "t_last", "dir", "controlled"}
        self.n_steps = 0
        self.max_excess = 0.0   # max (v - v_set): tracking lag of the ACC speed controller (reported)

    def depart(self, vid: str, lane_limit: float) -> None:
        ls.vehicle.setMaxSpeed(vid, lane_limit)
        self.st[vid] = {"v_set": lane_limit, "t_last": -1e9, "dir": 0, "controlled": False}

    def forget(self, vid: str) -> None:
        self.st.pop(vid, None)

    def update(self, t: float, vid: str, target: float | None, lane_limit: float) -> None:
        s = self.st.get(vid)
        if s is None:
            self.depart(vid, lane_limit)
            s = self.st[vid]
        v = ls.vehicle.getSpeed(vid)
        self.max_excess = max(self.max_excess, v - s["v_set"])
        if target is None and not s["controlled"]:
            if abs(s["v_set"] - lane_limit) > 1e-9:       # uncontrolled lane-limit change: follow at once
                s["v_set"] = lane_limit
                ls.vehicle.setMaxSpeed(vid, lane_limit)
            return
        if target is None:                                 # release through the staircase
            target = lane_limit
            if abs(s["v_set"] - lane_limit) <= 1e-9:
                s["controlled"] = False
                return
        else:
            s["controlled"] = True
        diff = target - s["v_set"]
        if abs(diff) <= 1e-9:
            return
        if t - s["t_last"] < self.x_s - 1e-9:
            return
        if s["dir"] < 0:
            reached = v <= s["v_set"] + TOL
        elif s["dir"] > 0:
            reached = v >= s["v_set"] - TOL
        else:
            reached = True
        if not reached:
            return
        d = 1 if diff > 0 else -1
        s["v_set"] += d * min(STEP, abs(diff))
        s["t_last"], s["dir"] = t, d
        ls.vehicle.setMaxSpeed(vid, s["v_set"])
        self.n_steps += 1
