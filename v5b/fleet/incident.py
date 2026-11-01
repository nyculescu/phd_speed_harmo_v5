"""Incident passing zone (V199) and its calibration against Knoop, Hoogendoorn & Adams (2009).

In SUMO the open lanes beside a crash keep their normal efficiency; in the field they run at about 54 % (Knoop 2009,
Table 5). While a crash blocks a lane, human drivers within ZONE_UP m upstream (along the road, across edges) and
ZONE_DOWN m downstream of the front crashed vehicle drive with their tau multiplied by a factor f; CAVs keep their
gaps. The factor is calibrated on a straight road so that the remaining lanes discharge at η = 0.54 of the plant's
queue discharge. Zone lengths are assumptions.
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

import libsumo as ls
import numpy as np

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.fleet import corridor, fleet as fl
from v5b.fleet.calib import HUMAN_SHARES
from v5b.fleet.smoke import CFG, loop_speed
from v5b.p1c.calibrate import _cpu_util

HUMAN = ("hdv_car", "truck")
ZONE_UP = ZONE_DOWN = 100.0


class PassingZone:
    """Sites are keyed by the front crashed vehicle; a site ends when that vehicle leaves the network."""

    def __init__(self, cls_of, factor: float, up: float = ZONE_UP, down: float = ZONE_DOWN):
        self.cls_of, self.f, self.up, self.down = cls_of, factor, up, down
        self.sites = set()
        self.slowed = {}     # vehicle -> its tau before the zone
        self.n_slowed = 0
        self.pred = {}
        for e in ls.edge.getIDList():
            if e.startswith(":"):
                continue
            for i in range(ls.edge.getLaneNumber(e)):
                for link in ls.lane.getLinks(f"{e}_{i}"):
                    self.pred.setdefault(link[0].rsplit("_", 1)[0], set()).add(e)

    def add(self, vid: str) -> None:
        self.sites.add(vid)

    def _inside(self, live: set) -> set:
        out = set()
        for site in list(self.sites):
            if site not in live:
                self.sites.discard(site)
                continue
            e, pos = ls.vehicle.getRoadID(site), ls.vehicle.getLanePosition(site)
            out.update(v for v in ls.edge.getLastStepVehicleIDs(e)
                       if pos - self.up <= ls.vehicle.getLanePosition(v) <= pos + self.down)
            todo = [(p, pos) for p in self.pred.get(e, ())]     # (edge, distance from its end to the site)
            while todo:
                p, d = todo.pop()
                length = ls.lane.getLength(f"{p}_0")
                out.update(v for v in ls.edge.getLastStepVehicleIDs(p)
                           if length - ls.vehicle.getLanePosition(v) + d <= self.up)
                if length + d < self.up:
                    todo += [(q, length + d) for q in self.pred.get(p, ())]
        return out

    def step(self, blocked) -> None:
        """Call at whole seconds; blocked(vid) is True for crashed vehicles."""
        if self.f == 1.0 or not (self.sites or self.slowed):
            return
        live = set(ls.vehicle.getIDList())
        inside = {v for v in self._inside(live) if self.cls_of(v) in HUMAN and not blocked(v)}
        for vid in list(self.slowed):
            if vid not in inside:
                tau = self.slowed.pop(vid)
                if vid in live and not blocked(vid):
                    ls.vehicle.setTau(vid, tau)
        for vid in inside - set(self.slowed):
            self.slowed[vid] = ls.vehicle.getTau(vid)
            ls.vehicle.setTau(vid, self.slowed[vid] * self.f)
            self.n_slowed += 1


# V199 calibration
Q = {"inc3": 5000.0, "inc2": 3300.0}
WARM, HOLD, SKIP = 600.0, 1800.0, 300.0
QDF_LANE = 1794.0       # plant per-lane queue discharge (V187)
V_CONG = 70.0 / 3.6     # Knoop 2009 congestion threshold
ETA, ETA_TOL, MIN_VALID = 0.54, 0.05, 8
GRID = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)


def run_one(seed: int, f: float, road: str, crash_lane: int, zone: float, run_dir: Path, weather: str = "dry",
            blocker: bool = False, hold: bool = False) -> dict:
    """blocker: a stalled vehicle that stops at the site with normal braking instead of a crash (V213 §5.2 check).
    hold: once stopped, the blocker's stop is replaced by speed 0, as for a crash (V215 A1 diagnostic)."""
    from v5b.fleet.day import CrashSim, _crash      # day imports this module
    t_w0 = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    cfg = dataclasses.replace(fl.apply_plant("v188", CFG), geom=road)
    fl.SHARES = HUMAN_SHARES
    fl.WEATHER = weather
    d = fl.build_net(cfg)
    dem = fl.FleetDemand(seed, [(0.0, WARM + HOLD + 600.0, Q[road])], cfg)
    tag = f"inc_{road}_f{f:g}_l{crash_lane}_z{zone:g}_{weather}_s{seed}_pid{os.getpid()}"
    rou = run_dir / f"r_{tag}.rou.xml"
    dem.write(rou)
    sim = CrashSim(d / "net.xml", rou, run_dir, dem, additional=[d / "add.xml"], step_length=cfg.step, seed=seed,
                   extra_args=[])
    loops = fl.loop_ids(road)
    sim.start()
    pz = PassingZone(lambda v: dem.by_id[v].cls, f, zone, zone)
    lane = f"a_{crash_lane}"
    crashed, t_c, ser, held = None, None, [], False
    while True:
        sim.step()
        t = sim.t
        if hold and crashed is not None and not held and ls.vehicle.isStopped(crashed):
            ls.vehicle.resume(crashed)
            ls.vehicle.setSpeed(crashed, 0.0)
            held = True
        if t_c is None and t >= WARM:
            if blocker:
                crashed = _stall(lane, crash_lane, dem)
            else:
                hit = [v for v in ls.lane.getLastStepVehicleIDs(lane)
                       if dem.by_id[v].cls in HUMAN and ls.vehicle.getLanePosition(v) >= corridor.STRAIGHT_CRASH]
                if hit:
                    crashed = min(hit, key=ls.vehicle.getLanePosition)
                    _crash((crashed,))
            if crashed is not None:
                pz.add(crashed)
                t_c = t
        if abs(t - round(t)) < 1e-6:
            pz.step(lambda v: v == crashed)
            if abs(t / 60 - round(t / 60)) < 1e-6:
                ser.append((round(t), sum(ls.inductionloop.getLastIntervalVehicleNumber(i) for i in loops["dn"]),
                            loop_speed(loops["upq"])))
        if t_c is not None and t >= t_c + HOLD - 1e-9:
            break
    res = sim.close(drained=False)
    log = sim.log_file.read_text(errors="replace")
    win = [(tt, n, v) for tt, n, v in ser if tt - 60 >= t_c + SKIP]
    q = 3600.0 * sum(n for _, n, _ in win) / (60.0 * len(win))
    cong = sum(v is None or v < V_CONG for _, _, v in win) / len(win)
    n = corridor.STRAIGHT[road]
    out = {"seed": seed, "f": f, "road": road, "crash_lane": crash_lane, "zone": zone, "weather": weather, "t_crash": t_c,
           "blocker": blocker, "hold": hold, "held": held,
           "crash_pos": corridor.STRAIGHT_CRASH, "discharge_vph": round(q, 1), "eta": round(q / ((n - 1) * QDF_LANE), 4),
           "F": round(q / (n * QDF_LANE), 4), "congested_share": round(cong, 3), "valid": cong >= 0.9,
           "minutes": len(win), "slowed": pz.n_slowed, "collisions": res["collisions"], "teleports": res["teleports"],
           "emergency_braking": log.count("performs emergency braking"), "sumo_errors": log.count("Error"),
           "series": ser, "wall_s": round(time.time() - t_w0, 1)}
    sim.log_file.unlink(missing_ok=True)
    for p in (rou, sim.stat_file):
        p.unlink(missing_ok=True)
    try:
        run_dir.rmdir()
    except OSError:
        pass
    return out


