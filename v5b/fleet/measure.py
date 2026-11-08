"""Report-only measurement pack (round 2, V468): speed and acceleration distributions, braking events and cascades, fuel by
vehicle class, merge bottlenecks and a space-time speed field for wave metrics. It only reads the simulation (libsumo getters),
so a run with the pack on must reproduce the run without it on every stored key; `docs/research/round2/measure2.py smoke` checks that.

Time window: after the warm-up, as every other counter. Vehicle classes: "car" (human-driven), "alks" (automated car), "truck".
Cars and ALKS use SUMO's default HBEFA4 petrol Euro-4 class; trucks use the default diesel articulated Euro VI class.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import numpy as np

CLASSES = ("car", "alks", "truck")
V_BIN, V_N = 5.0, 30     # km/h; the last bin holds 145 km/h and above
A_MIN, A_BIN, A_N = -10.0, 0.5, 30     # m/s²: bins from -10 to +5; values outside go to the end bins
PEAK_EDGES = (-3.0, -3.5, -4.0, -4.5, -5.0, -6.0, -7.0, -8.0, -9.0, -100.0)     # braking event peak decelerations, m/s²
DUR_EDGES = (0.0, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 1e9)     # braking event durations, s
BRAKE = -3.0     # m/s², as b3_step
CASCADE_S = 3.0     # a follower's braking event that starts within this many seconds after its leader's started
ST_DT, ST_DX = 10.0, 50.0     # space-time cells: 10 s by 50 m along the mainline, all lanes pooled
MAIN, RAMPS = "main", {"ramp1": ("r", "rj"), "ramp2": ("r2", "rj2")}
MERGES = {"m1": ("3a", "3"), "m2": ("4a", "4")}     # acceleration section, the road after it
MERGE_UP = {"m1": "2", "m2": "3"}     # the mainline road before each acceleration section
QUEUE_V = 1.0     # m/s: a ramp vehicle below this speed is queued


def v_bin(s: float) -> int:
    return min(int(s * 3.6 / V_BIN), V_N - 1)


def a_bin(a: float) -> int:
    return min(max(int((a - A_MIN) / A_BIN), 0), A_N - 1)


def bin_of(x: float, edges: tuple) -> int:
    """Index of the interval of `edges` (increasing or decreasing) that holds x."""
    inc = edges[1] > edges[0]
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if (lo <= x < hi) if inc else (hi < x <= lo):
            return i
    return len(edges) - 2


def offsets(route_edges: str, length) -> dict:
    """Start of each mainline edge along the corridor, from its lane-0 length; junction lengths are left out."""
    out, x = {}, 0.0
    for e in route_edges.split():
        out[e] = x
        x += length(e)
    out["_end"] = x
    return out


class Measure:
    def __init__(self, env, trucks: set, routes: dict, length, dt: float):
        self.env, self.trucks, self.dt = env, trucks, dt
        self.alks = env.alks_all
        self.off = offsets(routes[MAIN][0], length)
        self.len = {e: length(e) for e in ("3a", "4a")}
        self.t0, self.t_end = env.warm, env.t_end
        nt = int(np.ceil((self.t_end - self.t0) / ST_DT))
        nx = int(np.ceil(self.off["_end"] / ST_DX))
        self.st = np.zeros((2, nt, nx))     # speed sum (m/s) and vehicle-seconds per cell, 1-Hz samples
        self.vh = {c: np.zeros(V_N, np.int64) for c in CLASSES}     # vehicle-steps per speed bin
        self.ah = {c: np.zeros(A_N, np.int64) for c in CLASSES}     # vehicle-steps per acceleration bin
        self.fuel = defaultdict(float)     # mg, integrated per step
        self.dist = defaultdict(float)     # m, integrated per step
        self.a2 = defaultdict(float)     # sum of a² per vehicle-step
        self.n = defaultdict(int)     # vehicle-steps
        self.ev = {}     # vehicle -> [start time, peak, last braking step] of an open braking event
        self.started = {}     # vehicle -> start time of its latest braking event
        self.peak = {c: np.zeros(len(PEAK_EDGES) - 1, np.int64) for c in CLASSES}
        self.dur = {c: np.zeros(len(DUR_EDGES) - 1, np.int64) for c in CLASSES}
        self.events = defaultdict(int)
        self.event_s = defaultdict(float)
        self.cascade = defaultdict(int)
        self.road = {}     # vehicle -> last non-internal road (1 Hz)
        self.lane = {}     # vehicle -> last lane id and position (1 Hz)
        nm = int(np.ceil((self.t_end - self.t0) / 60.0))
        self.minute = {k: np.zeros(nm) for k in ("m1_out", "m2_out", "m1_ramp_in", "m2_ramp_in", "m1_main_in", "m2_main_in")}
        for m, (acc, _) in MERGES.items():
            for part in ("acc", "up"):
                self.minute[f"{m}_{part}_vs"] = np.zeros(nm)     # speed sum, m/s
                self.minute[f"{m}_{part}_n"] = np.zeros(nm)     # vehicle-seconds
        for r in RAMPS:
            self.minute[f"{r}_queue"] = np.zeros(nm)     # queued vehicle-seconds on the ramp
            self.minute[f"{r}_pending"] = np.zeros(nm)     # vehicle-seconds waiting to be inserted
        self.merge_pos = {m: np.zeros(10, np.int64) for m in MERGES}     # where on the acceleration lane a vehicle left lane 0
        self.route = {v.vid: r for v, r in zip(env.dem.veh, env.dem.route_of)}

    def cls(self, v: str) -> str:
        return "truck" if v in self.trucks else "alks" if v in self.alks else "car"

    def vehicle_step(self, ls, v: str, a: float, s: float, f: float, t: float) -> None:
        """Every simulation step, for every vehicle; a, s and f are the values the plant has just read."""
        c = self.cls(v)
        self.vh[c][v_bin(s)] += 1
        self.ah[c][a_bin(a)] += 1
        self.fuel[c] += f * self.dt
        self.dist[c] += s * self.dt
        self.a2[c] += a * a
        self.n[c] += 1
        e = self.ev.get(v)
        if a <= BRAKE:
            if e is None:
                self.ev[v] = [t, a, t]
                lead = ls.vehicle.getLeader(v, 200.0)
                if lead and lead[0]:
                    t_l = self.started.get(lead[0])
                    if t_l is not None and 0.0 <= t - t_l <= CASCADE_S:
                        self.cascade[c] += 1
                self.started[v] = t
            else:
                e[1], e[2] = min(e[1], a), t
        elif e is not None:
            self._close(v, c)

    def _close(self, v: str, c: str) -> None:
        """Duration = braking steps x dt, so the durations add up to b3_step even when a vehicle leaves mid-event."""
        t0, pk, t1 = self.ev.pop(v)
        d = t1 - t0 + self.dt
        self.peak[c][bin_of(pk, PEAK_EDGES)] += 1
        self.dur[c][bin_of(d, DUR_EDGES)] += 1
        self.events[c] += 1
        self.event_s[c] += d

    def second(self, ls, t: float) -> None:
        """Every simulated second after the warm-up."""
        k = int((t - self.t0 - 1e-9) // ST_DT)
        m = int((t - self.t0 - 1e-9) // 60.0)
        if not (0 <= k < self.st.shape[1]):
            return
        for v in ls.vehicle.getIDList():
            road = ls.vehicle.getRoadID(v)
            s = ls.vehicle.getSpeed(v)
            if road.startswith(":"):
                continue
            x = ls.vehicle.getLanePosition(v)
            lane = ls.vehicle.getLaneID(v)
            o = self.off.get(road)
            if o is not None:
                j = min(int((o + x) // ST_DX), self.st.shape[2] - 1)
                self.st[0, k, j] += s
                self.st[1, k, j] += 1
            prev = self.road.get(v)
            if prev is not None and prev != road:
                for mg, (acc, after) in MERGES.items():
                    if prev == acc and road == after:
                        self.minute[f"{mg}_out"][m] += 1
                    if road == acc:
                        self.minute[f"{mg}_{'main' if prev == MERGE_UP[mg] else 'ramp'}_in"][m] += 1
            pl = self.lane.get(v)
            if pl is not None and pl[0] != lane:
                for mg, (acc, _) in MERGES.items():
                    if pl[0] == f"{acc}_0":
                        self.merge_pos[mg][min(int(10.0 * pl[1] / self.len[acc]), 9)] += 1
            self.road[v], self.lane[v] = road, (lane, x)
            for mg, (acc, _) in MERGES.items():
                for part, edge in (("acc", acc), ("up", MERGE_UP[mg])):
                    if road == edge:
                        self.minute[f"{mg}_{part}_vs"][m] += s
                        self.minute[f"{mg}_{part}_n"][m] += 1
            for r, edges in RAMPS.items():
                if road in edges and s < QUEUE_V:
                    self.minute[f"{r}_queue"][m] += 1
        for v in ls.simulation.getPendingVehicles():
            r = self.route.get(v)
            if r in ("ramp", "ramp2"):
                self.minute[f"{'ramp1' if r == 'ramp' else 'ramp2'}_pending"][m] += 1

    def finish(self, t: float, out: Path | None, key: str) -> dict:
        """Scalars and short histograms for the row; the space-time field and minute series go to a side file."""
        for v in list(self.ev):
            self._close(v, self.cls(v))
        row = {}
        for c in CLASSES:
            row[f"m_vh_{c}"] = self.vh[c].tolist()
            row[f"m_ah_{c}"] = self.ah[c].tolist()
            row[f"m_peak_{c}"] = self.peak[c].tolist()
            row[f"m_dur_{c}"] = self.dur[c].tolist()
            row[f"m_fuel_mg_{c}"] = self.fuel[c]
            row[f"m_dist_m_{c}"] = self.dist[c]
            row[f"m_a2_{c}"] = self.a2[c]
            row[f"m_n_{c}"] = self.n[c]
            row[f"m_events_{c}"] = self.events[c]
            row[f"m_event_s_{c}"] = self.event_s[c]
            row[f"m_cascade_{c}"] = self.cascade[c]
        for mg in MERGES:
            row[f"m_mergepos_{mg}"] = self.merge_pos[mg].tolist()
        row["m_minute"] = {k: np.round(x, 3).tolist() for k, x in self.minute.items()}
        row["m_st_shape"] = list(self.st.shape[1:])
        row["m_st_dx"], row["m_st_dt"] = ST_DX, ST_DT
        row["m_offsets"] = self.off
        if out is not None:
            out.mkdir(parents=True, exist_ok=True)
            f = out / f"{key}.npz"
            np.savez_compressed(f, v=self.st[0].astype(np.float32), n=self.st[1].astype(np.float32))
            row["m_st_file"] = f.name
        return row


# Derived metrics, computed from the stored pack after the runs (no simulation).
JAM_KMH, CONGESTED_KMH = 30.0, 60.0     # space-time cell speeds: jammed below 30 km/h, congested below 60 km/h
MIN_CLUSTER = 3     # cells; smaller jam clusters are noise
OSC_COVER = 0.8     # a station enters the oscillation metric if it is occupied in at least this share of time bins
BREAK_MIN = 2     # minutes below CONGESTED_KMH on the acceleration section that make a breakdown, and above it a recovery
PETROL_G_PER_L, DIESEL_G_PER_L = 745.0, 835.0     # typical fuel densities [VERIFY], used only to print L/100 km


def quantiles(counts, lo: float, width: float, qs=(0.05, 0.25, 0.5, 0.75, 0.95)) -> list:
    """Quantiles of a binned distribution (bins of `width` from `lo`), interpolated linearly inside a bin."""
    c = np.asarray(counts, float)
    tot = c.sum()
    if tot <= 0:
        return [None] * len(qs)
    cum = np.cumsum(c) / tot
    out = []
    for q in qs:
        i = int(np.searchsorted(cum, q))
        prev = cum[i - 1] if i else 0.0
        frac = (q - prev) / max(cum[i] - prev, 1e-12)
        out.append(lo + width * (i + frac))
    return out


def speed_field(v_sum, n) -> np.ndarray:
    """Cell mean speed in km/h; NaN where no vehicle was sampled."""
    v_sum, n = np.asarray(v_sum, float), np.asarray(n, float)
    out = np.full(v_sum.shape, np.nan)
    m = n > 0
    out[m] = 3.6 * v_sum[m] / n[m]
    return out


def waves(v_sum, n, dt: float = ST_DT, dx: float = ST_DX) -> dict:
    """Wave metrics of one run from its space-time field (time bins x space bins).
    - jam_share, congested_share: vehicle-weighted share of sampled vehicle-seconds in cells below 30 and 60 km/h;
    - jams: 8-connected clusters of jammed cells (at least MIN_CLUSTER cells), with each one's duration, extent and the
      speed of its upstream front (linear fit of the front position over time; negative = moving upstream, km/h);
    - congested_km: congested length per time bin (cells below 60 km/h x dx), its mean and maximum;
    - osc_kmh: the temporal standard deviation of cell speed at each well-covered station, averaged over stations."""
    from scipy import ndimage
    V = speed_field(v_sum, n)
    n = np.asarray(n, float)
    occ = ~np.isnan(V)
    w = n.sum()
    jam = occ & (V < JAM_KMH)
    cong = occ & (V < CONGESTED_KMH)
    lab, k = ndimage.label(jam, structure=np.ones((3, 3)))
    clusters = []
    for i in range(1, k + 1):
        ti, xi = np.nonzero(lab == i)
        if len(ti) < MIN_CLUSTER:
            continue
        ts = np.unique(ti)
        front = np.array([xi[ti == t].min() for t in ts]) * dx
        speed = float(np.polyfit(ts * dt, front, 1)[0] * 3.6) if len(ts) >= 3 else None
        clusters.append({"duration_s": float((ts.max() - ts.min() + 1) * dt), "extent_m": float((xi.max() - xi.min() + 1) * dx),
                         "cells": int(len(ti)), "front_kmh": speed})
    cov = occ.mean(axis=0) >= OSC_COVER
    osc = [float(np.nanstd(V[:, j])) for j in np.nonzero(cov)[0]]
    ckm = cong.sum(axis=1) * dx / 1000.0
    return {"jam_share": float(n[jam].sum() / w) if w else None, "congested_share": float(n[cong].sum() / w) if w else None,
            "jams": len(clusters), "jam_clusters": clusters,
            "front_kmh_median": float(np.median([c["front_kmh"] for c in clusters if c["front_kmh"] is not None])) if any(c["front_kmh"] is not None for c in clusters) else None,
            "congested_km_mean": float(ckm.mean()), "congested_km_max": float(ckm.max()),
            "osc_kmh": float(np.mean(osc)) if osc else None, "osc_stations": len(osc)}


def breakdown(out_per_min, vs_per_min, n_per_min) -> dict:
    """One merge: the first minute its acceleration section averages below 60 km/h for BREAK_MIN minutes in a row; the best
    5-minute discharge before it; the mean discharge from it to the recovery (BREAK_MIN minutes back above 60 km/h) or the
    run's end; the capacity drop between the two (%). Flows in veh/h. No breakdown: only the overall discharge."""
    q = np.asarray(out_per_min, float) * 60.0
    n = np.asarray(n_per_min, float)
    v = np.where(n > 0, 3.6 * np.asarray(vs_per_min, float) / np.maximum(n, 1.0), np.nan)
    slow = (v < CONGESTED_KMH) & ~np.isnan(v)
    res = {"flow_mean": float(q.mean()), "breakdown_min": None, "recovery_min": None, "pre_q5max": None, "discharge": None, "drop_pct": None,
           "slow_minutes": int(slow.sum())}
    b = next((i for i in range(len(slow) - BREAK_MIN + 1) if slow[i:i + BREAK_MIN].all()), None)
    if b is None:
        return res
    r = next((i for i in range(b + BREAK_MIN, len(slow) - BREAK_MIN + 1) if not slow[i:i + BREAK_MIN].any()), None)
    res["breakdown_min"], res["recovery_min"] = b, r
    if b >= 5:
        res["pre_q5max"] = float(max(q[i:i + 5].mean() for i in range(b - 4)))
    res["discharge"] = float(q[b:(r if r is not None else len(q))].mean())
    if res["pre_q5max"]:
        res["drop_pct"] = 100.0 * (res["pre_q5max"] - res["discharge"]) / res["pre_q5max"]
    return res


