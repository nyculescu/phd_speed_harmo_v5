"""EXPLORATORY: fuel per km and jerk from the stored S6 rows (rows already read for a verdict)."""
import json
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
L = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
OPP = ["nc", "p333", "os0_10_10", "3E-C_TRUCK", "3E-D_TRUCK", "os1_15_10", "MPC-F"]
want = set(L + OPP); T = {}
for line in open(ROWS):
    r = json.loads(line); c, a = r["name"].split("|", 1)
    if a in want:
        T.setdefault((c, a), {})[r["seed"]] = (r.get("fuel_km"), r.get("jerk_step"), r.get("dist_step"))
seeds = list(range(7480400, 7480640)); n = len(seeds)
rng = np.random.default_rng(20261110); IDX = rng.integers(0, n, (10000, n))
def col(c, a, j): return np.array([np.nan if T[(c, a)][s][j] is None else float(T[(c, a)][s][j]) for s in seeds])
for c in ("TRUCK", "S"):
    print("#####", c, "positive = v3w lower; median paired difference over the opponent median, mean over 5 learners, seed bootstrap 95 %")
    for j, nm in ((0, "fuel_km"),):
        print("  medians", nm, {a: round(float(np.nanmedian(col(c, a, j))), 2) for a in OPP}, "v3w", [round(float(np.nanmedian(col(c, l, j))), 2) for l in L])
        for o in OPP:
            O = col(c, o, j); P = np.array([col(c, l, j) for l in L])
            f = lambda i: np.mean([np.median(O[i] - p[i]) for p in P]) / np.median(O[i]) * 100
            b = np.array([f(i) for i in IDX]); print("    vs %-11s %+.2f [%+.2f, %+.2f]" % (o, f(np.arange(n)), *np.percentile(b, (2.5, 97.5))))
    J = {a: col(c, a, 1) / col(c, a, 2) for a in OPP + L}
    print("  jerk per distance, median, relative to p333:", {a: round(float(np.median(J[a]) / np.median(J["p333"])), 3) for a in OPP}, "v3w", [round(float(np.median(J[l]) / np.median(J["p333"])), 3) for l in L])
