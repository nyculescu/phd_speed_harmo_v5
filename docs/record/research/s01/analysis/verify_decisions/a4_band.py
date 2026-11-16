"""D5, D6 residuals: band quadratic in mean mainline density for v3w; residuals of X1, X2, S1. Plus raw per-level medians and a
leave-one-level-out check of the fit (its null: band runs predicted from the other band levels)."""
import numpy as np
from base import *
ST = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st/"
rows, T = load()
dc = {}
def dens(r):
    k = r["m_st_file"]
    if k not in dc:
        z = np.load(ST + k); dc[k] = float(z["n"].sum() / 1500.0 / (z["n"].shape[1] * 0.05))
    return dc[k]
BAND = [4500.0, 5000.0, 5250.0, 5500.0, 6000.0]
def series(cell, q, names, k):
    return arm_series(T, cell, names, q, lambda r: derived(r)[k]), arm_series(T, cell, names, q, dens)
for gname, names in [("v3w", ARMS["v3w"]), ("os1_15_10", ["os1_15_10"]), ("3e", ["3e"]), ("p333", ["p333"])]:
    keys = ["conf_med", "rev_share", "ent", "share3"] if gname == "v3w" else ["share3"]
    for k in keys:
        xb, yb, lvl = [], [], []
        for q in BAND:
            y, x = series("B", q, names, k)
            for s in y: xb.append(x[s]); yb.append(y[s]); lvl.append(q)
        xb, yb, lvl = map(np.array, (xb, yb, lvl))
        c = np.polyfit(xb, yb, 2)
        # null: leave one band level out, residual of the left-out level
        loo = []
        for q in BAND[1:-1]:
            m = lvl != q; cc = np.polyfit(xb[m], yb[m], 2); loo.append(np.median(yb[~m] - np.polyval(cc, xb[~m])))
        out = [f"{gname} {k}: band n={len(xb)} dens {xb.min():.1f}-{xb.max():.1f}; interior LOO residual medians {np.round(loo,3).tolist()}"]
        for cell, q in [("X1", 5300.0), ("X2", 5300.0), ("B", 3500.0), ("B", 7000.0)]:
            if gname in ("v3w",) or True:
                try:
                    y, x = series(cell, q, names, k)
                except KeyError:
                    continue
                if not y: continue
                res = [y[s] - np.polyval(c, x[s]) for s in y]
                out.append(f"  {cell}{q:.0f}: dens med {np.median(list(x.values())):.1f}, value med {np.median(list(y.values())):.3f}, pred at med dens {np.polyval(c, np.median(list(x.values()))):.3f}, residual {fmt(boot_median(res))}")
        print("\n".join(out))
# raw per-level medians v3w
for k in ["conf_med", "rev_share"]:
    print(k, {f"{c}{q:.0f}": round(float(np.median(list(series(c, q, ARMS['v3w'], k)[0].values()))), 3) for c, q in [("B", 3500.0), ("B", 4500.0), ("B", 6000.0), ("B", 7000.0), ("X1", 5300.0), ("X2", 5300.0)]})
