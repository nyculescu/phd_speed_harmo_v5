"""Weather regimes (V204): calibration of the human tau factor g per wet state on the lane-drop road ld32.

Protocol `docs/research/weather_evidence_v0.md` §4. Rain scales human tau by g and caps each human's desired speed at
SAF × the dry desired speed (fleet.weather). g is fitted so that the paired wet/dry queue discharge ratio equals the
SHRP 2-L08 capacity factor, then confirmed on fresh seeds. Teleporting is off, as on the plant.
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
from v5b.fleet import fleet as fl
from v5b.fleet.calib import HUMAN_SHARES, lanes_out
from v5b.fleet.day import CrashSim
from v5b.fleet.smoke import CFG, loop_speed
from v5b.p1c import calibrate as cal
from v5b.p1c import plant as pl
from v5b.p1c.calibrate import _cpu_util

CAF = {"medium": 0.926, "heavy": 0.871, "heavy_hcm": 0.859}
STATE_OF = {"dry": "dry", "medium": "medium", "heavy": "heavy", "heavy_hcm": "heavy"}
GRID = tuple(round(1.0 + 0.05 * i, 2) for i in range(11))
WARM, RAMP, HOLD = 300.0, 1200.0, 3600.0
T_CAP = 10800.0             # V205: 7,200 s would not drain a heavy-rain queue in time
V_BREAK = 50.0 / 3.6
QDF_SKIP, QDF_LEN = 300.0, 1200.0
FIT_SEEDS = range(7_431_000, 7_431_020)
CONFIRM_SEEDS = range(7_431_020, 7_431_050)
TOL, MIN_VALID = 0.02, 0.8
PLANT_SEEDS = range(7_431_080, 7_431_110)


def profile(k: int) -> list:
    q0, q1 = (x * k for x in cal.RAMPS["bn4"])
    n = int(RAMP // 60)
    return ([(0.0, WARM, q0)] + [(WARM + 60 * i, WARM + 60 * (i + 1), q0 + (q1 - q0) * (i + 0.5) / n) for i in range(n)]
            + [(WARM + RAMP, WARM + RAMP + HOLD, q1)])


def measure(ser: list, k: int) -> dict:
    """Breakdown (4 × 30 s below 50 km/h at 'up'), pre-queue flow, QDF over a fixed window, drop, critical values."""
    t = np.array([x[0] for x in ser])
    q = np.array([x[1] for x in ser]) * 120.0 / k
    v = np.array([np.nan if x[2] is None else x[2] for x in ser])
    occ = np.array([x[3] for x in ser])
    q_up = np.array([x[4] for x in ser]) * 120.0
    slow = v < V_BREAK
    tb = next((t[i] for i in range(len(t) - 3) if t[i] > WARM and slow[i:i + 4].all()), None)
    out = {"breakdown_s": None if tb is None else float(tb), "pre": None, "qdf": None, "drop": None, "valid": False,
           "v_crit": None, "occ_crit": None, "dens_crit": None,
           "share_40_60": float(np.mean((v >= 40 / 3.6) & (v <= 60 / 3.6))) if v.size else None}
    if tb is None:
        return out
    roll = np.convolve(q, np.ones(10) / 10, mode="valid")
    ok = (t[9:] > WARM) & (t[9:] <= tb)
    if ok.any():
        j = int(np.flatnonzero(ok)[np.argmax(roll[ok])])
        w = slice(j, j + 10)
        vc = float(np.nanmean(v[w]))
        out |= {"pre": float(roll[j]), "v_crit": vc, "occ_crit": float(occ[w].mean()),
                "dens_crit": float(q_up[w].mean() / (3.6 * vc)) if vc > 0 else None}
    a, b = tb + QDF_SKIP, tb + QDF_SKIP + QDF_LEN
    m = (t > a) & (t <= b)
    out["valid"] = bool(b <= WARM + RAMP + HOLD and m.sum() == int(QDF_LEN / 30))
    out["qdf"] = float(q[m].mean()) if m.any() else None
    if out["pre"] and out["qdf"]:
        out["drop"] = 1 - out["qdf"] / out["pre"]
    return out


def run_one(seed: int, state: str, g: float, run_dir: Path, mix: bool = False, cav: bool = False) -> dict:
    """mix: the full V160-V161 fleet (protocol §5.1); cav: CAVs get the human factors (§5.5)."""
    t_w0 = time.time()
    run_dir.mkdir(parents=True, exist_ok=True)
    cfg = fl.apply_plant("v188", CFG)
    if not mix:
        fl.SHARES = HUMAN_SHARES
    fl.WEATHER, fl.WEATHER_G, fl.WEATHER_CAV = STATE_OF[state], g, cav
    d = fl.build_net(cfg)
    k = lanes_out(cfg.geom)
    dem = fl.FleetDemand(seed, profile(k), cfg)
    tag = f"wx_{state}_g{g:g}_s{seed}_pid{os.getpid()}"
    rou = run_dir / f"r_{tag}.rou.xml"
    dem.write(rou)
    sim = CrashSim(d / "net.xml", rou, run_dir, dem, additional=[d / "add.xml"], step_length=cfg.step, seed=seed,
                   extra_args=[])
    loops = fl.loop_ids(cfg.geom)
    sim.start()
    fl.all_green(cfg.geom)
    seen, ser, drained = {}, [], False
    while sim.t < T_CAP - 1e-9:
        sim.step()
        if sim.t <= WARM:
            for i in loops["up"]:
                for vid in ls.inductionloop.getLastStepVehicleIDs(i):
                    seen.setdefault(vid, ls.vehicle.getSpeed(vid))
        if abs(sim.t / pl.LOOP_PERIOD - round(sim.t / pl.LOOP_PERIOD)) < 1e-6:
            ser.append((round(sim.t, 1), int(sum(ls.inductionloop.getLastIntervalVehicleNumber(i) for i in loops["exit"])),
                        loop_speed(loops["up"]),
                        float(np.mean([ls.inductionloop.getLastIntervalOccupancy(i) for i in loops["up"]])),
                        int(sum(ls.inductionloop.getLastIntervalVehicleNumber(i) for i in loops["up"]))))
        if sim.departed == sim._total and ls.vehicle.getIDCount() == 0 and not ls.simulation.getPendingVehicles():
            drained = True
            break
    res = sim.close(drained=drained)
    log = sim.log_file.read_text(errors="replace")
    sp = np.array([x for x in seen.values() if x > 0])
    out = {"seed": seed, "state": state, "g": g, "saf": fl.WEATHER_STATES[STATE_OF[state]][1], "mix": mix, "cav": cav,
           **measure(ser, k),
           "v_free_hm": float(len(sp) / np.sum(1 / sp)) if sp.size else None, "n_free": int(sp.size),
           "drained": drained, "t_end": round(sim.t, 1), "collisions": res["collisions"], "teleports": res["teleports"],
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


def _name(state: str, g: float, seed: int) -> str:
    return f"{state}_g{g:g}_s{seed}"


def batch(out: Path, jobs: list, workers: int, extra: tuple = ()) -> None:
    """jobs: (seed, state, g); extra: flags passed to every run (--mix, --cav)."""
    (out / "runs").mkdir(parents=True, exist_ok=True)
    jobs = [j for j in jobs if not (out / "runs" / f"{_name(j[1], j[2], j[0])}.json").exists()]
    env = clean_sumo_env()
    print(f"{len(jobs)} runs, cpu {_cpu_util():.0f} %", flush=True)

    def one(j):
        sd, state, g = j
        while _cpu_util(1.0) > 90.0:          # CLAUDE.md CPU rule: launch only below 90 %
            time.sleep(30)
        r = subprocess.run(["nice", "-n", "10", PYTHON_BIN, "-m", "v5b.fleet.weather", "one", "--seed", str(sd),
                            "--state", state, "--g", str(g), *extra,
                            "--out", str(out / "runs" / f"{_name(state, g, sd)}.json")],
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


def _load(out: Path, state: str, g: float, seeds) -> dict:
    rs = {}
    for s in seeds:
        p = out / "runs" / f"{_name(state, g, s)}.json"
        if p.exists():
            rs[s] = json.loads(p.read_text())
    return rs


def _ratios(dry: dict, wet: dict, key: str = "qdf") -> np.ndarray:
    return np.array([wet[s][key] / dry[s][key] for s in dry if s in wet and dry[s]["valid"] and wet[s]["valid"]
                     and dry[s][key] and wet[s][key]])


def pava_decreasing(y: list) -> list:
    """Least-squares monotone non-increasing fit (pool adjacent violators)."""
    blocks = []
    for v in y:
        blocks.append([v, 1])
        while len(blocks) > 1 and blocks[-2][0] < blocks[-1][0]:
            v2, n2 = blocks.pop()
            v1, n1 = blocks.pop()
            blocks.append([(v1 * n1 + v2 * n2) / (n1 + n2), n1 + n2])
    return [b[0] for b in blocks for _ in range(b[1])]


def fit(out: Path, state: str) -> dict:
    dry = _load(out, "dry", 1.0, FIT_SEEDS)
    med = []
    for g in GRID:
        r = _ratios(dry, _load(out, STATE_OF[state], g, FIT_SEEDS))
        med.append(float(np.median(r)) if r.size else np.nan)
    ok = [i for i, m in enumerate(med) if m == m]
    curve = pava_decreasing([med[i] for i in ok])
    gs = [GRID[i] for i in ok]
    target = CAF[state]
    g_star = None
    for (g0, c0), (g1, c1) in zip(zip(gs, curve), zip(gs[1:], curve[1:])):
        if c0 >= target >= c1 and c0 != c1:
            g_star = round(g0 + (c0 - target) * (g1 - g0) / (c0 - c1), 2)
            break
        if c0 == target:
            g_star = g0
            break
    return {"state": state, "target": target, "grid": list(GRID), "median_ratio": med, "curve": dict(zip(gs, curve)),
            "g_star": g_star, "n_dry_valid": sum(r["valid"] for r in dry.values())}


def confirm(out: Path, state: str, g: float) -> dict:
    dry = _load(out, "dry", 1.0, CONFIRM_SEEDS)
    wet = _load(out, STATE_OF[state], g, CONFIRM_SEEDS)
    r = _ratios(dry, wet)
    rng = np.random.default_rng(0)
    ci = np.percentile(np.median(rng.choice(r, (10000, r.size)), axis=1), [2.5, 97.5]).tolist() if r.size else None
    med = float(np.median(r)) if r.size else None
    vr = np.array([wet[s]["v_free_hm"] / dry[s]["v_free_hm"] for s in dry if s in wet
                   and dry[s]["v_free_hm"] and wet[s]["v_free_hm"]])
    pre = _ratios(dry, wet, "pre")
    n = len(CONFIRM_SEEDS)
    checks = {
        "ci_contains_caf": bool(ci and ci[0] <= CAF[state] <= ci[1]),
        "median_within_tol": bool(med is not None and abs(med - CAF[state]) <= TOL),
        "valid_share": bool(sum(x["valid"] for x in dry.values()) >= MIN_VALID * n
                            and sum(x["valid"] for x in wet.values()) >= MIN_VALID * n),
        "speed_ratio": bool(vr.size and abs(float(np.median(vr)) - fl.WEATHER_STATES[STATE_OF[state]][1]) <= 0.01),
        "clean": all(x["teleports"] == 0 and x["collisions"] == 0 and x["drained"] for x in (*dry.values(), *wet.values())),
    }

    def med_of(rs, key):
        x = [v[key] for v in rs.values() if v.get(key) is not None]
        return float(np.median(x)) if x else None

    return {"state": state, "g": g, "target": CAF[state], "n_pairs": int(r.size), "median_ratio": med, "ci95": ci,
            "speed_ratio_median": float(np.median(vr)) if vr.size else None,
            "pre_ratio_median": float(np.median(pre)) if pre.size else None,
            "drop_wet_median": med_of(wet, "drop"), "drop_dry_median": med_of(dry, "drop"),
            "report": {k: (med_of(wet, k), med_of(dry, k)) for k in ("v_crit", "occ_crit", "dens_crit", "share_40_60")},
            "checks": checks, "pass": all(checks.values()), "n_dry": len(dry), "n_wet": len(wet)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--seed", type=int, required=True)
    o.add_argument("--state", required=True)
    o.add_argument("--g", type=float, required=True)
    o.add_argument("--out", required=True)
    o.add_argument("--mix", action="store_true")
    o.add_argument("--cav", action="store_true")
    b = sub.add_parser("batch")
    b.add_argument("--out", required=True)
    b.add_argument("--stage", choices=("fit", "confirm", "mix", "mixcav"), required=True)
    b.add_argument("--g", help="confirm: state=g pairs, e.g. medium=1.12,heavy=1.27")
    b.add_argument("--workers", type=int, default=30)
    f = sub.add_parser("fit")
    f.add_argument("--out", required=True)
    c = sub.add_parser("confirm")
    c.add_argument("--out", required=True)
    c.add_argument("--g", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "one":
        out = Path(a.out)
        r = run_one(a.seed, a.state, a.g, out.parent.parent / f"rd_s{a.seed}_pid{os.getpid()}", a.mix, a.cav)
        tmp = out.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(json.dumps(r))
        tmp.replace(out)
    elif a.cmd == "batch":
        if a.stage == "fit":
            jobs = [(s, "dry", 1.0) for s in FIT_SEEDS] + [(s, st, g) for st in ("medium", "heavy") for g in GRID
                                                          for s in FIT_SEEDS]
        elif a.stage == "confirm":
            pairs = [x.split("=") for x in a.g.split(",")]
            jobs = [(s, "dry", 1.0) for s in CONFIRM_SEEDS] + [(s, STATE_OF[st], float(g)) for st, g in pairs
                                                              for s in CONFIRM_SEEDS]
        else:      # §5.1 full mix on the plant seeds at the adopted g; §5.5 CAV bound on 10 of them
            seeds = PLANT_SEEDS if a.stage == "mix" else PLANT_SEEDS[:10]
            states = ("dry", "medium", "heavy") if a.stage == "mix" else ("medium", "heavy")
            jobs = [(s, st, fl.WEATHER_STATES[st][0]) for st in states for s in seeds]
        batch(Path(a.out), jobs, a.workers, {"fit": (), "confirm": (), "mix": ("--mix",),
                                             "mixcav": ("--mix", "--cav")}[a.stage])
    elif a.cmd == "fit":
        res = {st: fit(Path(a.out), st) for st in CAF}
        (Path(a.out) / "fit.json").write_text(json.dumps(res, indent=1))
        for st, r in res.items():
            print(st, "g*", r["g_star"], "medians", [None if m != m else round(m, 4) for m in r["median_ratio"]])
    else:
        res = {st: confirm(Path(a.out), st, float(g)) for st, g in (x.split("=") for x in a.g.split(","))}
        (Path(a.out) / "confirm.json").write_text(json.dumps(res, indent=1))
        for st, r in res.items():
            print(st, {k: r[k] for k in ("g", "n_pairs", "median_ratio", "ci95", "speed_ratio_median", "checks", "pass")})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
