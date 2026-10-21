"""V146 fair BN4 test, slowdown only: T1a/T1b (gate detector), T1c, T1d, T0, T1f, T3 on seeds 7,430,150-179.
Gate criteria from docs/research/protocols/p1c_gate_t1.md (V138); T1e dropped (V140, V146).

Usage: python -m v5b.p1c.bn4_slow_test --out DIR [--workers N]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from v5b.p1c import calibrate as cal
from v5b.p1c.t1checks import boot_ci, job, run_jobs, r50

CFG = {"merge": "zip100", "cf": "Krauss", "lc_coop": 1.0, "speed_dev": 0.1, "step": 0.5, "geom": "bn4"}
Q_NEAR = 2100.0
S = lambda a, b: list(range(7_430_000 + a, 7_430_000 + b + 1))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args(argv)
    out = Path(a.out)
    (out / "runs").mkdir(parents=True, exist_ok=True)
    rep = {"cfg": CFG, "q_near": Q_NEAR}

    R = run_jobs([job(CFG, "NC", "none", None, s, 600.0, f"t1ab_s{s}", cal.profile("bn4")) for s in S(150, 159)],
                 out, a.workers)
    m = [cal.measure(r) for r in R.values() if r]
    drops = [x["drop"] for x in m if x["drop"] is not None]
    qdfs = [x["qdf"] for x in m if x["qdf"] is not None]
    med_drop = float(np.median(drops)) if drops else None
    med_qdf = float(np.median(qdfs)) if qdfs else None
    share = sum(cal.T1A[0] <= d <= cal.T1A[1] for d in drops) / len(m)
    rep["T1a"] = {"median_drop": med_drop, "share_in_range": share, "n_breakdown": len(drops), "n": len(m),
                  "pass": bool(med_drop is not None and cal.T1A[0] <= med_drop <= cal.T1A[1] and share >= 0.75)}
    rep["T1b"] = {"median_qdf": med_qdf, "pass": bool(med_qdf is not None and cal.T1B[0] <= med_qdf <= cal.T1B[1])}
    qdf = med_qdf or 1950.0
    r_min = r50(0.4 * qdf)
    grid = [r50(f * qdf) for f in (0.6, 0.7, 0.8, 0.9, 1.0)]
    t0r = [r50(f * qdf) for f in (0.4, 0.6, 0.8)]
    rep.update(r_min=r_min, const_grid=grid, t0_rates=t0r)
    print("T1a/b", rep["T1a"], rep["T1b"], "r_min", r_min, "grid", grid, flush=True)

    jobs = []
    for s in S(160, 169):
        for inc in ("none", "slow"):
            jobs.append(job(CFG, "NC", inc, Q_NEAR, s, r_min, f"nc_{inc}_s{s}"))
            for c in sorted(set(grid + t0r)):
                jobs.append(job(CFG, f"c{c:g}", inc, Q_NEAR, s, r_min, f"c{c:g}_{inc}_s{s}"))
    for s in S(160, 164):
        jobs.append(job(CFG, f"c{t0r[1]:g}", "slow", Q_NEAR, s, r_min, f"t3dup_s{s}"))
    R2 = run_jobs(jobs, out, a.workers)

    med = {c: float(np.median([R2[f"c{c:g}_slow_s{s}"]["delay_s"] for s in S(160, 169)])) for c in grid}
    best = min(med, key=med.get)
    ev = []
    for s in S(170, 179):
        ev.append(job(CFG, "NC", "slow", Q_NEAR, s, r_min, f"ev_nc_slow_s{s}"))
        ev.append(job(CFG, f"c{best:g}", "slow", Q_NEAR, s, r_min, f"ev_c{best:g}_slow_s{s}"))
    R3 = run_jobs(ev, out, a.workers)
    allr = [r for r in list(R.values()) + list(R2.values()) + list(R3.values()) if r]
    rep["T1c"] = {"n_runs": len(allr), "invalid": sum(not r["valid"] for r in allr),
                  "teleports": sum(r["teleports"] for r in allr), "collisions": sum(r["collisions"] for r in allr)}
    rep["T1c"]["pass"] = bool(rep["T1c"]["invalid"] == 0 and rep["T1c"]["teleports"] == 0 and rep["T1c"]["collisions"] == 0)

    stops = reds = 0
    for s in S(160, 169):
        for inc in ("none", "slow"):
            for c in t0r:
                r = R2[f"c{c:g}_{inc}_s{s}"]
                stops += sum(v for e, v in r["emerg_by_edge"]["stop"].items() if e == "2" or e.startswith(":3"))
                reds += 4 * r["n_red_onsets"]
    rep["T1d"] = {"forced_stops": stops, "lane_red_onsets": reds, "share": stops / max(reds, 1),
                  "pass": bool(stops / max(reds, 1) < 0.01)}
    ratios = [R2[f"c{c:g}_none_s{s}"]["discharge_ctrl_vph"] / c for s in S(160, 169) for c in t0r]
    rep["T0"] = {"median_ratio": float(np.median(ratios)), "min": float(min(ratios)), "max": float(max(ratios)),
                 "pass": bool(abs(np.median(ratios) - 1) <= 0.10)}

    nc = np.array([R3[f"ev_nc_slow_s{s}"]["delay_s"] for s in S(170, 179)])
    bc = np.array([R3[f"ev_c{best:g}_slow_s{s}"]["delay_s"] for s in S(170, 179)])
    ncw = np.array([R3[f"ev_nc_slow_s{s}"]["ttt_window_vehh"] for s in S(170, 179)])
    bcw = np.array([R3[f"ev_c{best:g}_slow_s{s}"]["ttt_window_vehh"] for s in S(170, 179)])
    dd = nc - bc
    rep["T1f"] = {"tuning_medians": med, "best": best, "nc_median": float(np.median(nc)),
                  "best_median": float(np.median(bc)), "rel": float(np.median(dd) / np.median(nc)),
                  "diff_ci95": boot_ci(dd), "ttt_window_rel": float(np.median(ncw - bcw) / np.median(ncw)),
                  "seeds_better": int((dd > 0).sum()),
                  "tuning_nc_median": float(np.median([R2[f"nc_slow_s{s}"]["delay_s"] for s in S(160, 169)]))}
    rep["T1f"]["pass"] = bool(rep["T1f"]["rel"] >= 0.10)
    same = [R2[f"t3dup_s{s}"]["hash"] == R2[f"c{t0r[1]:g}_slow_s{s}"]["hash"] for s in S(160, 164)]
    rep["T3"] = {"identical": sum(same), "n": len(same), "pass": bool(all(same))}
    rep["all_pass"] = all(rep[k]["pass"] for k in ("T0", "T1a", "T1b", "T1c", "T1d", "T1f", "T3"))
    dflt = lambda o: o.item() if hasattr(o, "item") else str(o)
    (out / "bn4_slow_result.json").write_text(json.dumps(rep, indent=1, default=dflt))
    print(json.dumps(rep, indent=1, default=dflt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
