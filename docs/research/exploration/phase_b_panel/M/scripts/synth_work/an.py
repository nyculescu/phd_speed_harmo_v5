"""EXPLORATORY, read-only: Screen M synthesis checks on stored S6 rows. Median of paired differences, percentile bootstrap."""
import pickle, sys
import numpy as np
T = pickle.load(open(sys.argv[1], "rb"))
rng = np.random.default_rng(20261110)
LEARN = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
seeds = sorted(T["S|p333"])
n = len(seeds)
IDX = rng.integers(0, n, (20000, n))
def ci(x, lev):
    b = np.median(np.asarray(x, float)[IDX], axis=1)
    a = (100 - lev) / 2
    return np.percentile(b, a), np.percentile(b, 100 - a)
col = lambda nm, k: np.array([T[nm][s][k] for s in seeds], float)
print("seeds", n, seeds[0], seeds[-1])
for cond in ("S", "TRUCK"):
    P = col(f"{cond}|p333", "d"); med = np.median(P)
    print(f"\n{cond}: p333 median all_delay {med:.0f}; collisions median {np.median(col(f'{cond}|p333','col')):.1f} mean {np.mean(col(f'{cond}|p333','col')):.2f}")
    def parts(nm):
        out = {k: [] for k in ("E", "M1", "M2", "Q", "P21", "P54")}
        for s in seeds:
            r = T[nm][s]; dl, ds = r["dl"], r["ds"]
            rate = lambda g: dl[g] / (ds[g] / 1000.0)
            m1 = dl["3a"] - rate("2") * ds["3a"] / 1000.0
            m2 = dl["4a"] - rate("3") * ds["4a"] / 1000.0
            q = dl.get("pending_ramp", 0.0) + dl.get("pending_ramp2", 0.0)
            out["E"].append(100 * (m1 + m2 + q) / r["d"]); out["M1"].append(100 * m1 / r["d"]); out["M2"].append(100 * m2 / r["d"]); out["Q"].append(100 * q / r["d"])
            out["P21"].append(100 * (dl["2"] - rate("1") * ds["2"] / 1000.0) / r["d"])
            out["P54"].append(100 * (dl["5"] - rate("4") * ds["5"] / 1000.0) / r["d"])
        return {k: np.array(v) for k, v in out.items()}
    pp = parts(f"{cond}|p333")
    for k, v in pp.items():
        print(f"  {k:4s} median {np.median(v):6.2f}  95 %% [%.2f, %.2f]  97.5 %% [%.2f, %.2f]" % (ci(v, 95) + ci(v, 97.5)))
    print("  E share of seeds below 5 %%: %.1f" % (100 * np.mean(pp["E"] < 5)))
    if cond != "S":
        continue
    print("  keys in dl:", sorted(T["S|p333"][seeds[0]]["dl"]))
    rows = []
    for nm in sorted(T):
        c, a = nm.split("|", 1)
        if c != cond or a == "p333" or a in LEARN:
            continue
        d = 100.0 * (P - col(nm, "d")) / med
        lo, hi = ci(d, 97.5); lo95, hi95 = ci(d, 95)
        rows.append((np.median(d), a, lo, hi, lo95, hi95, d.std(ddof=1), int((d == 0).sum()), np.median(col(nm, "col"))))
    print("  arm: edge vs p333 %, 97.5 % CI, 95 % CI, paired SD %, identical seeds, median collisions")
    for m, a, lo, hi, lo95, hi95, sd, same, cc in sorted(rows, reverse=True):
        print(f"  {a:18s} {m:+7.2f} [{lo:+7.2f}, {hi:+7.2f}] 95: [{lo95:+7.2f}, {hi95:+7.2f}] sd {sd:5.1f} same {same:3d} col {cc:.1f}")
    for nm in ("S|p333", "S|nc"):
        print(" ", nm, "lane speeds km/h:", {k: round(float(np.median(col(nm, k))), 1) for k in ("v_3_0", "v_4a_1", "v_3_1", "v_3_2")},
              "lane-0 share of edge-3 veh-s:", round(float(np.median(col(nm, "n_3_0") / (col(nm, "n_3_0") + col(nm, "n_3_1") + col(nm, "n_3_2")))), 3),
              "end_stop2", np.median(col(nm, "end2")), "stuck max", np.nanmax(col(nm, "stuck")))
    print("  p333 mean level index:", {x: round(float(np.median([T["S|p333"][s]["lv_" + x] for s in seeds if "lv_" + x in T["S|p333"][s]])), 2) for x in ("1", "3", "4a", "r2", "rj2")})
    print("  ctrl p333:", T["S|p333"][seeds[0]]["ctrl"])
