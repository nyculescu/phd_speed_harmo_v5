"""No-control reference days for the fleet plant (V167): capacity, Layer A safety and conflict records.

Day = 24 hourly Poisson rates: ADT x the UK motorway weekday shares (V166 (f), WebTRIS, 10 sites, Tue-Thu autumn 2025),
then drain until empty (cap 2 h). BN4 zipper 100 m (or bn4x, 3 km longer entry, V169), step 0.1 s, the V156-V164
fleet (each CAV class on SUMO's ACC / CACC or on IDM), all green.
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
import dataclasses
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

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, SUMO_BIN, clean_sumo_env
from v5b.fleet import fleet as fl
from v5b.fleet.crash import CrashProcess
from v5b.fleet.smoke import CFG, loop_speed
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


class CrashSim(Sim):
    """episode.Sim with teleporting off, so crashed vehicles stay where they stopped (V163)."""

    def start(self) -> None:
        self.log_file = self.run_dir / f"sumo_pid{os.getpid()}.log"
        self.stat_file = self.run_dir / f"stats_pid{os.getpid()}.xml"
        args = [SUMO_BIN, "-n", str(self.net_file), "-r", str(self.route_file), "--step-length", str(self.dt),
                "--seed", str(self.seed), "--route-steps", "0", "--time-to-teleport", "-1",
                "--collision.action", "warn", "--collision.check-junctions", "true",
                "--no-step-log", "true", "--duration-log.disable", "true",
                "--log", str(self.log_file), "--statistic-output", str(self.stat_file)]
        if self.additional:
            args += ["-a", ",".join(self.additional)]
        ls.start(args + self.extra_args)
        self.loaded += ls.simulation.getLoadedNumber()
        self._started = True
        self._wall0 = time.time()


def _crash(vids: tuple) -> None:
    for vid in vids:
        ls.vehicle.setLaneChangeMode(vid, 0)
        ls.vehicle.setDecel(vid, ls.vehicle.getEmergencyDecel(vid))
        ls.vehicle.setSpeed(vid, 0.0)


def run_day(seed: int, run_dir: Path, adt: float = ADT, cfg: pl.Config = CFG, crash: dict | None = None) -> dict:
    """crash = None (crash-free reference day) or CrashProcess keyword arguments except seed."""
    t_w0 = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    d = fl.build_net(cfg)
    dem = fl.FleetDemand(seed, profile(adt), cfg)
    models = "".join(f"_{c}{m}" for c, m in fl.CAV_MODELS.items())
    tag = f"day_{cfg.tag()}{models}_adt{adt:g}_s{seed}_pid{os.getpid()}"
    rou, trip = run_dir / f"r_{tag}.rou.xml", run_dir / f"t_{tag}.xml"
    dem.write(rou)
    sim = (CrashSim if crash else Sim)(d / "net.xml", rou, run_dir, dem, additional=[d / "add.xml"],
                                       step_length=cfg.step, seed=seed, extra_args=["--tripinfo-output", str(trip)])
    cp = CrashProcess(seed, **crash) if crash else None
    removed, arrived_while_crashed = [], []
    loops = pl.loop_ids(cfg.geom)
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
        if cp is not None and cp.release:
            live = set(ls.vehicle.getIDList())
            for vid in cp.due(t):
                if vid in live:
                    ls.vehicle.remove(vid)
                    removed.append(vid)
                else:
                    arrived_while_crashed.append(vid)
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
                    if cp is not None and cp.observe(t, idx[vid], idx[lead[0]], vid, lead[0], dem.by_id[vid].cls, ttc):
                        cp.events[-1] |= {"lane": ls.vehicle.getLaneID(vid), "pos": round(ls.vehicle.getLanePosition(vid), 1),
                                          "speed": round(sp[vid], 2)}
                        _crash((vid, lead[0]))
            if cp is not None and int(round(t)) % 60 == 0:
                cp.prune(t)
            if abs(t / pl.LOOP_PERIOD - round(t / pl.LOOP_PERIOD)) < 1e-6:
                ser.append((round(t, 1), int(sum(ls.inductionloop.getLastIntervalVehicleNumber(i) for i in loops["exit"])),
                            loop_speed(loops["up"]), int(sim.departed), len(ls.simulation.getPendingVehicles())))
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
        "seed": seed, "adt": adt, "geom": cfg.geom, "cav_models": dict(fl.CAV_MODELS),
        "cav_apparent_decel": fl.CAV_APPARENT_DECEL, "generated": len(dem.veh), "arrived": res["arrived"], "drained": drained,
        "sumo_errors": log.count("Error"), "teleports": res["teleports"], "collisions": res["collisions"],
        "collision_pairs": dict(Counter(f"{dem.by_id[c['collider']].cls}>{dem.by_id[c['victim']].cls}" for c in coll
                                        if c["collider"] in dem.by_id and c["victim"] in dem.by_id)),
        "collision_events": _first_steps(coll),
        "emergency_stops": res["emergency_stops"], "emergency_braking_warnings": log.count("performs emergency braking"),
        "breakdowns": breakdowns(ser), "max_pending": res.get("max_pending"),
        "crash_rule": crash, "crashes": cp.events if cp else [], "removed": len(removed),
        "arrived_while_crashed": arrived_while_crashed, "arrived_plus_removed": res["arrived"] + len(removed),
        "vehicle_seconds": veh_s, "closing_seconds": closing_s,
        "ttc_seconds_below": {f"{x:g}": int((ttc < x).sum()) for x in (0.5, 1.0, 1.5, 2.0, 3.0)},
        "ttc_min": float(ttc.min()) if ttc.size else None,
        "delay_mean_by_class": {c: round(float(np.mean(x)), 1) if x else None for c, x in delays.items()},
        "series": ser, "health": res["health"]["status"], "health_codes": sorted(res["health"]["by_code"]), "hash": res["hash"], "wall_s": round(time.time() - t_w0, 1),
    }
    sim.log_file.replace(run_dir.parent / f"sumo_s{seed}.log")
    for f in (rou, trip, sim.stat_file):
        f.unlink(missing_ok=True)
    return out


def batch(out: Path, seeds: list, workers: int, extra: list) -> None:
    out.mkdir(parents=True, exist_ok=True)
    env = clean_sumo_env()
    print(f"{len(seeds)} days, cpu {_cpu_util():.0f} %", flush=True)

    def one(s):
        while _cpu_util(1.0) > 90.0:          # CLAUDE.md CPU rule: launch only below 90 %
            time.sleep(30)
        r = subprocess.run(["nice", "-n", "10", PYTHON_BIN, "-m", "v5b.fleet.day", "one", "--seed", str(s),
                            "--out", str(out / f"day_s{s}.json"), *extra], cwd=REPO_ROOT, env=env, capture_output=True,
                           text=True)
        return s, r.returncode, r.stderr[-500:] if r.returncode else ""

    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        for s, rc, err in ex.map(one, seeds):
            print(("FAIL" if rc else "done"), s, f"{time.time() - t0:.0f} s", err, flush=True)
    print(f"all done in {time.time() - t0:.0f} s", flush=True)


def _common(p) -> None:
    p.add_argument("--cav-apparent-decel", type=float)
    p.add_argument("--geom", default=CFG.geom)
    for c in fl.CAV_MODELS:
        p.add_argument(f"--{c}-model", default=fl.CAV_MODELS[c])
    p.add_argument("--crash-k", type=float, help="Layer B scale k; no crash process when not given")
    p.add_argument("--crash-u", type=float, default=1.5)
    p.add_argument("--crash-shape", default="linear")
    p.add_argument("--crash-who", default="human")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--seed", type=int, required=True)
    o.add_argument("--adt", type=float, default=ADT)
    o.add_argument("--out", required=True)
    _common(o)
    b = sub.add_parser("batch")
    b.add_argument("--out", required=True)
    b.add_argument("--seed0", type=int, required=True)
    b.add_argument("--n", type=int, default=10)
    b.add_argument("--workers", type=int, default=10)
    _common(b)
    a = ap.parse_args(argv)
    if a.cav_apparent_decel is not None:
        fl.CAV_APPARENT_DECEL = a.cav_apparent_decel
    fl.CAV_MODELS.update({c: getattr(a, f"{c}_model") for c in fl.CAV_MODELS})
    crash = None if a.crash_k is None else {"k": a.crash_k, "u": a.crash_u, "shape": a.crash_shape,
                                             "who": a.crash_who}
    if a.cmd == "one":
        out = Path(a.out)
        res = run_day(a.seed, out.parent / f"rd_s{a.seed}", a.adt, dataclasses.replace(CFG, geom=a.geom), crash)
        tmp = out.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(json.dumps(res))
        tmp.replace(out)
    else:
        extra = ["--geom", a.geom] + [x for c in fl.CAV_MODELS for x in (f"--{c}-model", fl.CAV_MODELS[c])]
        if a.cav_apparent_decel is not None:
            extra += ["--cav-apparent-decel", str(a.cav_apparent_decel)]
        if crash:
            extra += [x for k, v in crash.items() for x in (f"--crash-{k}", str(v))]
        batch(Path(a.out), list(range(a.seed0, a.seed0 + a.n)), a.workers, extra)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