def summary(row: dict, field: dict | None = None) -> dict:
    """Per-run report metrics from a row with the pack (and its space-time field, if loaded)."""
    out = {}
    for c in CLASSES:
        n = row[f"m_n_{c}"]
        out[f"v_q_{c}"] = quantiles(row[f"m_vh_{c}"], 0.0, V_BIN)
        out[f"a_q_{c}"] = quantiles(row[f"m_ah_{c}"], A_MIN, A_BIN)
        out[f"a_rms_{c}"] = float(np.sqrt(row[f"m_a2_{c}"] / n)) if n else None
        out[f"fuel_g_km_{c}"] = row[f"m_fuel_mg_{c}"] / row[f"m_dist_m_{c}"] if row[f"m_dist_m_{c}"] else None     # mg/m = g/km
        out[f"events_{c}"] = row[f"m_events_{c}"]
        out[f"cascade_share_{c}"] = row[f"m_cascade_{c}"] / row[f"m_events_{c}"] if row[f"m_events_{c}"] else None
        pk = np.asarray(row[f"m_peak_{c}"])
        out[f"events_ge45_{c}"] = int(pk[3:].sum())     # peak at or beyond -4.5 m/s²
        out[f"events_ge7_{c}"] = int(pk[6:].sum())
    cars = ("car", "alks")
    dist = sum(row[f"m_dist_m_{c}"] for c in cars)
    out["fuel_petrol_g_km"] = sum(row[f"m_fuel_mg_{c}"] for c in cars) / dist if dist else None
    out["fuel_petrol_l_100km"] = out["fuel_petrol_g_km"] * 100.0 / PETROL_G_PER_L if dist else None
    mm = row["m_minute"]
    for mg in MERGES:
        out[mg] = breakdown(mm[f"{mg}_out"], mm[f"{mg}_acc_vs"], mm[f"{mg}_acc_n"])
        out[f"{mg}_mergepos"] = row[f"m_mergepos_{mg}"]
    for r in RAMPS:
        out[f"{r}_queue_mean"] = float(np.mean(mm[f"{r}_queue"]) / 60.0)
        out[f"{r}_queue_max_min"] = float(np.max(mm[f"{r}_queue"]) / 60.0)
        out[f"{r}_pending_mean"] = float(np.mean(mm[f"{r}_pending"]) / 60.0)
    if field is not None:
        out["waves"] = waves(field["v"], field["n"], row["m_st_dt"], row["m_st_dx"])
    return out
