"""Merge V&V instruments (V532, docs/research/protocols/merge_vv.md §2). Read only: getters, never a setter or an env method that
writes state (V386). Every output key starts with "vv_"; a run with none of the flags is unchanged.

cfg flags: vv_count (main-lane count, encounters), vv_trace (every counted close-following sample), vv_log (merges and lane-end
standing, to a side file), vv_meter (TTC below 3 s every 0.1-s step), vv_obs (the policy's position inputs on 3a and 4a stay in the
300-m training range; how often column 15 sits at its cap).
"""
from __future__ import annotations

import gzip
import json
from collections import Counter, defaultdict, deque
from pathlib import Path

ACC = ("3a_0", "4a_0")
NOT_MAIN_LANES = set(ACC)
RAMP_ROADS = {"r", "rj", "r2", "rj2"}
FEED = {"3a_0": ("r_0", "rj_0", "3a_0"), "4a_0": ("r2_0", "rj2_0", "4a_0")}
HIST_S = 10.0
TRAIN_LEN_OF = {"3a": 294.72, "4a": 294.72}     # as b_env.TRAIN_LEN
FLAGS = ("vv_count", "vv_trace", "vv_log", "vv_meter", "vv_obs")


def wanted(c: dict) -> bool:
    return any(c.get(k) for k in FLAGS)


def is_main(lane: str, road: str) -> bool:
    """The main-lane count's rule: the follower is on neither acceleration lane nor a ramp road."""
    return lane not in NOT_MAIN_LANES and road not in RAMP_ROADS


def encounter_new(last: dict, pair: tuple, t: float) -> bool:
    """One encounter = consecutive 1-Hz samples of the same follower-leader pair."""
    new = abs(last.get(pair, -99.0) - (t - 1.0)) > 1e-6
    last[pair] = t
    return new