def _stall(lane: str, idx: int, dem) -> str | None:
    """The human vehicle nearest to the site that can stop there at its own decel with 10 m to spare."""
    x0 = corridor.STRAIGHT_CRASH
    cand = sorted(((ls.vehicle.getLanePosition(v), v) for v in ls.lane.getLastStepVehicleIDs(lane)
                   if dem.by_id[v].cls in HUMAN and ls.vehicle.getLanePosition(v)
                   <= x0 - ls.vehicle.getSpeed(v) ** 2 / (2.0 * ls.vehicle.getDecel(v)) - 10.0), reverse=True)
    for _, v in cand:
        try:
            ls.vehicle.setStop(v, "a", pos=x0, laneIndex=idx, duration=HOLD + 900.0)
        except ls.TraCIException:
            continue
        ls.vehicle.setLaneChangeMode(v, 0)
        return v
    return None


def _name(f, road, lane, zone, weather="dry", blocker=False, hold=False) -> str:
    return (f"{road}_f{f:g}_l{lane}_z{zone:g}" + ("" if weather == "dry" else f"_{weather}")
            + ("_blk" if blocker else "") + ("_hold" if hold else ""))


def batch(out: Path, jobs: list, workers: int) -> None:
    """jobs: (seed, f, road, crash lane, zone, weather, blocker, hold)."""
    (out / "runs").mkdir(parents=True, exist_ok=True)
    jobs = [j for j in jobs if not (out / "runs" / f"{_name(*j[1:])}_s{j[0]}.json").exists()]
    env = clean_sumo_env()
    print(f"{len(jobs)} runs, cpu {_cpu_util():.0f} %", flush=True)

    def one(j):
        sd, f, road, lane, zone, weather, blk, hold = j
        while _cpu_util(1.0) > 90.0:          # CLAUDE.md CPU rule: launch only below 90 %
            time.sleep(30)
        r = subprocess.run(["nice", "-n", "10", PYTHON_BIN, "-m", "v5b.fleet.incident", "one", "--seed", str(sd),
                            "--f", str(f), "--road", road, "--lane", str(lane), "--zone", str(zone),
                            "--weather", weather, *(["--blocker"] if blk else []), *(["--hold"] if hold else []),
                            "--out", str(out / "runs" / f"{_name(f, road, lane, zone, weather, blk, hold)}_s{sd}.json")],
                           cwd=REPO_ROOT, env=env, capture_output=True, text=True)
        return j, r.returncode, r.stderr[-300:] if r.returncode else ""

    t0 = time.time()
    with ThreadPoolExecutor(workers) as ex:
        for i, (j, rc, err) in enumerate(ex.map(one, jobs), 1):
            if rc:
                print("FAIL", j, err, flush=True)
            if i % 10 == 0:
                print(f"{i}/{len(jobs)} done, {time.time() - t0:.0f} s", flush=True)
    print(f"all done in {time.time() - t0:.0f} s", flush=True)


