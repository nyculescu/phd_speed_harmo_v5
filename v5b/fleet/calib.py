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


# V180 stage 2: lane-end merges (SUMO's zipper caps throughput at about 1,350 veh/h for steps <= 0.25 s);
# V182 stage 3: lane-end merges, accel 2.6, plus the HDV-car action-step scale
STAGE_MERGES = {1: MERGES, 2: ("laneend",), 3: ("laneend",)}
STAGE_ACCELS = {1: ACCELS, 2: ACCELS, 3: (2.6,)}
STAGE_ASL = {1: (1.0,), 2: (1.0,), 3: (0.25, 0.5, 0.75, 1.0)}
STAGE_DEFAULTS = {1: DEFAULTS + (1.0,), 2: (1.0, "laneend", 2.6, 1.0), 3: (1.0, "laneend", 2.6, 1.0)}


def grid(stage: int = 1) -> list:
    return [(c, m, a, s) for c in TAU_SCALES for m in STAGE_MERGES[stage] for a in STAGE_ACCELS[stage]
            for s in STAGE_ASL[stage]]


def _name(c, m, a, s) -> str:
    return f"c{c:g}_{m}_a{a:g}" + ("" if s == 1.0 else f"_s{s:g}")


def run_once(seed: int, c: float, merge: str, accel: float, run_dir: Path, shares: tuple = HUMAN_SHARES,
             geom: str = "bn4x", step: float = CFG.step, ballistic: bool = False, asl_scale: float = 1.0) -> dict:
    t_w0 = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    fl.SHARES, fl.HDV_TAU_SCALE, fl.HDV_ACCEL = shares, c, None if accel == 2.6 else accel
    fl.HDV_ASL_SCALE = asl_scale
    cfg = dataclasses.replace(CFG, geom=geom, merge=merge, step=step)
    d = fl.build_net(cfg)
    dem = fl.FleetDemand(seed, cal.profile("bn4"), cfg)
    tag = f"cal_{cfg.tag()}_c{c:g}_a{accel:g}_s{seed}_pid{os.getpid()}"
    rou, trip = run_dir / f"r_{tag}.rou.xml", run_dir / f"t_{tag}.xml"
    dem.write(rou)
    sim = Sim(d / "net.xml", rou, run_dir, dem, additional=[d / "add.xml"], step_length=cfg.step, seed=seed,
              extra_args=["--tripinfo-output", str(trip)] + (["--step-method.ballistic", "true"] if ballistic else []))
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
    out = {"seed": seed, "c": c, "merge": merge, "accel": accel, "asl_scale": asl_scale, **m, "drained": drained,
           "collisions": res["collisions"], "teleports": res["teleports"],
           "emergency_braking": log.count("performs emergency braking"), "sumo_errors": log.count("Error"),
           "tau_mean": round(float(np.mean([v.tau for v in hdv])), 3),
           "resample_share": round(sum(v.resampled for v in hdv) / max(1, len(hdv)), 3),
           "wall_s": round(time.time() - t_w0, 1)}
    for f in (rou, trip, sim.log_file, sim.stat_file):
        f.unlink(missing_ok=True)
    return out


DIAG = {"base_sigmastep0.5": {"sigma_step": 0.5}, "base": {}, "no_trucks": {"shares": (1.0, 0.0, 0.0, 0.0, 0.0)}, "asl_step": {"asl": 0.1},
        "sigma_0.5": {"sigma": 0.5}, "all_three": {"shares": (1.0, 0.0, 0.0, 0.0, 0.0), "asl": 0.1, "sigma": 0.5}}


def diag_one(seed: int, name: str, run_dir: Path) -> dict:
    """V178 diagnosis: the default human-only configuration with one sourced ingredient switched off."""
    d = DIAG[name]
    fl.HDV_ASL_FIXED, fl.HDV_SIGMA_FIXED, fl.HDV_SIGMA_STEP = d.get("asl"), d.get("sigma"), d.get("sigma_step")
    return {"diag": name, **run_once(seed, *DEFAULTS, run_dir, d.get("shares", HUMAN_SHARES))}


# V178 walk from a V139-like human plant to the fleet plant, one difference added per step (cumulative)
WALK = [("w0_v139like", {"geom": "bn4", "limit": 23.0, "step": 0.5, "tau": 1.0, "sf": (1.0, 0.1, 0.2, 2.0),
                         "lengths": ((100.0, 5.0, 0.0),)}),
        ("w1_step0.1", {"step": 0.1}), ("w2_bn4x", {"geom": "bn4x"}), ("w3_100kmh", {"limit": 100.0 / 3.6}),
        ("w4_uk_speeds", {"sf": fl.CAR_SF}), ("w5_lengths", {"lengths": fl.CAR_SEGMENTS}), ("w6_tau_beta", {"tau": None}),
        ("w7_w1_plus_sigmastep0.5", None)]


def walk_one(seed: int, i: int, run_dir: Path) -> dict:
    k = {"sigma_step": None}
    steps = WALK[:2] + [("", {"sigma_step": 0.5})] if WALK[i][1] is None else WALK[:i + 1]
    for _, d in steps:
        k |= d
    fl.LIMIT, fl.CAR_SF, fl.CAR_SEGMENTS = k["limit"], k["sf"], k["lengths"]
    fl.HDV_TAU_FIXED, fl.HDV_ASL_FIXED, fl.HDV_SIGMA_FIXED = k["tau"], k["step"], 0.5
    fl.HDV_SIGMA_STEP = k["sigma_step"]
    out = run_once(seed, *DEFAULTS, run_dir, (1.0, 0.0, 0.0, 0.0, 0.0), geom=k["geom"], step=k["step"])
    return {"walk": WALK[i][0], **out}


