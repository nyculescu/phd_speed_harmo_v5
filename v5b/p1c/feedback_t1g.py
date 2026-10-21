"""T1g (docs/research/protocols/p1c_feedback_t1g.md, V148): ALINEA / PI-ALINEA vs no control on BN4, slowdown.

Usage: python -m v5b.p1c.feedback_t1g --out DIR [--workers N]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from v5b.p1c.t1checks import boot_ci, job, run_jobs

CFG = {"merge": "zip100", "cf": "Krauss", "lc_coop": 1.0, "speed_dev": 0.1, "step": 0.5, "geom": "bn4"}
Q, R_MIN = 2100.0, 800.0
KR, OH, EDGES, KP = [20.0, 40.0, 70.0], [10.0, 15.0, 20.0, 25.0, 30.0], ["e4", "e5"], [20.0, 70.0]
EXT = {"KR": {20.0: 10.0, 70.0: 120.0}, "OH": {10.0: 5.0, 30.0: 35.0}}
S = lambda a, b: list(range(7_430_000 + a, 7_430_000 + b + 1))


def laws(kr=KR, oh=OH):
    out = [f"a{k:g}_{o:g}_{e}" for k in kr for o in oh for e in EDGES]
    out += [f"p{p:g}_{k:g}_{o:g}_{e}" for p in KP for k in kr for o in oh for e in EDGES]
    return out


def tune(lawset, out, workers):
    R = run_jobs([job(CFG, L, "slow", Q, s, R_MIN, f"tu_{L}_s{s}") for L in lawset for s in S(180, 189)], out, workers)
    med = {L: float(np.median([R[f"tu_{L}_s{s}"]["delay_s"] for s in S(180, 189)])) for L in lawset}
    best = min(lawset, key=lambda L: (med[L], lawset.index(L)))
    return med, best


def parts(L):
    p = L[1:].split("_")
    return (None, float(p[0]), float(p[1]), p[2]) if L[0] == "a" else (float(p[0]), float(p[1]), float(p[2]), p[3])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args(argv)
    out = Path(a.out)
    (out / "runs").mkdir(parents=True, exist_ok=True)
    base = laws()
    med, best = tune(base, out, a.workers)
    rep = {"n_laws": len(base), "best_first": best, "median_first": med[best]}
    kp, kr, oh, e = parts(best)
    kr2 = KR + [EXT["KR"][kr]] if kr in EXT["KR"] else KR
    oh2 = OH + [EXT["OH"][oh]] if oh in EXT["OH"] else OH
    if kr2 != KR or oh2 != OH:                       # grid adequacy: extend once (protocol step 2)
        ext = [L for L in laws(sorted(kr2), sorted(oh2)) if L not in base]
        m2, _ = tune(ext, out, a.workers)
        med.update(m2)
        allL = base + ext
        best = min(allL, key=lambda L: (med[L], allL.index(L)))
        rep["extended"] = {"KR": sorted(kr2), "OH": sorted(oh2), "n_new": len(ext)}
    rep["best"] = best
    rep["tuning_median_best"] = med[best]
    rep["tuning_top5"] = sorted(med.items(), key=lambda kv: kv[1])[:5]
    ev = []
    for s in S(190, 199):
        for inc in ("slow", "none"):
            ev.append(job(CFG, "NC", inc, Q, s, R_MIN, f"te_nc_{inc}_s{s}"))
            ev.append(job(CFG, best, inc, Q, s, R_MIN, f"te_best_{inc}_s{s}"))
    R = run_jobs(ev, out, a.workers)
    g = lambda arm, inc, k: np.array([R[f"te_{arm}_{inc}_s{s}"][k] for s in S(190, 199)])
    nc, bl = g("nc", "slow", "delay_s"), g("best", "slow", "delay_s")
    dd = nc - bl
    rep["T1g"] = {"nc_median": float(np.median(nc)), "law_median": float(np.median(bl)),
                  "rel": float(np.median(dd) / np.median(nc)), "diff_ci95": boot_ci(dd),
                  "ttt_window_rel": float(np.median(g("nc", "slow", "ttt_window_vehh") - g("best", "slow", "ttt_window_vehh"))
                                          / np.median(g("nc", "slow", "ttt_window_vehh"))),
                  "served_diff_vph": float(np.median(g("best", "slow", "served_ctrl_vph") - g("nc", "slow", "served_ctrl_vph"))),
                  "seeds_better": int((dd > 0).sum()),
                  "clean_day_rel": float(np.median(g("nc", "none", "delay_s") - g("best", "none", "delay_s"))
                                         / np.median(g("nc", "none", "delay_s")))}
    rep["T1g"]["pass"] = bool(rep["T1g"]["rel"] >= 0.10)
    allr = [r for r in R.values() if r]
    rep["artefacts"] = {"invalid": sum(not r["valid"] for r in allr), "teleports": sum(r["teleports"] for r in allr),
                        "collisions": sum(r["collisions"] for r in allr)}
    dflt = lambda o: o.item() if hasattr(o, "item") else str(o)
    (out / "t1g_result.json").write_text(json.dumps(rep, indent=1, default=dflt))
    print(json.dumps(rep, indent=1, default=dflt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