def analyse(out: Path) -> dict:
    rows = [json.loads(p.read_text()) for p in sorted((out / "runs").glob("*.json"))]
    groups = {}
    for r in rows:
        groups.setdefault(_name(r["f"], r["road"], r["crash_lane"], r["zone"], r.get("weather", "dry"),
                                r.get("blocker", False), r.get("hold", False)), []).append(r)
    rng = np.random.default_rng(0)
    summ = {}
    for k, rs in sorted(groups.items()):
        ok = [r for r in rs if r["valid"]]
        e = np.array([r["eta"] for r in ok])
        ci = (np.percentile(np.median(rng.choice(e, (10000, e.size)), axis=1), [2.5, 97.5]).round(4).tolist()
              if e.size else None)
        summ[k] = {"f": rs[0]["f"], "road": rs[0]["road"], "crash_lane": rs[0]["crash_lane"], "zone": rs[0]["zone"],
                   "weather": rs[0].get("weather", "dry"), "blocker": rs[0].get("blocker", False),
                   "n": len(rs), "n_valid": len(ok), "eta_median": float(np.median(e)) if e.size else None,
                   "eta_ci95": ci, "F_median": float(np.median([r["F"] for r in ok])) if ok else None,
                   "discharge_median": float(np.median([r["discharge_vph"] for r in ok])) if ok else None,
                   "collisions": sum(r["collisions"] for r in rs), "teleports": sum(r["teleports"] for r in rs),
                   "emergency_braking": sum(r["emergency_braking"] for r in rs),
                   "sumo_errors": sum(r["sumo_errors"] for r in rs)}
    main = [s for s in summ.values() if s["road"] == "inc3" and s["crash_lane"] == 0 and s["zone"] == ZONE_UP
            and s["weather"] == "dry" and s["eta_median"] is not None]
    best = min(main, key=lambda s: abs(s["eta_median"] - ETA), default=None)
    passed = best is not None and abs(best["eta_median"] - ETA) <= ETA_TOL and best["n_valid"] >= MIN_VALID
    res = {"target_eta": ETA, "tol": ETA_TOL, "chosen": best, "pass": passed, "groups": summ}
    (out / "analysis.json").write_text(json.dumps(res, indent=1))
    for k, s in summ.items():
        print(k, {x: s[x] for x in ("n_valid", "eta_median", "eta_ci95", "F_median", "discharge_median", "collisions",
                                    "teleports", "emergency_braking")})
    print("chosen", best and best["f"], "pass", passed)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--seed", type=int, required=True)
    o.add_argument("--f", type=float, required=True)
    o.add_argument("--road", default="inc3")
    o.add_argument("--lane", type=int, default=0)
    o.add_argument("--zone", type=float, default=ZONE_UP)
    o.add_argument("--weather", default="dry")
    o.add_argument("--blocker", action="store_true", help="stalled vehicle instead of a crash (V213 §5.2)")
    o.add_argument("--hold", action="store_true", help="hold the stopped blocker at speed 0 (V215 A1)")
    o.add_argument("--out", required=True)
    b = sub.add_parser("batch")
    b.add_argument("--out", required=True)
    b.add_argument("--seed0", type=int, required=True)
    b.add_argument("--n", type=int, default=10)
    b.add_argument("--workers", type=int, default=20)
    b.add_argument("--f", default=",".join(f"{x:g}" for x in GRID))
    b.add_argument("--road", default="inc3")
    b.add_argument("--lane", type=int, default=0)
    b.add_argument("--zone", type=float, default=ZONE_UP)
    b.add_argument("--weather", default="dry", help="comma-separated weather states")
    b.add_argument("--blocker", action="store_true")
    b.add_argument("--hold", action="store_true")
    a_ = sub.add_parser("analyse")
    a_.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "one":
        out = Path(a.out)
        r = run_one(a.seed, a.f, a.road, a.lane, a.zone, out.parent.parent / f"rd_s{a.seed}_pid{os.getpid()}",
                    a.weather, a.blocker, a.hold)
        tmp = out.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(json.dumps(r))
        tmp.replace(out)
    elif a.cmd == "batch":
        jobs = [(sd, float(f), a.road, a.lane, a.zone, w, a.blocker, a.hold) for w in a.weather.split(",") for f in a.f.split(",")
                for sd in range(a.seed0, a.seed0 + a.n)]
        batch(Path(a.out), jobs, a.workers)
    else:
        analyse(Path(a.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
