"""MRG3 job (Track 2): one run of one classical controller at the merge bottleneck.

Controllers: nc | const:<b> (constant VSL rate b on the application area) | mtfc[:rho:kp:ki:ki2]
Upstream safety staircase (Carlson et al. "safety VSLs"): up2 = min(1, b+0.2), up3 = min(1, b+0.4);
application area (up1, up0a) = b; acceleration area (up0b) = 0.9 while active. VSL = b x 120 km/h.
Metrics: door-to-door mean time in system (all, mainline, ramp; incl. origin queue; drain until empty);
exit throughput; capacity-drop measurement from 5-min aggregates (onset = 5-min speed at up0b < 60 km/h).

python -m vsl_lab.jobs.mrg3_run --ctrl nc --seed 7120000 --main-peak 5400 --ramp-peak 900 --tag calib
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import libsumo as ls
import numpy as np

from vsl_lab.config import RUNS_ROOT
from vsl_lab.controllers.mtfc import MTFC
from vsl_lab.plants import mrg3 as P
from vsl_lab.sim.runner import SumoSim


# 10 s speed probes (edge, lane position; mean speed of vehicles within +-50 m): x ~ 500, 1500, 2500, 3250, 3735 m
# (merge starts at x = 4000). Used by the realism gate (docs/lab/t2_realism_protocol.md).
PROBES = (("up3", 500.0), ("up2", 500.0), ("up1", 500.0), ("up0a", 250.0), ("up0b", 233.0))


def capacity_drop(ts: list) -> dict:
    """ts rows: (t, exit_flow_vph_total, speed_up0b_kmh). 5-min (10 x 30 s) rolling means."""
    if len(ts) < 20:
        return {}
    t = np.array([r[0] for r in ts])
    q = np.array([r[1] for r in ts])
    v = np.array([r[2] if r[2] >= 0 else np.nan for r in ts])
    w = 10
    q5 = np.convolve(q, np.ones(w) / w, "valid")
    v5 = np.array([np.nanmean(v[i:i + w]) if np.isfinite(v[i:i + w]).any() else np.nan for i in range(len(v) - w + 1)])
    t5 = t[w - 1:]
    onset = np.nonzero(v5 < 60.0)[0]
    if len(onset) == 0:
        return {"breakdown": False, "max_5min_flow": float(np.max(q5))}
    i0 = int(onset[0])
    pre = q5[max(0, i0 - 30):i0 + 1]
    rec = np.nonzero(v5[i0:] > 70.0)[0]
    i1 = i0 + (int(rec[0]) if len(rec) else len(v5) - i0)
    dis = q5[min(i0 + 10, i1 - 1):i1] if i1 - i0 > 10 else q5[i0:i1]
    pre_max = float(np.max(pre)) if len(pre) else float("nan")
    dmean = float(np.mean(dis)) if len(dis) else float("nan")
    return {"breakdown": True, "onset_t": float(t5[i0]), "pre_max_5min_flow": pre_max, "discharge_mean_5min_flow": dmean,
            "ratio": dmean / pre_max if pre_max else float("nan"), "congested_s": float((i1 - i0) * 30.0)}


def run(ctrl: str, seed: int, main_peak: float, ramp_peak: float, p_nc: float, truck: float, tag: str, out_root: Path,
        t_end: float = 3900.0, t_ctrl0: float = 300.0, t_max: float = 10800.0, plant: str = "v1",
        driver: str | None = None) -> dict:
    model, dspeed = P.PLANTS[plant]
    run_id = (f"mrg3{plant}{'' if driver is None else driver}_{ctrl.replace(':', '_')}_s{seed}_m{int(main_peak)}"
              f"_r{int(ramp_peak)}_nc{p_nc:g}_tr{truck:g}_pid{os.getpid()}")
    run_dir = out_root / tag / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    f = P.files()
    mprof = P.profile(2500.0, main_peak, 600.0, 1200.0, 3000.0, t_end)
    rprof = P.profile(300.0, ramp_peak, 600.0, 1200.0, 3000.0, t_end)
    dem = P.demand(seed, mprof, rprof, p_noncompliant=p_nc, truck_share=truck, model=model, depart_speed=dspeed,
                   driver=driver)
    rou = run_dir / f"routes_s{seed}_pid{os.getpid()}.rou.xml"
    dem.write(rou)
    sim = SumoSim(f["net"], rou, run_dir, dem, additional=[f["add"]], step_length=P.STEP_LENGTH, checkpoint_s=300.0,
                  seed=seed, stuck_wait_s=180.0, extra_args=(P.DRIVERS[driver]["args"] if driver else []))
    sim.start()
    sens = P.Sensors(f["lanes"])
    mt = None
    b_const = None
    if ctrl.startswith("mtfc"):
        parts = ctrl.split(":")
        vals = [float(x) for x in parts[1:]] if len(parts) > 1 else []
        names = ["rho_set", "kp", "ki", "ki2"]
        mt = MTFC(**dict(zip(names, vals)))
    elif ctrl.startswith("const:"):
        b_const = float(ctrl.split(":")[1])
    ts, bs, feats, probes = [], [], [], []
    dens_samples, qc_hist = [], []
    b_app, b_acc = 1.0, 1.0
    next_loop, next_ctrl, next_samp = 30.0, t_ctrl0 + 60.0, 10.0
    vmax = P.V_LIMIT

    def post(b_app, b_acc):
        P.set_vsl(("up1", "up0a"), b_app * vmax)
        P.set_vsl(("up2",), min(1.0, b_app + 0.2) * vmax)
        P.set_vsl(("up3",), min(1.0, b_app + 0.4) * vmax)
        P.set_vsl(("up0b",), b_acc * vmax)

    while sim.t < t_end - 1e-9:
        sim.run_until(sim.t + 10.0)
        if sim.t >= next_samp - 1e-9:
            dens_samples.append(sens.density_merge_vkl())
            row = [round(sim.t, 1)]
            for e, x in PROBES:
                vs = [ls.vehicle.getSpeed(v) for v in ls.edge.getLastStepVehicleIDs(e)
                      if abs(ls.vehicle.getLanePosition(v) - x) <= 50.0]
                row.append(round(float(np.mean(vs)), 3) if vs else "")
            probes.append(row)
            next_samp += 10.0
        if sim.t >= next_loop - 1e-9:
            q_exit = sum(ls.inductionloop.getLastIntervalVehicleNumber(f"e1_down_{i}") for i in range(3)) * 120.0
            ts.append((sim.t, q_exit, P.Sensors.speed_kmh("up0b")))
            qc_hist.append(P.Sensors.flow_vph_per_lane("up0a"))
            # D-check feature table (30 s): per-edge flow/lane, speed, per-lane speed spread, densities, ramp flow, b
            row = [round(sim.t, 1)]
            for e in ("up3", "up2", "up1", "up0a", "up0b", "down"):
                lane_v = [ls.inductionloop.getLastIntervalMeanSpeed(f"e1_{e}_{i}") for i in range(3)]
                lane_v = [v for v in lane_v if v >= 0]
                row += [round(P.Sensors.flow_vph_per_lane(e), 1), round(P.Sensors.speed_kmh(e), 2),
                        round(float(np.std(lane_v)) * 3.6, 2) if len(lane_v) > 1 else 0.0]
            row += [round(sens.density_merge_vkl(), 2), round(sens.density_down_vkl(), 2),
                    ls.inductionloop.getLastIntervalVehicleNumber("e1_ramp_0") * 120, round(b_app, 2)]
            feats.append(row)
            next_loop += 30.0
        if sim.t >= next_ctrl - 1e-9 and sim.t >= t_ctrl0:
            if mt is not None:
                rho = float(np.mean(dens_samples[-6:])) if dens_samples else 0.0
                qc = float(np.mean(qc_hist[-2:])) if qc_hist else 0.0
                b_app, b_acc = mt.step(rho, qc)
                post(b_app, b_acc)
            elif b_const is not None:
                b_app, b_acc = b_const, (0.9 if b_const < 1.0 else 1.0)
                post(b_app, b_acc)
            bs.append((sim.t, b_app))
            next_ctrl += 60.0
    # demand over: release VSL, drain uncontrolled
    post(1.0, 1.0)
    drained = sim.drain(t_max)
    by_route = sim.time_in_system_by_route()
    out = sim.close(drained=drained)
    n = out["generated"]
    out.update({
        "job": "mrg3_run", "plant": plant, "run_id": run_id, "ctrl": ctrl, "seed": seed, "main_peak": main_peak,
        "ramp_peak": ramp_peak,
        "p_noncompliant": p_nc, "truck_share": truck,
        "mean_time_in_system_s": out["tts_system_vehh"] * 3600.0 / max(n, 1),
        "time_main_s": by_route.get("main", {}).get("mean_s"), "time_ramp_s": by_route.get("ramp", {}).get("mean_s"),
        "n_main": by_route.get("main", {}).get("n"), "n_ramp": by_route.get("ramp", {}).get("n"),
        "capdrop": capacity_drop(ts), "b_trace": bs[::5], "min_b": min((b for _, b in bs), default=1.0),
    })
    out.pop("arrivals_bins", None)
    (run_dir / "summary.json").write_text(json.dumps(out, indent=1, default=str))
    with open(run_dir / "probes10.csv", "w") as fh:
        fh.write("t," + ",".join(f"{e}@{int(x)}" for e, x in PROBES) + "\n")
        for r in probes:
            fh.write(",".join(str(x) for x in r) + "\n")
    hdr = ["t"] + [f"{e}_{k}" for e in ("up3", "up2", "up1", "up0a", "up0b", "down") for k in ("q", "v", "vspread")] \
        + ["rho_merge", "rho_down", "q_ramp", "b"]
    with open(run_dir / "features.csv", "w") as fh:
        fh.write(",".join(hdr) + "\n")
        for r in feats:
            fh.write(",".join(str(x) for x in r) + "\n")
    try:
        rou.unlink()
    except OSError:
        pass
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctrl", default="nc")
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--main-peak", type=float, default=5400.0)
    ap.add_argument("--ramp-peak", type=float, default=900.0)
    ap.add_argument("--p-nc", type=float, default=0.3)
    ap.add_argument("--truck", type=float, default=0.1)
    ap.add_argument("--plant", default="v1", choices=["v1", "v2", "v3"])
    ap.add_argument("--driver", default=None, choices=["H0", "H1", "H2", "H3", "H4"])
    ap.add_argument("--tag", default="smoke")
    ap.add_argument("--out-root", default=str(RUNS_ROOT / "t2"))
    a = ap.parse_args(argv)
    out = run(a.ctrl, a.seed, a.main_peak, a.ramp_peak, a.p_nc, a.truck, a.tag, Path(a.out_root), plant=a.plant,
              driver=a.driver)
    keys = ("run_id", "mean_time_in_system_s", "time_main_s", "time_ramp_s", "capdrop", "min_b", "teleports", "drained",
            "wall_s")
    print(json.dumps({k: out.get(k) for k in keys} | {"health": out["health"]["status"],
                                                       "codes": list(out["health"]["by_code"].keys())}, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
