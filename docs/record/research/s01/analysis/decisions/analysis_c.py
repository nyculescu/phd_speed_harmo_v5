"""(c) Level choice against density and close-following.
1. Share of V2V-on ALKS-seconds at level 3 (0.8 s) against mean mainline density: a quadratic fitted on the band's runs
   (cell B, in-draw slowdowns, 100 arm-mean runs per arm), and X1's and X2's residuals from it (median over 40 seeds, 95 % CI).
   Rules show what a fixed state-to-level map gives under the same comparison (their residual = traffic structure that
   mean density does not capture).
2. In X1 and X2, every arm's share3, mean V2V-on gap, mean commanded level per road, and close-following against no control
   (round 2's effect on ttc_net, 95 % CI)."""
import json
import pickle
import sys

import numpy as np

from common_dec import GROUPS, load_table, arm_values, med_ci, raw, paired_diff, HERE, B, SEED_RNG

BAND = [("band", "B", q) for q in (4500.0, 5000.0, 5250.0, 5500.0, 6000.0)]
X = {"X1": ("test", "X1", 5300.0), "X2": ("test", "X2", 5300.0)}
RULE_ARMS = ["p333", "os1_15_10", "os0_10_10", "os1_10_0", "3e", "3ex1", "3ex2", "lr1000_10_1", "lr1000_16_2", "lr400_13_2", "lr400_16_1",
             "a4400_10_1", "copy", "r4a1", "z33133"]


def boot_med(d):
    d = np.asarray(d, float)
    rng = np.random.default_rng(SEED_RNG)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (B, len(d)))], axis=1), (2.5, 97.5))
    return float(np.median(d)), float(lo), float(hi), len(d)


def main() -> int:
    M = load_table()
    out = {"density_fit": {}, "x_cells": {}}
    n_cmp = 0
    fit_arms = {**GROUPS, "os1_15_10": ["os1_15_10"], "3E-T": ["3e"], "p333": ["p333"]}
    for g, names in fit_arms.items():
        dx, sy, gy = [], [], []
        for k in BAND:
            D, S, G = arm_values(M, k, names, "density"), arm_values(M, k, names, "share3"), arm_values(M, k, names, "gap_on")
            for s in D:
                dx.append(D[s]); sy.append(S[s]); gy.append(G[s])
        dx, sy, gy = map(np.array, (dx, sy, gy))
        cs, cg = np.polyfit(dx, sy, 2), np.polyfit(dx, gy, 2)
        rs = float(np.sqrt(np.mean((np.polyval(cs, dx) - sy) ** 2)))
        res = {"band_density_range": [float(dx.min()), float(dx.max())], "rmse_share3": rs, "n_band": len(dx)}
        for c, k in X.items():
            D, S, G = arm_values(M, k, names, "density"), arm_values(M, k, names, "share3"), arm_values(M, k, names, "gap_on")
            ss = sorted(D)
            res[c] = {"density": boot_med([D[s] for s in ss]), "share3": boot_med([S[s] for s in ss]),
                      "share3_pred": boot_med([np.polyval(cs, D[s]) for s in ss]),
                      "share3_resid": boot_med([S[s] - np.polyval(cs, D[s]) for s in ss]),
                      "gap_on_resid": boot_med([G[s] - np.polyval(cg, D[s]) for s in ss])}
            n_cmp += 2
        out["density_fit"][g] = res
    arms = {**{k: v for k, v in GROUPS.items()}, **{r: [r] for r in RULE_ARMS}}
    for c, k in X.items():
        nc_t, nc_d = arm_values(M, k, ["nc"], "ttc_net"), arm_values(M, k, ["nc"], "all_delay")
        out["x_cells"][c] = {}
        for g, names in arms.items():
            if any(n not in M[k] for n in names):
                continue
            r = {f: med_ci(arm_values(M, k, names, f)) for f in ("share3", "share0", "gap_on", "lv_3", "lv_4a", "lv_4", "lv_5", "density")}
            r["ttc_vs_nc"] = raw(arm_values(M, k, names, "ttc_net"), nc_t, -1)
            r["delay_vs_nc"] = raw(arm_values(M, k, names, "all_delay"), nc_d, -1)
            n_cmp += 2
            out["x_cells"][c][g] = r
    # v3w: X1 vs X2 close-following, paired, and across-arm rank correlation of share3 with the TTC effect
    for g in ("v3w", "os1_15_10", "3E-T", "p333"):
        names = GROUPS.get(g, {"3E-T": ["3e"]}.get(g, [g]))
        out.setdefault("x1_vs_x2_ttc", {})[g] = raw(arm_values(M, X["X1"], names, "ttc_net"), arm_values(M, X["X2"], names, "ttc_net"), -1)
        n_cmp += 1
    for c in X:
        a = out["x_cells"][c]
        s3 = np.array([a[g]["share3"][0] for g in a])
        te = np.array([a[g]["ttc_vs_nc"][0] for g in a])
        rk = lambda v: np.argsort(np.argsort(v))
        out.setdefault("spearman_share3_vs_ttc_effect", {})[c] = {"rho": float(np.corrcoef(rk(s3), rk(te))[0, 1]), "n_arms": len(s3)}
    out["comparisons"] = n_cmp
    (HERE / "analysis_c.json").write_text(json.dumps(out, indent=1))
    f3 = lambda t: f"{t[0]:+.3f} [{t[1]:+.3f},{t[2]:+.3f}]"
    print("density fit (band quadratic): arm | band density range | rmse | X1 dens, share3, pred, resid | X2 dens, share3, pred, resid")
    for g, r in out["density_fit"].items():
        print(f"  {g:<12} {r['band_density_range'][0]:.1f}-{r['band_density_range'][1]:.1f} rmse {r['rmse_share3']:.3f} | "
              + " | ".join(f"{c}: {r[c]['density'][0]:.1f} {r[c]['share3'][0]:.3f} pred {r[c]['share3_pred'][0]:.3f} resid {f3(r[c]['share3_resid'])} gap resid {f3(r[c]['gap_on_resid'])}" for c in X))
    for c in X:
        print(f"== {c}: arm | share3 | gap_on s | lv_3 lv_4a lv_4 lv_5 | TTC vs nc % [CI] | delay vs nc % [CI]")
        for g, r in sorted(out["x_cells"][c].items(), key=lambda kv: -kv[1]["share3"][0]):
            print(f"  {g:<12} {r['share3'][0]:.3f}  {r['gap_on'][0]:.3f}  {r['lv_3'][0]:.2f} {r['lv_4a'][0]:.2f} {r['lv_4'][0]:.2f} {r['lv_5'][0]:.2f}  "
                  f"ttc {r['ttc_vs_nc'][0]:+.1f} [{r['ttc_vs_nc'][1]:+.1f},{r['ttc_vs_nc'][2]:+.1f}]  delay {r['delay_vs_nc'][0]:+.1f} [{r['delay_vs_nc'][1]:+.1f},{r['delay_vs_nc'][2]:+.1f}]")
    print("X1 vs X2 ttc_net (positive = less close-following in X1):", {g: [round(x, 1) for x in v[:3]] for g, v in out["x1_vs_x2_ttc"].items()})
    print("Spearman share3 vs TTC effect across arms:", out["spearman_share3_vs_ttc_effect"], "comparisons", n_cmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
