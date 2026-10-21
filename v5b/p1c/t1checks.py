"""P1c gate tool checks T0, T1a-f, T3 on fresh seeds 7,430,050-099 (gate page §3, approved V138), for the
configuration chosen by calibration stage 1 (V139). Criteria are the gate page's; this script only computes them.

Usage: python -m v5b.p1c.t1checks --out DIR --cfg JSON [--workers N]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.p1c import calibrate as cal

Q_NEAR = 2100.0          # near-capacity demand = calibration pre-queue flow (2,106 veh/h), rounded (V139)
CONST_GRID = [1200.0, 1400.0, 1600.0, 1800.0, 2000.0]
S = lambda a, b: list(range(7_430_000 + a, 7_430_000 + b + 1))


def flat(q):
    return [(0.0, 1200.0, q)]


def run_jobs(jobs, out: Path, workers: int) -> dict:
    env = clean_sumo_env()

    def one(j):
        f = out / "runs" / f"{j['name']}.json"
        if not f.exists():
            while cal._cpu_util(1.0) > 90.0:
                time.sleep(30)
            jj = {**j, "out": str(f)}
            r = subprocess.run(["nice", "-n", "10", PYTHON_BIN, "-m", "v5b.p1c.episode", "--job", json.dumps(jj),
                                "--run-dir", str(out / "rd")], cwd=REPO_ROOT, env=env, capture_output=True, text=True)
            if r.returncode:
                print("FAIL", j["name"], r.stderr[-400:], flush=True)
                return j["name"], None
        return j["name"], json.loads(f.read_text())

    with ThreadPoolExecutor(workers) as ex:
        return dict(ex.map(one, jobs))


def job(cfg, arm, inc, q, seed, r_min, name, profile=None):
    return {"cfg": cfg, "arm": arm, "incident": inc, "profile": profile or flat(q), "seed": seed, "r_min": r_min,
            "name": name, "series": True}


def boot_ci(x, B=20000, seed=20261021, level=0.95, stat=np.median):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), (B, len(x)))
    v = stat(x[idx], axis=1)
    a = (1 - level) / 2
    return [float(np.quantile(v, a)), float(np.quantile(v, 1 - a))]


def exit_flow(r, t0, t1):
    ser = [x for x in r["series"] if t0 < x[0] <= t1 + 1e-6]
    return 120.0 * float(np.mean([x[1] for x in ser])) if ser else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args(argv)
    out = Path(a.out)
    (out / "runs").mkdir(parents=True, exist_ok=True)
    cfg = json.loads(a.cfg)
    rep = {"cfg": cfg, "q_near": Q_NEAR}

    # T1a / T1b: ramp, no control, seeds 050-069
    R = run_jobs([job(cfg, "NC", "none", None, s, 600.0, f"t1ab_s{s}", cal.profile()) for s in S(50, 69)], out, a.workers)
    m = [cal.measure(r) for r in R.values() if r]
    drops = [x["drop"] for x in m if x["drop"] is not None]
    qdfs = [x["qdf"] for x in m if x["qdf"] is not None]
    med_drop, med_qdf = float(np.median(drops)), float(np.median(qdfs))
    share = sum(cal.T1A[0] <= d <= cal.T1A[1] for d in drops) / len(m)
    rep["T1a"] = {"median_drop": med_drop, "share_in_range": share, "n_breakdown": len(drops), "n": len(m),
                  "pass": cal.T1A[0] <= med_drop <= cal.T1A[1] and share >= 0.75}
    rep["T1b"] = {"median_qdf": med_qdf, "pass": cal.T1B[0] <= med_qdf <= cal.T1B[1]}
    r_min = round(0.4 * med_qdf / 50.0) * 50.0
    rep["r_min"] = r_min
    print("T1a/T1b", rep["T1a"], rep["T1b"], "r_min", r_min, flush=True)

    jobs = []
    for s in S(70, 79):                                   # T1d meter physics; T1e closure; T1f tuning
        for inc in ("none", "close", "slow"):
            jobs.append(job(cfg, "NC", inc, Q_NEAR, s, r_min, f"nc_{inc}_s{s}"))
            for c in sorted(set(CONST_GRID + [800.0])):
                jobs.append(job(cfg, f"c{c:g}", inc, Q_NEAR, s, r_min, f"c{c:g}_{inc}_s{s}"))
    for s in S(90, 94):                                   # T0
        for c in (800.0, 1200.0, 1600.0):
            jobs.append(job(cfg, f"c{c:g}", "none", Q_NEAR, s, r_min, f"t0_c{c:g}_s{s}"))
    for s in S(95, 99):                                   # T3
        for k in (0, 1):
            jobs.append(job(cfg, "c1200", "close", Q_NEAR, s, r_min, f"t3_k{k}_s{s}"))
    R2 = run_jobs(jobs, out, a.workers)
    allr = [r for r in list(R.values()) + list(R2.values()) if r]

    rep["T1c"] = {"n_runs": len(allr) + 0, "invalid": sum(not r["valid"] for r in allr),
                  "teleports": sum(r["teleports"] for r in allr), "collisions": sum(r["collisions"] for r in allr)}
    rep["T1c"]["pass"] = rep["T1c"]["invalid"] == 0 and rep["T1c"]["teleports"] == 0 and rep["T1c"]["collisions"] == 0

    stops = reds = 0
    for s in S(70, 79):
        for inc in ("none", "close", "slow"):
            for c in (800.0, 1200.0, 1600.0):
                r = R2[f"c{c:g}_{inc}_s{s}"]
                st = r["emerg_by_edge"]["stop"]
                stops += sum(v for e, v in st.items() if e == "2" or e.startswith(":3"))
                reds += 4 * r["n_red_onsets"]
    rep["T1d"] = {"forced_stops": stops, "lane_red_onsets": reds, "share": stops / max(reds, 1),
                  "pass": stops / max(reds, 1) < 0.01}

    diffs = []
    for s in S(70, 79):
        rc, rn = R2[f"nc_close_s{s}"], R2[f"nc_none_s{s}"]
        diffs.append(exit_flow(rn, rc["t_on"], rc["t_off"]) - exit_flow(rc, rc["t_on"], rc["t_off"]))
    ci = boot_ci(diffs)
    stuck = sum("H-R5" in R2[f"nc_close_s{s}"]["health_codes"] for s in S(70, 79))
    rep["T1e"] = {"median_flow_reduction_vph": float(np.median(diffs)), "ci95": ci, "runs_with_H-R5": stuck,
                  "pass": ci[0] > 0 and stuck == 0}

    t1f = {}
    ev = []
    for inc in ("close", "slow"):
        med = {c: float(np.median([R2[f"c{c:g}_{inc}_s{s}"]["delay_s"] for s in S(70, 79)])) for c in CONST_GRID}
        best = min(med, key=med.get)
        for s in S(80, 89):
            ev.append(job(cfg, "NC", inc, Q_NEAR, s, r_min, f"t1f_nc_{inc}_s{s}"))
            ev.append(job(cfg, f"c{best:g}", inc, Q_NEAR, s, r_min, f"t1f_c{best:g}_{inc}_s{s}"))
        t1f[inc] = {"tuning_medians": med, "best": best}
    R3 = run_jobs(ev, out, a.workers)
    for inc, d in t1f.items():
        nc = np.array([R3[f"t1f_nc_{inc}_s{s}"]["delay_s"] for s in S(80, 89)])
        bc = np.array([R3[f"t1f_c{d['best']:g}_{inc}_s{s}"]["delay_s"] for s in S(80, 89)])
        dd = nc - bc
        d.update(nc_median=float(np.median(nc)), best_median=float(np.median(bc)),
                 rel=float(np.median(dd) / np.median(nc)), diff_ci95=boot_ci(dd),
                 ttt_rel=float(np.median([R3[f"t1f_nc_{inc}_s{s}"]["ttt_window_vehh"] - R3[f"t1f_c{d['best']:g}_{inc}_s{s}"]["ttt_window_vehh"] for s in S(80, 89)])
                               / np.median([R3[f"t1f_nc_{inc}_s{s}"]["ttt_window_vehh"] for s in S(80, 89)])))
    rep["T1f"] = {**t1f, "pass": any(d["rel"] >= 0.10 for d in t1f.values())}
    for r in R3.values():
        if r and not (r["valid"] and r["teleports"] == 0 and r["collisions"] == 0):
            rep["T1c"]["pass"] = False

    ratios = [R2[f"t0_c{c:g}_s{s}"]["discharge_ctrl_vph"] / c for s in S(90, 94) for c in (800.0, 1200.0, 1600.0)]
    rep["T0"] = {"median_ratio": float(np.median(ratios)), "min": float(min(ratios)), "max": float(max(ratios)),
                 "wall_s_median": float(np.median([r["wall_s"] for r in allr])),
                 "pass": abs(np.median(ratios) - 1) <= 0.10}
    same = [R2[f"t3_k0_s{s}"]["hash"] == R2[f"t3_k1_s{s}"]["hash"] for s in S(95, 99)]
    rep["T3"] = {"identical": sum(same), "n": len(same), "pass": all(same)}
    rep["all_pass"] = all(rep[k]["pass"] for k in ("T0", "T1a", "T1b", "T1c", "T1d", "T1e", "T1f", "T3"))
    (out / "t1_result.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
