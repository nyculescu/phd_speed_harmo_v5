"""Human-only recalibration of the fleet plant (V177): pass rule and selection fixed in docs/decisions.md V177.

One run = the V139 ramp (calibrate.profile) on bn4x with HDV cars and trucks only, no control, no crashes; breakdown,
pre-queue flow, QDF and drop by the V139 rule (calibrate.measure) at a 100 km/h free speed, with a vehicle-weighted
loop speed.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

import libsumo as ls
import numpy as np

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.fleet import fleet as fl
from v5b.fleet.smoke import CFG, _nan, loop_speed
from v5b.p1c import calibrate as cal
from v5b.p1c import plant as pl
from v5b.p1c.episode import Sim

HUMAN_SHARES = (0.925, 0.075, 0.0, 0.0, 0.0)
TAU_SCALES = (0.6, 0.7, 0.8, 0.9, 1.0)
MERGES = ("zip20", "zip100")
ACCELS = (2.6, 2.0)
DEFAULTS = (1.0, "zip100", 2.6)
DROP_BAND, DROP_SHARE, QDF_BAND, DROP_AIM = (0.02, 0.11), 0.75, cal.T1B, 0.05
T_CAP = 7200.0


def grid() -> list:
    return [(c, m, a) for c in TAU_SCALES for m in MERGES for a in ACCELS]


def run_once(seed: int, c: float, merge: str, accel: float, run_dir: Path) -> dict:
    t_w0 = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    fl.SHARES, fl.HDV_TAU_SCALE, fl.HDV_ACCEL = HUMAN_SHARES, c, None if accel == 2.6 else accel
    cfg = dataclasses.replace(CFG, geom="bn4x", merge=merge)
    d = fl.build_net(cfg)
    dem = fl.FleetDemand(seed, cal.profile("bn4"), cfg)
    tag = f"cal_{cfg.tag()}_c{c:g}_a{accel:g}_s{seed}_pid{os.getpid()}"
    rou, trip = run_dir / f"r_{tag}.rou.xml", run_dir / f"t_{tag}.xml"
    dem.write(rou)
    sim = Sim(d / "net.xml", rou, run_dir, dem, additional=[d / "add.xml"], step_length=cfg.step, seed=seed,
              extra_args=["--tripinfo-output", str(trip)])
    loops = pl.loop_ids(cfg.geom)
    sim.start()
    ls.trafficlight.setProgram(pl.TLS_ID, "allgreen")
    ser, drained = [], False
    while sim.t < T_CAP - 1e-9:
        sim.step()
        if abs(sim.t / pl.LOOP_PERIOD - round(sim.t / pl.LOOP_PERIOD)) < 1e-6:
            ser.append((round(sim.t, 1), int(sum(ls.inductionloop.getLastIntervalVehicleNumber(i) for i in loops["exit"])),
                        _nan(loop_speed(loops["e4"])), _nan(loop_speed(loops["e3"])), None,
                        _nan(loop_speed(loops["up"]))))
        if sim.departed == sim._total and ls.vehicle.getIDCount() == 0 and not ls.simulation.getPendingVehicles():
            drained = True
            break
    res = sim.close(drained=drained)
    log = sim.log_file.read_text(errors="replace")
    with mock.patch.object(cal, "FREE", fl.LIMIT):
        m = cal.measure({"series": ser})
    hdv = [v for v in dem.veh if v.cls == "hdv_car"]
    out = {"seed": seed, "c": c, "merge": merge, "accel": accel, **m, "drained": drained,
           "collisions": res["collisions"], "teleports": res["teleports"],
           "emergency_braking": log.count("performs emergency braking"), "sumo_errors": log.count("Error"),
           "tau_mean": round(float(np.mean([v.tau for v in hdv])), 3),
           "resample_share": round(sum(v.resampled for v in hdv) / max(1, len(hdv)), 3),
           "wall_s": round(time.time() - t_w0, 1)}
    for f in (rou, trip, sim.log_file, sim.stat_file):
        f.unlink(missing_ok=True)
    return out


def batch(out: Path, seeds: list, workers: int) -> None:
    (out / "runs").mkdir(parents=True, exist_ok=True)
    env = clean_sumo_env()
    jobs = [(s, c, m, a) for (c, m, a) in grid() for s in seeds
            if not (out / "runs" / f"c{c:g}_{m}_a{a:g}_s{s}.json").exists()]
    print(f"{len(jobs)} runs, cpu {cal._cpu_util():.0f} %", flush=True)

    def one(j):
        s, c, m, a = j
        while cal._cpu_util(1.0) > 90.0:          # CLAUDE.md CPU rule: launch only below 90 %
            time.sleep(30)
        r = subprocess.run(["nice", "-n", "10", PYTHON_BIN, "-m", "v5b.fleet.calib", "one", "--seed", str(s),
                            "--c", str(c), "--merge", m, "--accel", str(a),
                            "--out", str(out / "runs" / f"c{c:g}_{m}_a{a:g}_s{s}.json")],
                           cwd=REPO_ROOT, env=env, capture_output=True, text=True)
        return j, r.returncode, r.stderr[-300:] if r.returncode else ""

    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        for i, (j, rc, err) in enumerate(ex.map(one, jobs), 1):
            if rc:
                print("FAIL", j, err, flush=True)
            if i % 20 == 0:
                print(f"{i}/{len(jobs)} done, {time.time() - t0:.0f} s", flush=True)
    print(f"all done in {time.time() - t0:.0f} s", flush=True)


def analyse(out: Path) -> dict:
    runs = [json.loads(f.read_text()) for f in sorted((out / "runs").glob("*.json"))]
    rows = []
    for (c, m, a) in grid():
        rs = [r for r in runs if (r["c"], r["merge"], r["accel"]) == (c, m, a)]
        if not rs:
            continue
        drops = [r["drop"] for r in rs if r["drop"] is not None]
        qdfs = [r["qdf"] for r in rs if r["qdf"] is not None]
        med_drop = float(np.median(drops)) if drops else None
        med_qdf = float(np.median(qdfs)) if qdfs else None
        in_band = sum(DROP_BAND[0] <= d <= DROP_BAND[1] for d in drops) / len(rs)
        safe = all(r["collisions"] == 0 and r["teleports"] == 0 for r in rs)
        ok = (med_drop is not None and DROP_BAND[0] <= med_drop <= DROP_BAND[1] and in_band >= DROP_SHARE
              and med_qdf is not None and QDF_BAND[0] <= med_qdf <= QDF_BAND[1] and safe)
        rows.append({"c": c, "merge": m, "accel": a, "n": len(rs), "breakdowns": len(drops),
                     "median_drop": med_drop, "drop_in_band_share": round(in_band, 2), "median_qdf": med_qdf,
                     "median_pre": float(np.median([r["pre"] for r in rs if r["pre"] is not None])) if drops else None,
                     "collisions": sum(r["collisions"] for r in rs), "teleports": sum(r["teleports"] for r in rs),
                     "emergency_braking_median": float(np.median([r["emergency_braking"] for r in rs])),
                     "tau_mean": rs[0]["tau_mean"], "pass": ok,
                     "non_default": sum(x != y for x, y in zip((c, m, a), DEFAULTS))})
    passing = [r for r in rows if r["pass"]]
    chosen = min(passing, key=lambda r: (r["non_default"], abs(r["median_drop"] - DROP_AIM), -r["median_qdf"])) \
        if passing else None
    res = {"rows": rows, "n_pass": len(passing), "chosen": chosen}
    (out / "calibration.json").write_text(json.dumps(res, indent=1))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--seed", type=int, required=True)
    o.add_argument("--c", type=float, required=True)
    o.add_argument("--merge", required=True)
    o.add_argument("--accel", type=float, required=True)
    o.add_argument("--out", required=True)
    b = sub.add_parser("batch")
    b.add_argument("--out", required=True)
    b.add_argument("--seed0", type=int, required=True)
    b.add_argument("--n", type=int, default=10)
    b.add_argument("--workers", type=int, default=30)
    n = sub.add_parser("analyse")
    n.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "one":
        out = Path(a.out)
        res = run_once(a.seed, a.c, a.merge, a.accel, out.parent.parent / "rd")
        tmp = out.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(json.dumps(res))
        tmp.replace(out)
    elif a.cmd == "batch":
        batch(Path(a.out), list(range(a.seed0, a.seed0 + a.n)), a.workers)
        print(json.dumps(analyse(Path(a.out)), indent=1))
    else:
        print(json.dumps(analyse(Path(a.out)), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
