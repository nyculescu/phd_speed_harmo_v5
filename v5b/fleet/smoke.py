"""Smoke run: does the BN4 plant (V139 calibration: zipper 100 m, step 0.1 s) run with the V156-V161 fleet?

Criteria, fixed before the first run (software checks, not results; seeds follow the tests' 7,400,000 convention):
  S1 load      no SUMO error; loaded = generated = arrived; drained by 7,200 s
  S2 read-back every departed vehicle's libsumo values equal its spec (tau, sigma, action step, length, width,
               speedFactor, truck maxSpeed); libsumo cannot read
               ACC gains back, so tests/test_fleet_sumo.py checks that they change behaviour
  S3 shares    each class count within 4 binomial SDs of its share
  S5 safety    0 teleports and 0 collisions (otherwise reported by class)
  S6 CRN       the same seed twice gives the same result hash
  S8 actuator  ALKS vehicles commanded to 20 m/s for 120 s are never faster than 20.1 m/s once 5 s have passed
               since their command (setSpeed obeys the deceleration limit)
Report-only: S4 ballistic switch (log), S7 breakdown and capacity drop (V139 rule with the 100 km/h free speed),
per-class speeds, emergency-braking warnings, wall time.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from collections import Counter
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest import mock

import libsumo as ls
import numpy as np

from v5b.d2.incidents import incident_window
from v5b.fleet import fleet as fl
from v5b.p1c import calibrate as cal
from v5b.p1c import plant as pl
from v5b.p1c.episode import Sim, _mean

CFG = pl.Config(merge="zip100", cf="Krauss", step=fl.STEP)
CMD_SPEED, CMD_FOR, CMD_SETTLE = 20.0, 120.0, 5.0


def _readback(vid: str, v: fl.VehSpec) -> list:
    bad = []

    def chk(name, got, want, tol=1e-3):
        if want is not None and abs(got - want) > tol:
            bad.append((vid, v.cls, name, got, want))

    chk("length", ls.vehicle.getLength(vid), v.length)
    chk("width", ls.vehicle.getWidth(vid), v.width)
    chk("speedFactor", ls.vehicle.getSpeedFactor(vid), v.sf, 1e-4)
    chk("tau", ls.vehicle.getTau(vid), v.tau)
    if v.cls == "hdv_car":
        chk("sigma", ls.vehicle.getImperfection(vid), v.sigma)
        chk("actionStepLength", ls.vehicle.getActionStepLength(vid), v.asl, 1e-6)
    if v.cls == "truck":
        chk("maxSpeed", ls.vehicle.getMaxSpeed(vid), fl.TRUCK_MAX)
    return bad


def run(seed: int, run_dir: Path, incident: str = "none", command: bool = False, warmup: float = 300.0,
        control: float = 900.0, t_cap: float = 7200.0) -> dict:
    t_w0 = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    d = fl.build_net(CFG)
    dem = fl.FleetDemand(seed, cal.profile("bn4"), CFG)
    tag = f"fleet_{CFG.tag()}_{incident}_cmd{int(command)}_s{seed}_pid{os.getpid()}"
    rou, trip = run_dir / f"r_{tag}.rou.xml", run_dir / f"t_{tag}.xml"
    dem.write(rou)
    sim = Sim(d / "net.xml", rou, run_dir, dem, additional=[d / "add.xml"], step_length=CFG.step, seed=seed,
              extra_args=["--tripinfo-output", str(trip)])
    loops = pl.loop_ids(CFG.geom)
    onset, dur = incident_window(seed, warmup, control)
    sim.start()
    ls.trafficlight.setProgram(pl.TLS_ID, "allgreen")
    bad, speeds, ser = [], {c: [] for c in fl.CLASSES}, []
    cmd_t0 = warmup + 300.0
    cmd = {"n_cmd": 0, "max_over": 0.0, "set": {}}
    slow_on = False
    coll = []
    while True:
        t = sim.t
        if incident == "slow":
            if not slow_on and onset <= t < onset + dur:
                ls.edge.setMaxSpeed(pl.GEOMS[CFG.geom]["bott_edge"], 5.0)
                slow_on = True
            elif slow_on and t >= onset + dur:
                ls.edge.setMaxSpeed(pl.GEOMS[CFG.geom]["bott_edge"], fl.LIMIT)
                slow_on = False
        sim.step()
        coll += [(c.collider, c.victim) for c in ls.simulation.getCollisions()]
        for vid in ls.simulation.getDepartedIDList():
            bad += _readback(vid, dem.by_id[vid])
        ids = ls.vehicle.getIDList()
        if command:
            on = cmd_t0 <= sim.t < cmd_t0 + CMD_FOR
            for vid in ids:
                if dem.by_id[vid].cls not in fl.COMMANDED:
                    continue
                if on and vid not in cmd["set"]:
                    ls.vehicle.setSpeed(vid, CMD_SPEED)
                    cmd["set"][vid] = sim.t
                    cmd["n_cmd"] += 1
                elif on and sim.t - cmd["set"][vid] >= CMD_SETTLE:
                    cmd["max_over"] = max(cmd["max_over"], ls.vehicle.getSpeed(vid) - CMD_SPEED)
            if not on and cmd["set"] and sim.t >= cmd_t0 + CMD_FOR:
                for vid in set(cmd["set"]) & set(ids):
                    ls.vehicle.setSpeed(vid, -1)
                cmd["set"] = {}
        if abs(sim.t - round(sim.t)) < 1e-6 and int(round(sim.t)) % 10 == 0:
            for vid in ids:
                speeds[dem.by_id[vid].cls].append(ls.vehicle.getSpeed(vid))
        if abs(sim.t / pl.LOOP_PERIOD - round(sim.t / pl.LOOP_PERIOD)) < 1e-6:
            ser.append((round(sim.t, 1), int(sum(ls.inductionloop.getLastIntervalVehicleNumber(i) for i in loops["exit"])),
                        round(_mean(loops["e4"], ls.inductionloop.getLastIntervalMeanSpeed), 2),
                        round(_mean(loops["e3"], ls.inductionloop.getLastIntervalMeanSpeed), 2), None,
                        round(_mean(loops["up"], ls.inductionloop.getLastIntervalMeanSpeed), 2)))
        if sim.departed == sim._total and ls.vehicle.getIDCount() == 0 and not ls.simulation.getPendingVehicles():
            drained = True
            break
        if sim.t >= t_cap - 1e-9:
            drained = False
            break
    res = sim.close(drained=drained)
    log = sim.log_file.read_text(errors="replace")
    delays = {c: [] for c in fl.CLASSES}
    for _, el in ET.iterparse(trip, events=("end",)):
        if el.tag == "tripinfo":
            v = dem.by_id[el.get("id")]
            tot = float(el.get("duration")) + float(el.get("departDelay"))
            delays[v.cls].append(tot - float(el.get("routeLength")) / v.desired)
            el.clear()
    counts = {c: sum(v.cls == c for v in dem.veh) for c in fl.CLASSES}
    n = len(dem.veh)
    with mock.patch.object(cal, "FREE", fl.LIMIT):
        drop = cal.measure({"series": ser})
    out = {
        "seed": seed, "incident": incident, "command": command, "generated": n, "loaded": res["loaded"],
        "arrived": res["arrived"], "drained": drained, "sumo_errors": log.count("Error"),
        "S2_mismatches": len(bad), "S2_examples": bad[:5],
        "counts": counts, "S3_z": {c: round((counts[c] - n * p) / np.sqrt(n * p * (1 - p)), 2)
                                   for c, p in zip(fl.CLASSES, fl.SHARES)},
        "hdv_resample_share": round(sum(v.resampled for v in dem.veh if v.cls == "hdv_car")
                                    / max(1, counts["hdv_car"]), 3),
        "teleports": res["teleports"], "collisions": res["collisions"],
        "collision_pairs": dict(Counter(f"{dem.by_id[a].cls}>{dem.by_id[b].cls}" for a, b in coll if a in dem.by_id
                                        and b in dem.by_id).most_common()),
        "emergency_stops": res["emergency_stops"], "emergency_braking_warnings": log.count("performs emergency braking"),
        "ballistic_in_log": "ballistic" in log.lower(),
        "log_warning_lines": sorted({ln[:160] for ln in log.splitlines() if ln.startswith("Warning")
                                     and "collision" not in ln and "emergency" not in ln})[:6],
        "speed_mean_by_class": {c: round(float(np.mean(s)), 2) if s else None for c, s in speeds.items()},
        "delay_mean_by_class": {c: round(float(np.mean(x)), 1) if x else None for c, x in delays.items()},
        "drop": drop, "actuator": {k: (round(v, 3) if isinstance(v, float) else v) for k, v in cmd.items() if k != "set"},
        "hash": res["hash"], "health": res["health"]["status"], "wall_s": round(time.time() - t_w0, 1),
    }
    for f in (rou, trip, sim.log_file, sim.stat_file):
        f.unlink(missing_ok=True)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7_400_000)
    ap.add_argument("--incident", default="none")
    ap.add_argument("--command", action="store_true")
    ap.add_argument("--acc-override", type=float, help="collisionAvoidanceOverride for the ACC class (variant)")
    ap.add_argument("--acc-default", action="store_true", help="SUMO default ACC gains (variant)")
    ap.add_argument("--acc-gapclosing-only", action="store_true",
                    help="original gap-closing gains, default collision avoidance and override (variant)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.acc_default:
        fl.ACC_ORIGINAL.clear()
    elif a.acc_gapclosing_only:
        for k in ("collisionAvoidanceGainSpeed", "collisionAvoidanceGainSpace", "collisionAvoidanceOverride"):
            fl.ACC_ORIGINAL.pop(k)
    elif a.acc_override is not None:
        fl.ACC_ORIGINAL["collisionAvoidanceOverride"] = a.acc_override
    res = run(a.seed, Path(a.out).parent / f"run_{Path(a.out).stem}", a.incident, a.command)
    res["acc_gains"] = dict(fl.ACC_ORIGINAL)
    Path(a.out).write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