# V179 step-length check on the V139-like human plant (WALK[0])
VERIFY = {"euler_0.25": (0.25, False), "euler_0.2": (0.2, False), "ballistic_0.5": (0.5, True),
          "ballistic_0.1": (0.1, True)}


def verify_one(seed: int, name: str, run_dir: Path) -> dict:
    step, ballistic = VERIFY[name]
    k = dict(WALK[0][1])
    fl.LIMIT, fl.CAR_SF, fl.CAR_SEGMENTS = k["limit"], k["sf"], k["lengths"]
    fl.HDV_TAU_FIXED, fl.HDV_ASL_FIXED, fl.HDV_SIGMA_FIXED, fl.HDV_SIGMA_STEP = k["tau"], step, 0.5, None
    out = run_once(seed, *DEFAULTS, run_dir, (1.0, 0.0, 0.0, 0.0, 0.0), geom=k["geom"], step=step,
                   ballistic=ballistic)
    return {"verify": name, **out}


def batch(out: Path, seeds: list, workers: int, stage: int = 1) -> None:
    (out / "runs").mkdir(parents=True, exist_ok=True)
    env = clean_sumo_env()
    jobs = [(sd, c, m, a, s) for (c, m, a, s) in grid(stage) for sd in seeds
            if not (out / "runs" / f"{_name(c, m, a, s)}_s{sd}.json").exists()]
    print(f"{len(jobs)} runs, cpu {cal._cpu_util():.0f} %", flush=True)

    def one(j):
        sd, c, m, a, s = j
        while cal._cpu_util(1.0) > 90.0:          # CLAUDE.md CPU rule: launch only below 90 %
            time.sleep(30)
        r = subprocess.run(["nice", "-n", "10", PYTHON_BIN, "-m", "v5b.fleet.calib", "one", "--seed", str(sd),
                            "--c", str(c), "--merge", m, "--accel", str(a), "--asl-scale", str(s),
                            "--out", str(out / "runs" / f"{_name(c, m, a, s)}_s{sd}.json")],
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


def analyse(out: Path, stage: int = 1) -> dict:
    runs = [json.loads(f.read_text()) for f in sorted((out / "runs").glob("*.json"))]
    rows = []
    for (c, m, a, s) in grid(stage):
        rs = [r for r in runs if (r["c"], r["merge"], r["accel"], r.get("asl_scale", 1.0)) == (c, m, a, s)]
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
        rows.append({"c": c, "merge": m, "accel": a, "asl_scale": s, "n": len(rs), "breakdowns": len(drops),
                     "median_drop": med_drop, "drop_in_band_share": round(in_band, 2), "median_qdf": med_qdf,
                     "median_pre": float(np.median([r["pre"] for r in rs if r["pre"] is not None])) if drops else None,
                     "collisions": sum(r["collisions"] for r in rs), "teleports": sum(r["teleports"] for r in rs),
                     "emergency_braking_median": float(np.median([r["emergency_braking"] for r in rs])),
                     "tau_mean": rs[0]["tau_mean"], "pass": ok,
                     "non_default": sum(x != y for x, y in zip((c, m, a, s), STAGE_DEFAULTS[stage]))})
    passing = [r for r in rows if r["pass"]]
    chosen = min(passing, key=lambda r: (r["non_default"], abs(r["median_drop"] - DROP_AIM), -r["median_qdf"])) \
        if passing else None
    res = {"stage": stage, "rows": rows, "n_pass": len(passing), "chosen": chosen}
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
    o.add_argument("--asl-scale", type=float, default=1.0)
    o.add_argument("--out", required=True)
    b = sub.add_parser("batch")
    b.add_argument("--out", required=True)
    b.add_argument("--seed0", type=int, required=True)
    b.add_argument("--n", type=int, default=10)
    b.add_argument("--workers", type=int, default=30)
    b.add_argument("--stage", type=int, default=1)
    g = sub.add_parser("diag")
    g.add_argument("--seed", type=int, required=True)
    g.add_argument("--name", required=True)
    g.add_argument("--out", required=True)
    w = sub.add_parser("walk")
    w.add_argument("--seed", type=int, required=True)
    w.add_argument("--i", type=int, required=True)
    w.add_argument("--out", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--seed", type=int, required=True)
    v.add_argument("--name", required=True)
    v.add_argument("--out", required=True)
    n = sub.add_parser("analyse")
    n.add_argument("--out", required=True)
    n.add_argument("--stage", type=int, default=1)
    a = ap.parse_args(argv)
    if a.cmd == "one":
        out = Path(a.out)
        res = run_once(a.seed, a.c, a.merge, a.accel, out.parent.parent / "rd", asl_scale=a.asl_scale)
        tmp = out.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(json.dumps(res))
        tmp.replace(out)
    elif a.cmd == "diag":
        out = Path(a.out)
        out.write_text(json.dumps(diag_one(a.seed, a.name, out.parent / "rd")))
    elif a.cmd == "walk":
        out = Path(a.out)
        out.write_text(json.dumps(walk_one(a.seed, a.i, out.parent / "rd")))
    elif a.cmd == "verify":
        out = Path(a.out)
        out.write_text(json.dumps(verify_one(a.seed, a.name, out.parent / "rd")))
    elif a.cmd == "batch":
        batch(Path(a.out), list(range(a.seed0, a.seed0 + a.n)), a.workers, a.stage)
        print(json.dumps(analyse(Path(a.out), a.stage), indent=1))
    else:
        print(json.dumps(analyse(Path(a.out), a.stage), indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
