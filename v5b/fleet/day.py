"""No-control reference days for the fleet plant (V167): capacity, Layer A safety and conflict records.

Day = 24 hourly Poisson rates: ADT x the UK motorway weekday shares (V166 (f), WebTRIS, 10 sites, Tue-Thu autumn 2025),
then drain until empty (cap 2 h). BN4 zipper 100 m, step 0.1 s, the V156-V164 fleet, all green.
Every whole second, each vehicle's same-lane leader comes from getLeader; rear-end TTC = (gap + follower minGap) /
closing speed when the follower is faster. Every TTC below TTC_KEEP is stored (t, follower, leader, TTC, speeds), so the
1.0 / 1.5 / 3.0 s thresholds and the EVT fit (V166 (c)) can be computed afterwards. The SSM device is not used (V166 (a)).
Breakdowns: 'up' loop speed (vehicle-weighted over lanes; intervals without vehicles count as free) below half the
limit for 4 consecutive 30-s intervals; recovery after 4 intervals above.
Pre-queue flow = highest 5-min rolling exit flow in the hour before breakdown; QDF = mean exit flow from 5 min after
breakdown to recovery (the V139 rule adapted to a day with two peaks).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import libsumo as ls
import numpy as np

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.fleet import fleet as fl
from v5b.fleet.smoke import CFG
from v5b.p1c import plant as pl
from v5b.p1c.calibrate import _cpu_util
from v5b.p1c.episode import Sim

# share of daily traffic per hour, 00-01 to 23-24 (%)
UK_WEEKDAY = (0.61, 0.51, 0.52, 0.65, 1.08, 2.35, 5.32, 7.23, 6.71, 6.02, 5.61, 5.70,
              5.89, 6.10, 6.60, 7.21, 7.75, 7.41, 5.70, 4.00, 2.80, 1.96, 1.40, 0.89)
ADT = 20_000
TTC_KEEP = 3.0
LEADER_RANGE = 200.0
DRAIN_CAP = 7200.0


def profile(adt: float = ADT) -> list:
    tot = sum(UK_WEEKDAY)
    return [(3600.0 * h, 3600.0 * (h + 1), adt * s / tot) for h, s in enumerate(UK_WEEKDAY)]


def _up_speed(ids: list) -> float | None:
    n = [ls.inductionloop.getLastIntervalVehicleNumber(i) for i in ids]
    if not sum(n):
        return None
    return round(sum(k * ls.inductionloop.getLastIntervalMeanSpeed(i) for k, i in zip(n, ids) if k) / sum(n), 2)


def _first_steps(coll: list) -> list:
    """One row per collision: SUMO reports a pair again on every step while it overlaps."""
    seen, out = {}, []
    for c in coll:
        k = (c["collider"], c["victim"])
        if k not in seen or c["t"] - seen[k] > 1.0:
            out.append(c)
        seen[k] = c["t"]
    return out


def breakdowns(ser: list) -> list:
    t = np.array([x[0] for x in ser])
    q = np.array([x[1] for x in ser]) * 120.0
    v = np.array([np.nan if x[2] is None else x[2] for x in ser], dtype=float)
    slow = np.nan_to_num(v, nan=fl.LIMIT) < 0.5 * fl.LIMIT
    roll = np.convolve(q, np.ones(10) / 10, mode="valid")
    ends = t[9:]
    out, i, n = [], 0, len(t)
    while i <= n - 4:
        if not slow[i:i + 4].all():
            i += 1
            continue
        tb, j = t[i], i + 4
        while j <= n - 4 and not (~slow[j:j + 4]).all():
            j += 1
        tr = t[j] if j <= n - 4 else t[-1]
        cand = roll[(ends > tb - 3600) & (ends <= tb)]
        m = (t >= tb + 300) & (t <= tr)
        pre = float(cand.max()) if cand.size else None
        qdf = float(q[m].mean()) if m.any() else None
        out.append({"t_break": float(tb), "t_recover": float(tr), "min": round((tr - tb) / 60, 1), "pre": pre,
                    "qdf": qdf, "drop": (1 - qdf / pre) if pre and qdf else None})
        i = j + 4
    return out


def run_day(seed: int, run_dir: Path, adt: float = ADT) -> dict:
    t_w0 = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    d = fl.build_net(CFG)
    dem = fl.FleetDemand(seed, profile(adt), CFG)
    tag = f"day_{CFG.tag()}_adt{adt:g}_s{seed}_pid{os.getpid()}"
    rou, trip = run_dir / f"r_{tag}.rou.xml", run_dir / f"t_{tag}.xml"
    dem.write(rou)
    sim = Sim(d / "net.xml", rou, run_dir, dem, additional=[d / "add.xml"], step_length=CFG.step, seed=seed,
              extra_args=["--tripinfo-output", str(trip)])
    loops = pl.loop_ids(CFG.geom)
    idx = {v.vid: i for i, v in enumerate(dem.veh)}
    cls_i = np.array([fl.CLASSES.index(v.cls) for v in dem.veh], dtype=np.int8)
    sim.start()
    ls.trafficlight.setProgram(pl.TLS_ID, "allgreen")
    rec, ser, coll = [], [], []
    veh_s = closing_s = 0
    min_gap = {}
    t_end = profile(adt)[-1][1]
    drained = False
    while True:
        sim.step()
        coll += [{"t": round(sim.t, 1), "collider": c.collider, "victim": c.victim, "type": c.type, "lane": c.lane,
                  "v_collider": round(c.colliderSpeed, 2), "v_victim": round(c.victimSpeed, 2)}
                 for c in ls.simulation.getCollisions()]
        for vid in ls.simulation.getDepartedIDList():
            min_gap[vid] = ls.vehicle.getMinGap(vid)
        t = sim.t
        if abs(t - round(t)) < 1e-6:
            ids = ls.vehicle.getIDList()
            veh_s += len(ids)
            sp = {vid: ls.vehicle.getSpeed(vid) for vid in ids}
            for vid in ids:
                lead = ls.vehicle.getLeader(vid, LEADER_RANGE)
                if not lead or not lead[0] or lead[0] not in sp:
                    continue
                dv = sp[vid] - sp[lead[0]]
                if dv <= 0:
                    continue
                closing_s += 1
                ttc = (lead[1] + min_gap[vid]) / dv
                if ttc < TTC_KEEP:
                    rec.append((t, idx[vid], idx[lead[0]], ttc, sp[vid], sp[lead[0]]))
            if abs(t / pl.LOOP_PERIOD - round(t / pl.LOOP_PERIOD)) < 1e-6:
                ser.append((round(t, 1), int(sum(ls.inductionloop.getLastIntervalVehicleNumber(i) for i in loops["exit"])),
                            _up_speed(loops["up"]), int(sim.departed), len(ls.simulation.getPendingVehicles())))
        if t >= t_end and sim.departed == sim._total and ls.vehicle.getIDCount() == 0 \
                and not ls.simulation.getPendingVehicles():
            drained = True
            break
        if t >= t_end + DRAIN_CAP - 1e-9:
            break
    res = sim.close(drained=drained)
    log = sim.log_file.read_text(errors="replace")
    delays = {c: [] for c in fl.CLASSES}
    for _, el in ET.iterparse(trip, events=("end",)):
        if el.tag == "tripinfo":
            v = dem.by_id[el.get("id")]
            delays[v.cls].append(float(el.get("duration")) + float(el.get("departDelay"))
                                 - float(el.get("routeLength")) / v.desired)
            el.clear()
    r = np.array(rec, dtype=np.float64).reshape(-1, 6)
    np.savez_compressed(run_dir.parent / f"conflicts_s{seed}.npz", t=r[:, 0].astype(np.float32),
                        follower=r[:, 1].astype(np.int32), leader=r[:, 2].astype(np.int32),
                        ttc=r[:, 3].astype(np.float32), v_f=r[:, 4].astype(np.float32), v_l=r[:, 5].astype(np.float32),
                        cls=cls_i)
    ttc = r[:, 3]
    out = {
        "seed": seed, "adt": adt, "generated": len(dem.veh), "arrived": res["arrived"], "drained": drained,
        "sumo_errors": log.count("Error"), "teleports": res["teleports"], "collisions": res["collisions"],
        "collision_pairs": dict(Counter(f"{dem.by_id[c['collider']].cls}>{dem.by_id[c['victim']].cls}" for c in coll
                                        if c["collider"] in dem.by_id and c["victim"] in dem.by_id)),
        "collision_events": _first_steps(coll),
        "emergency_stops": res["emergency_stops"], "emergency_braking_warnings": log.count("performs emergency braking"),
        "breakdowns": breakdowns(ser), "max_pending": res.get("max_pending"),
        "vehicle_seconds": veh_s, "closing_seconds": closing_s,
        "ttc_seconds_below": {f"{x:g}": int((ttc < x).sum()) for x in (0.5, 1.0, 1.5, 2.0, 3.0)},
        "ttc_min": float(ttc.min()) if ttc.size else None,
        "delay_mean_by_class": {c: round(float(np.mean(x)), 1) if x else None for c, x in delays.items()},
        "series": ser, "health": res["health"]["status"], "hash": res["hash"], "wall_s": round(time.time() - t_w0, 1),
    }
    sim.log_file.replace(run_dir.parent / f"sumo_s{seed}.log")
    for f in (rou, trip, sim.stat_file):
        f.unlink(missing_ok=True)
    return out


def batch(out: Path, seeds: list, workers: int) -> None:
    out.mkdir(parents=True, exist_ok=True)
    env = clean_sumo_env()
    print(f"{len(seeds)} days, cpu {_cpu_util():.0f} %", flush=True)

    def one(s):
        while _cpu_util(1.0) > 90.0:          # CLAUDE.md CPU rule: launch only below 90 %
            time.sleep(30)
        r = subprocess.run(["nice", "-n", "10", PYTHON_BIN, "-m", "v5b.fleet.day", "one", "--seed", str(s),
                            "--out", str(out / f"day_s{s}.json")], cwd=REPO_ROOT, env=env, capture_output=True,
                           text=True)
        return s, r.returncode, r.stderr[-500:] if r.returncode else ""

    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        for s, rc, err in ex.map(one, seeds):
            print(("FAIL" if rc else "done"), s, f"{time.time() - t0:.0f} s", err, flush=True)
    print(f"all done in {time.time() - t0:.0f} s", flush=True)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--seed", type=int, required=True)
    o.add_argument("--adt", type=float, default=ADT)
    o.add_argument("--out", required=True)
    b = sub.add_parser("batch")
    b.add_argument("--out", required=True)
    b.add_argument("--seed0", type=int, required=True)
    b.add_argument("--n", type=int, default=10)
    b.add_argument("--workers", type=int, default=10)
    a = ap.parse_args(argv)
    if a.cmd == "one":
        out = Path(a.out)
        res = run_day(a.seed, out.parent / f"rd_s{a.seed}", a.adt)
        tmp = out.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(json.dumps(res))
        tmp.replace(out)
    else:
        batch(Path(a.out), list(range(a.seed0, a.seed0 + a.n)), a.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
