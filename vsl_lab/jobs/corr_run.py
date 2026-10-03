"""CORR2 job (Track 4): one run of one classical controller on the CORR2 freeway corridor (plants/corr2.py).

Controllers (--ctrl):
  nc                      meters all-green (program "allgreen", asserted at every checkpoint: health H-R7), no VSL
  alinea:<o_set>:<K_R>    local ALINEA on BOTH ramps (below)
  const:<b>               posted constant VSL rate b (x 33.33 m/s) on VSL areas 1 (m1) and 2 (m4), with a one-step
                          upstream staircase min(1, b + 0.2) on m0 / m3 and the acceleration areas m2 / m5 at 0.9
                          while b < 1 (mirrors mrg3_run post(): application area b, staircase upstream, acceleration
                          area 0.9; CORR2 has one 1.5 km / 1.25 km edge upstream of each area, so one step, not two)
  vslalinea:<b>:<o_set>:<K_R>   both
Control acts from t_ctrl0 = 300 s, first update at 360 s, then every T_c = 60 s; at the end of demand (3900 s)
VSL is released and the meters go all-green, and the network drains uncontrolled (as mrg3_run).

ALINEA (Papageorgiou, Hadj-Salem & Blosseville 1991, "ALINEA: a local feedback control law for on-ramp metering",
Transportation Research Record 1320 [VERIFY]: not read in full here; formula and K_R = 70 veh/h as commonly reported
in the literature [VERIFY]):
    r(k) = r(k-1) + K_R * (o_set - o_out(k))
  o_out(k) = downstream occupancy (%) over the last T_c = 60 s: mean over the 3 mainline lanes of
             getLastIntervalOccupancy of the 60 s loops e1a_m3_* / e1a_m6_* 40 m downstream of the merge1 / merge2
             end (checked 2026-10-03: at t = 60 k s the running interval is empty, so the last interval is exactly
             [60(k-1), 60k)); o_set in %, K_R in veh/h per % occupancy;
  r clipped to [240, 1800] veh/h; r(0) = 1800 (no metering) at the first control step;
  queue override: if the ramp storage fill (sum over vehicles on the 400 m storage edge of length + minGap, divided
             by 400 m; mean of the 1 s samples of the last 10 s) exceeds 0.9, r(k) = r_max for that period;
  anti-windup: r(k-1) in the next update is the rate actually applied (after clipping and override).
  r is applied by plants/corr2.Meter: one vehicle per green, a green every 3600 / r s (2 s, extended until the
  waiting head vehicle has crossed, max 4 s; yellow between greens; r >= 1800 = permanent green).
  Smoke note (2026-10-03, throw-away seed 7140000, q 4500/600/900): the 1-min downstream occupancies peaked at
  ~17 % (R1) / ~15 % (R2) in nc, so alinea:20:70 never metered (r = 1800 in all 60 periods; result hash identical
  to nc); alinea:12:70 metered. o_set must be tuned on tuning seeds; SUMO point-loop occupancy at capacity is low.

Metrics (summary.json): door-to-door mean time incl. origin (insertion) queues = arrival - desired departure, for all
vehicles (tts_system / generated, as mrg3_run) and per group (main, r1, r2, offramp = main_off + r1_off,
through_main = main_ex) and per route, plus the same by 300 s departure bins and a delay vs the 0-300 s departure bin
(base demand, before any control acts); stops per vehicle (tripinfo waitingCount, --stops); teleports, collisions,
health; per ramp: max queue (storage edge, origin edge, insertion backlog, total), max fill, share of time fill > 0.9
over [0, 3900 s), meter counters and realised discharge; congested time (30 s loop speed < 60 km/h) at every mainline
edge end (spillback diagnostics: m3 end = just upstream of the off-ramp diverge).

python -m vsl_lab.jobs.corr_run --ctrl nc --seed 7140000 --q-main 4500 --q-r1 600 --q-r2 900 --tag smoke --stops
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import libsumo as ls
import numpy as np

from vsl_lab.config import RUNS_ROOT
from vsl_lab.netgen import corr2 as N
from vsl_lab.plants import corr2 as P
from vsl_lab.sim.runner import SumoSim

R_MIN, R_MAX = 240.0, 1800.0
T_C = 60.0
Q_OVERRIDE = 0.9
CONG_KMH = 60.0


class Alinea:
    def __init__(self, o_set: float, k_r: float, r_min: float = R_MIN, r_max: float = R_MAX,
                 q_frac: float = Q_OVERRIDE):
        self.o_set, self.k_r, self.r_min, self.r_max, self.q_frac = o_set, k_r, r_min, r_max, q_frac
        self.r = r_max
        self.n_override = 0

    def step(self, o_out: float, fill: float) -> tuple:
        r = self.r + self.k_r * (self.o_set - o_out)
        r = min(max(r, self.r_min), self.r_max)
        ov = fill > self.q_frac
        if ov:
            r = self.r_max
            self.n_override += 1
        self.r = r
        return r, ov


def parse_ctrl(ctrl: str) -> dict:
    p = ctrl.split(":")
    if p[0] == "nc" and len(p) == 1:
        return {"b": None, "alinea": None}
    if p[0] == "alinea" and len(p) == 3:
        return {"b": None, "alinea": (float(p[1]), float(p[2]))}
    if p[0] == "const" and len(p) == 2:
        return {"b": float(p[1]), "alinea": None}
    if p[0] == "vslalinea" and len(p) == 4:
        return {"b": float(p[1]), "alinea": (float(p[2]), float(p[3]))}
    raise ValueError(f"unknown controller {ctrl!r}")


def post_vsl(b: float) -> None:
    vmax = P.V_LIMIT
    acc = 0.9 if b < 1.0 - 1e-9 else 1.0
    for app, up, accel in (("m1", "m0", "m2"), ("m4", "m3", "m5")):
        P.set_vsl((app,), b * vmax)
        P.set_vsl((up,), min(1.0, b + 0.2) * vmax)
        P.set_vsl((accel,), acc * vmax)


def _group_stats(dem, arrival_t: dict, t_censor: float, bin_s: float = 300.0, t_end: float = 3900.0) -> dict:
    tt = {}
    for dep, vid, rid, _ in dem.vehicles:
        tt.setdefault(rid, []).append((dep, arrival_t.get(vid, t_censor) - dep))
    groups = dict(P.GROUPS, all=tuple(tt))
    groups.update({f"route:{r}": (r,) for r in tt})
    nb = int(round(t_end / bin_s))
    out = {}
    for g, rids in groups.items():
        rows = [x for r in rids for x in tt.get(r, [])]
        if not rows:
            continue
        dep = np.array([x[0] for x in rows])
        t = np.array([x[1] for x in rows])
        bins = []
        for k in range(nb):
            m = (dep >= k * bin_s) & (dep < (k + 1) * bin_s)
            bins.append(round(float(t[m].mean()), 1) if m.any() else None)
        ref = bins[0]
        out[g] = {"mean_s": float(t.mean()), "n": int(len(t)), "ref_0_300_s": ref,
                  "delay_vs_ref_s": float(t.mean() - ref) if ref is not None else None,
                  "max_bin_mean_s": max(b for b in bins if b is not None), "by_dep_bin_300s": bins}
    return out


def run(ctrl: str, seed: int, q_main: float, q_r1: float, q_r2: float, tag: str, out_root: Path,
        stops: bool = False, off_share: float = P.OFF_SHARE, p_nc: float = 0.3, truck: float = 0.1,
        driver: str = "H5", step: float = P.STEP_LENGTH, t_end: float = 3900.0, t_ctrl0: float = 300.0,
        t_max: float = 10800.0) -> dict:
    w_all = time.time()
    cfg = parse_ctrl(ctrl)
    dt = step
    run_id = (f"corr2{driver}_{ctrl.replace(':', '_')}_s{seed}_m{int(q_main)}_r{int(q_r1)}_{int(q_r2)}"
              f"_off{off_share:g}_nc{p_nc:g}_tr{truck:g}_dt{dt:g}_pid{os.getpid()}")
    run_dir = out_root / tag / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    f = P.files()
    lanes = f["lanes"]
    dem = P.demand(seed, q_main, q_r1, q_r2, off_share=off_share, p_noncompliant=p_nc, truck_share=truck,
                   driver=driver, step_length=dt, t_end=t_end)
    rou = run_dir / f"routes_s{seed}_pid{os.getpid()}.rou.xml"
    dem.write(rou)
    trip_file = run_dir / f"tripinfo_pid{os.getpid()}.xml"
    extra = list(P.DRIVERS[driver]["args"])
    if stops:
        extra += ["--tripinfo-output", str(trip_file)]
    sim = SumoSim(f["net"], rou, run_dir, dem, additional=[f["add"]], step_length=dt, checkpoint_s=300.0,
                  seed=seed, stuck_wait_s=180.0, extra_args=extra)
    sim.start()
    sens = P.Sensors(lanes)
    meters = {r: P.Meter(N.TLS[r], r, lanes[f"{r}_0"]) for r in N.RAMPS}
    for m in meters.values():
        m.all_green_program()
    sim.asserts.append(P.assert_meter_links)
    if cfg["alinea"] is None:
        sim.asserts.append(P.assert_meters_green)
    alin = {r: Alinea(*cfg["alinea"]) for r in N.RAMPS} if cfg["alinea"] else None
    b = cfg["b"]

    prefix = {"R1": "r1_", "R2": "r2_"}
    qs = {r: [] for r in N.RAMPS}          # 1 s samples: (fill, n_storage, n_origin, n_pending, jam_m)
    feats, trace = [], {r: [] for r in N.RAMPS}
    occ_last = {r: -1.0 for r in N.RAMPS}
    qout30 = {r: [] for r in N.RAMPS}       # ramp-end loop flows (veh/h) of the 30 s intervals
    next_loop, next_ctrl, next_samp = 30.0, t_ctrl0 + T_C, 1.0
    b_now = 1.0
    while sim.t < t_end - 1e-9:
        sim.step(1)
        t = sim.t
        if alin is not None:
            for m in meters.values():
                m.tick(t)
        if t >= next_samp - 1e-9:
            pend = ls.simulation.getPendingVehicles()
            for r in N.RAMPS:
                fill, n_st = sens.ramp_fill(r)
                n_or = ls.lanearea.getLastStepVehicleNumber(f"e2_{r}o_0")
                n_pd = sum(1 for v in pend if v.startswith(prefix[r]))
                qs[r].append((fill, n_st, n_or, n_pd, ls.lanearea.getJamLengthMeters(f"e2_{r}_0")))
            next_samp += 1.0
        if t >= next_loop - 1e-9:
            row = [round(t, 1)]
            for e in N.MAIN_EDGES:
                row += [round(P.Sensors.flow_vph_per_lane(e), 1), round(P.Sensors.speed_kmh(e), 2)]
            row.append(round(P.Sensors.speed_kmh("m3", lanes=[0]), 2))
            row.append(round(P.Sensors.loop_vph("e1_O1_0"), 1))
            for r in N.RAMPS:
                q_out = P.Sensors.loop_vph(f"e1_{r}out_0")
                qout30[r].append(q_out)
                last = qs[r][-1] if qs[r] else (0.0, 0, 0, 0, 0.0)
                row += [round(P.Sensors.loop_vph(f"e1_{r}in_0"), 1), round(q_out, 1), round(last[0], 3), last[1],
                        last[2], last[3], round(occ_last[r], 2),
                        round(meters[r].rate, 1) if meters[r].rate is not None else R_MAX]
            row.append(round(b_now, 2))
            feats.append(row)
            next_loop += 30.0
        if t >= next_ctrl - 1e-9 and t >= t_ctrl0:
            if b is not None:
                post_vsl(b)
                b_now = b
            for r in N.RAMPS:
                occ_last[r] = P.Sensors.alinea_occ_pct(r)
            if alin is not None:
                for r in N.RAMPS:
                    fill10 = float(np.mean([s[0] for s in qs[r][-10:]])) if qs[r] else 0.0
                    rr, ov = alin[r].step(occ_last[r], fill10)
                    meters[r].set_rate(rr, t)
                    trace[r].append((round(t), round(occ_last[r], 2), round(rr, 1), int(ov), round(fill10, 3),
                                     round(float(np.mean(qout30[r][-2:])), 1) if qout30[r] else None,
                                     round(P.Sensors.alinea_flow_vph(r), 1)))
            next_ctrl += T_C
    if b is not None:
        post_vsl(1.0)
    for m in meters.values():
        m.release()
    drained = sim.drain(t_max)
    arrival_t = dict(sim.arrival_t)
    t_close = sim.t
    out = sim.close(drained=drained)
    n = out["generated"]
    d2d = _group_stats(dem, arrival_t, t_close, t_end=t_end)
    ramp = {}
    for r in N.RAMPS:
        a = np.array(qs[r]) if qs[r] else np.zeros((1, 5))
        tot = a[:, 1] + a[:, 2] + a[:, 3]
        ramp[r] = {"max_storage_veh": int(a[:, 1].max()), "max_origin_edge_veh": int(a[:, 2].max()),
                   "max_pending_veh": int(a[:, 3].max()), "max_total_queue_veh": int(tot.max()),
                   "mean_total_queue_veh": float(tot.mean()), "max_fill": float(a[:, 0].max()),
                   "mean_fill": float(a[:, 0].mean()), "share_fill_gt_0.9": float((a[:, 0] > Q_OVERRIDE).mean()),
                   "max_jam_m": float(a[:, 4].max()),
                   "meter": {"n_greens": meters[r].n_greens, "n_head_greens": meters[r].n_head_greens,
                             "n_head_passed": meters[r].n_head_passed,
                             "n_override": alin[r].n_override if alin else 0}}
        if trace[r]:   # realised discharge while the meter was binding (r < r_max and storage fill > 0.3)
            bind = [x for x in trace[r] if x[2] < R_MAX - 1e-6 and x[4] > 0.3]
            ramp[r]["binding_periods"] = len(bind)
            ramp[r]["binding_mean_r_vph"] = float(np.mean([x[2] for x in bind])) if bind else None
            ramp[r]["binding_mean_out_vph"] = float(np.mean([x[5] for x in bind])) if bind else None
            ramp[r]["periods_at_r_min"] = sum(1 for x in trace[r] if x[2] <= R_MIN + 1e-6)
            ramp[r]["periods_at_r_max"] = sum(1 for x in trace[r] if x[2] >= R_MAX - 1e-6)
    cong = {}
    for j, e in enumerate(N.MAIN_EDGES):
        v = [row[2 + 2 * j] for row in feats]
        idx = [k for k, x in enumerate(v) if 0 <= x < CONG_KMH]
        cong[e] = {"congested_s": 30.0 * len(idx), "first_t": feats[idx[0]][0] if idx else None,
                   "last_t": feats[idx[-1]][0] if idx else None, "min_speed_kmh": min((x for x in v if x >= 0),
                                                                                       default=None)}
    v0 = [row[1 + 2 * len(N.MAIN_EDGES)] for row in feats]
    cong["m3_lane0"] = {"congested_s": 30.0 * sum(1 for x in v0 if 0 <= x < CONG_KMH),
                        "min_speed_kmh": min((x for x in v0 if x >= 0), default=None)}
    served = sum(1 for a_ in arrival_t.values() if a_ <= t_end + 1e-9)
    due_end = sum(1 for v in dem.vehicles if v[0] < t_end)
    out.update({
        "job": "corr_run", "plant": "CORR2", "net_hash": N.spec_hash(), "run_id": run_id, "ctrl": ctrl, "seed": seed,
        "q_main": q_main, "q_r1": q_r1, "q_r2": q_r2, "off_share": off_share, "driver": driver,
        "p_noncompliant": p_nc, "truck_share": truck, "step_length": dt, "t_end": t_end, "t_ctrl0": t_ctrl0,
        "mean_time_in_system_s": out["tts_system_vehh"] * 3600.0 / max(n, 1),
        "door_to_door": d2d, "ramp_queues": ramp, "congestion": cong,
        "served_by_t_end": served, "generated_by_t_end": due_end,
        "served_share_by_t_end": served / max(due_end, 1),
        "alinea_trace_cols": ["t", "o_out_pct", "r_vph", "override", "fill10", "q_out_last60_vph", "q_down_vph"],
        "alinea_trace": trace if alin else None, "vsl_b": b,
        "emergency_braking": (out.get("sumo_stats") or {}).get("emergencyBraking"),
        "wall_total_s": None,
    })
    try:
        txt = sim.log_file.read_text(errors="replace")
        out["red_light_emergency_stops"] = len(re.findall(r"emergency stop .* red traffic light", txt))
    except OSError:
        out["red_light_emergency_stops"] = None
    if stops:
        try:
            import xml.etree.ElementTree as _ET
            per = {}
            for _, el in _ET.iterparse(trip_file):
                if el.tag == "tripinfo":
                    rid = el.get("id").rsplit(".", 1)[0]
                    per.setdefault(rid, []).append((int(el.get("waitingCount", 0)), float(el.get("waitingTime", 0.0)),
                                                    float(el.get("timeLoss", 0.0))))
                    el.clear()
            allr = [x for v in per.values() for x in v]
            out["stops_per_veh"] = float(np.mean([x[0] for x in allr])) if allr else None
            out["share_stopped_veh"] = float(np.mean([x[0] > 0 for x in allr])) if allr else None
            out["stop_time_per_veh_s"] = float(np.mean([x[1] for x in allr])) if allr else None
            out["time_loss_per_veh_s"] = float(np.mean([x[2] for x in allr])) if allr else None
            out["n_tripinfo"] = len(allr)
            out["stops_by_group"] = {}
            for g, rids in dict(P.GROUPS, **{f"route:{r}": (r,) for r in per}).items():
                rows = [x for r in rids for x in per.get(r, [])]
                if rows:
                    out["stops_by_group"][g] = {"stops_per_veh": float(np.mean([x[0] for x in rows])),
                                                "share_stopped": float(np.mean([x[0] > 0 for x in rows])),
                                                "n": len(rows)}
            trip_file.unlink()
        except Exception as exc:   # noqa: BLE001
            out["stops_error"] = repr(exc)
    out.pop("arrivals_bins", None)
    out["wall_total_s"] = round(time.time() - w_all, 2)
    (run_dir / "summary.json").write_text(json.dumps(out, indent=1, default=str))
    hdr = ["t"] + [f"{e}_{k}" for e in N.MAIN_EDGES for k in ("q", "v")] + ["m3_l0_v", "q_O1"]
    for r in N.RAMPS:
        hdr += [f"{r}_qin", f"{r}_qout", f"{r}_fill", f"{r}_nstor", f"{r}_norig", f"{r}_npend", f"{r}_occ", f"{r}_r"]
    hdr.append("b")
    with open(run_dir / "features.csv", "w") as fh:
        fh.write(",".join(hdr) + "\n")
        for row in feats:
            fh.write(",".join(str(x) for x in row) + "\n")
    try:
        rou.unlink()
    except OSError:
        pass
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctrl", default="nc")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--q-main", type=float, default=4500.0)
    ap.add_argument("--q-r1", type=float, default=600.0)
    ap.add_argument("--q-r2", type=float, default=900.0)
    ap.add_argument("--off-share", type=float, default=P.OFF_SHARE)
    ap.add_argument("--p-nc", type=float, default=0.3)
    ap.add_argument("--truck", type=float, default=0.1)
    ap.add_argument("--driver", default="H5", choices=sorted(P.DRIVERS))
    ap.add_argument("--step", type=float, default=P.STEP_LENGTH)
    ap.add_argument("--stops", action="store_true", help="tripinfo stop metrics")
    ap.add_argument("--tag", default="smoke")
    ap.add_argument("--out-root", default=str(RUNS_ROOT / "t4"))
    a = ap.parse_args(argv)
    out = run(a.ctrl, a.seed, a.q_main, a.q_r1, a.q_r2, a.tag, Path(a.out_root), stops=a.stops,
              off_share=a.off_share, p_nc=a.p_nc, truck=a.truck, driver=a.driver, step=a.step)
    d = out["door_to_door"]
    print(json.dumps({"run_id": out["run_id"], "mean_time_in_system_s": round(out["mean_time_in_system_s"], 1),
                      "d2d": {g: round(d[g]["mean_s"], 1) for g in ("all", "main", "r1", "r2", "offramp") if g in d},
                      "stops_per_veh": out.get("stops_per_veh"), "teleports": out["teleports"],
                      "collisions": out["collisions"], "drained": out["drained"], "wall_s": out["wall_s"],
                      "health": out["health"]["status"], "codes": list(out["health"]["by_code"].keys())}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
