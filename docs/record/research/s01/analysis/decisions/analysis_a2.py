"""(a) Density-matched reading of the decision metrics: each metric against mean mainline density, a quadratic fitted on the
band's runs (cell B, training's slowdown draw, 4,500-6,000 veh/h), and the residuals of X1, X2 (40 seeds) and S1's 3,500 and
7,000 (20 seeds; outside the band's density range, so their prediction is an extrapolation). Median residual, 95 % CI."""
import json
import sys

import numpy as np

from common_dec import GROUPS, load_table, arm_values, HERE, B, SEED_RNG

BAND = [("band", "B", q) for q in (4500.0, 5000.0, 5250.0, 5500.0, 6000.0)]
TARGETS = {"X1": ("test", "X1", 5300.0), "X2": ("test", "X2", 5300.0), "S1_3500": ("s1", "B", 3500.0), "S1_7000": ("s1", "B", 7000.0)}
FIELDS = ("conf_med", "conf_lt05", "entropy", "reversal_share", "applied_share", "excess_per_veh", "share3", "want3", "gap_on")


def boot_med(d):
    d = np.asarray(d, float)
    rng = np.random.default_rng(SEED_RNG)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (B, len(d)))], axis=1), (2.5, 97.5))
    return float(np.median(d)), float(lo), float(hi), len(d)


def main() -> int:
    M = load_table()
    out, n = {}, 0
    for g, names in GROUPS.items():
        out[g] = {}
        for f in FIELDS:
            dx, y = [], []
            for k in BAND:
                D, Y = arm_values(M, k, names, "density"), arm_values(M, k, names, f)
                for s in set(D) & set(Y):
                    dx.append(D[s]); y.append(Y[s])
            dx, y = np.array(dx), np.array(y)
            c = np.polyfit(dx, y, 2)
            res = {"band_range": [float(dx.min()), float(dx.max())], "rmse": float(np.sqrt(np.mean((np.polyval(c, dx) - y) ** 2)))}
            for t, k in TARGETS.items():
                if k not in M or any(nm not in M[k] for nm in names):
                    continue
                D, Y = arm_values(M, k, names, "density"), arm_values(M, k, names, f)
                ss = sorted(set(D) & set(Y))
                res[t] = {"value": boot_med([Y[s] for s in ss]), "pred": float(np.median([np.polyval(c, D[s]) for s in ss])),
                          "resid": boot_med([Y[s] - np.polyval(c, D[s]) for s in ss]), "density": float(np.median([D[s] for s in ss])),
                          "extrapolated": bool(np.median([D[s] for s in ss]) < dx.min() or np.median([D[s] for s in ss]) > dx.max())}
                n += 1
            out[g][f] = res
    out["comparisons"] = n
    (HERE / "analysis_a2.json").write_text(json.dumps(out, indent=1))
    for g in GROUPS:
        print(f"== {g}")
        for f in FIELDS:
            r = out[g][f]
            parts = [f"{t}: {r[t]['value'][0]:.3f} pred {r[t]['pred']:.3f} resid {r[t]['resid'][0]:+.3f} [{r[t]['resid'][1]:+.3f},{r[t]['resid'][2]:+.3f}]{' (extrap)' if r[t]['extrapolated'] else ''}"
                     for t in TARGETS if t in r]
            print(f"  {f:<15} rmse {r['rmse']:.3f} | " + " | ".join(parts))
    print("comparisons", n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