class VV:
    def __init__(self, ls, c: dict, alks: set, trucks: set, side: Path | None):
        self.ls, self.alks, self.trucks, self.side = ls, alks, trucks, side
        self.count = bool(c.get("vv_count") or c.get("vv_trace"))
        self.trace = [] if c.get("vv_trace") else None
        self.log = bool(c.get("vv_log"))
        self.meter = bool(c.get("vv_meter"))
        self.obs = bool(c.get("vv_obs"))
        self.S = defaultdict(float)
        self.last_pair = {}
        self.merges, self.stand = [], {x: Counter() for x in ACC}
        self.prev = {x: {} for x in ACC}     # vehicle -> lane position at the last step on that acceleration lane
        self.hist = defaultdict(deque)       # vehicle -> (t, speed) over the last 10 s on its ramp and acceleration lane
        self.lanes = {x: ls.lane.getLength(x) for x in ls.lane.getIDList() if not x.startswith(":")}     # T0: every built lane

    def kind(self, v: str) -> str:
        return "alks" if v in self.alks else "truck" if v in self.trucks else "car"

    def hit(self, t: float, v: str, lead: tuple, s: float, sl: float, gap: float, road: str) -> None:
        """One counted 1-Hz sample of TTC below 3 s (plant_sweep conflicts(): follower v, leader lead[0], gap with minGap)."""
        if not self.count:
            return
        ls = self.ls
        lane = ls.vehicle.getLaneID(v)
        self.S["vv_ttc3_main"] += is_main(lane, road)
        self.S["vv_enc"] += encounter_new(self.last_pair, (v, lead[0]), t)
        if self.trace is not None:
            w = lead[0]
            self.trace.append([round(t, 3), v, w, self.kind(v), self.kind(w), road, lane, ls.vehicle.getLanePosition(v), ls.vehicle.getLength(v),
                               ls.vehicle.getRoadID(w), ls.vehicle.getLaneID(w), ls.vehicle.getLanePosition(w), ls.vehicle.getLength(w),
                               lead[1], ls.vehicle.getMinGap(v), s, sl])

    def step(self, t: float, warm: bool) -> None:
        """Every 0.1-s step: merges off both acceleration lanes, the speed history for 'minimum speed before'."""
        if not self.log or not warm:
            return
        ls = self.ls
        for x in ACC:
            for e in FEED[x]:
                for v in ls.lane.getLastStepVehicleIDs(e):
                    h = self.hist[v]
                    h.append((t, ls.vehicle.getSpeed(v)))
                    while h and h[0][0] < t - HIST_S - 1e-9:
                        h.popleft()
            now = {v: ls.vehicle.getLanePosition(v) for v in ls.lane.getLastStepVehicleIDs(x)}
            for v, p0 in self.prev[x].items():
                if v not in now:
                    self._merge(t, v, x, p0)
            self.prev[x] = now

    def _merge(self, t: float, v: str, x: str, p0: float) -> None:
        ls = self.ls
        try:
            lane = ls.vehicle.getLaneID(v)
        except Exception:     # left the network between steps
            self.S["vv_merge_gone"] += 1
            return
        if lane != x[:-1] + "1":
            self.S["vv_merge_other"] += 1
            return
        s, p, L = ls.vehicle.getSpeed(v), ls.vehicle.getLanePosition(v), ls.vehicle.getLength(v)
        rec = {"t": round(t, 2), "v": v, "type": self.kind(v), "lane0": x, "pos0": p0, "pos": p, "speed": s,
               "min_speed_10s": min((u for _, u in self.hist.get(v, ())), default=s)}
        for side, f in (("lead", ls.vehicle.getLeader(v, 200.0)), ("lag", ls.vehicle.getFollower(v, 200.0))):
            if f and f[0]:
                w = f[0]
                same = ls.vehicle.getLaneID(w) == lane
                pw = ls.vehicle.getLanePosition(w)
                net = (pw - ls.vehicle.getLength(w) - p) if side == "lead" else (p - L - pw)
                rec[side] = {"v": w, "type": self.kind(w), "speed": ls.vehicle.getSpeed(w), "sumo_dist": f[1], "same_lane": same,
                             "net_gap": net if same else None}
        self.merges.append(rec)
        self.S["vv_merges"] += 1
        self.hist.pop(v, None)

    def second(self, t: float, lanes: set) -> None:
        """At the moment plant_sweep counts end_stop/end_stop2: the same rule, per vehicle."""
        if not self.log:
            return
        ls = self.ls
        for x in ACC:
            if x not in lanes:
                continue
            L = ls.lane.getLength(x)
            for v in ls.lane.getLastStepVehicleIDs(x):
                if ls.vehicle.getSpeed(v) < 1.0 and ls.vehicle.getLanePosition(v) > L - 30.0:
                    self.stand[x][v] += 1

    def meter_step(self, t: float, v: str, s: float) -> None:
        """TTC below 3 s at one 0.1-s step, with the counter's definition (SUMO gap + minGap, closing only)."""
        ls = self.ls
        lead = ls.vehicle.getLeader(v, 200.0)
        if not (lead and lead[0]):
            return
        dv = s - ls.vehicle.getSpeed(lead[0])
        if dv > 0 and (lead[1] + ls.vehicle.getMinGap(v)) / dv < 3.0:
            self.S["vv_m_step"] += 1
            frac = t % 1.0
            if frac < 1e-6 or frac > 1.0 - 1e-6:
                self.S["vv_m_whole"] += 1
            elif abs(frac - 0.5) < 1e-6:
                self.S["vv_m_half"] += 1

    def obs_check(self, o, env) -> None:
        """After each decision: env.xlast holds the position the policy just read (a read; nothing is written)."""
        if not self.obs or not (isinstance(o, tuple) and len(o) == 4):
            return
        ls = self.ls
        ids, rows = o[0], o[1]
        train = env._x_base(train=True)     # fills a cache from TRAIN_LEN and lane lengths; no traffic state
        for i, v in enumerate(ids):
            e = ls.vehicle.getRoadID(v)
            if e in ("3a", "4a"):
                x = env.xlast.get(v)
                self.S["vv_x_acc_n"] += 1
                self.S["vv_x_out"] += x is None or not (train[e] - 1e-6 <= x <= train[e] + TRAIN_LEN_OF[e] + 1e-6)
            self.S["vv_c15_n"] += 1
            self.S["vv_c15_cap"] += bool(rows[i][15] >= 1.0)

    def finish(self, tag: str) -> dict:
        row = dict(self.S) | {"vv_lanes": self.lanes}
        if self.meter:
            row["vv_m_time"] = self.S.get("vv_m_step", 0.0) * 0.1     # vehicle-seconds at 0.1 s
        if self.trace is not None:
            row["vv_trace"] = self.trace
        if self.log:
            row["vv_stand_n"] = {x: len(c) for x, c in self.stand.items()}
            row["vv_stand_s"] = {x: sum(c.values()) for x, c in self.stand.items()}
            if self.side is not None:
                self.side.mkdir(parents=True, exist_ok=True)
                f = self.side / f"{tag}.json.gz"
                with gzip.open(f, "wt") as w:
                    json.dump({"merges": self.merges, "stand": {x: dict(c) for x, c in self.stand.items()}}, w)
                row["vv_log_file"] = f.name
            else:
                row["vv_merges_log"] = self.merges
        return row
