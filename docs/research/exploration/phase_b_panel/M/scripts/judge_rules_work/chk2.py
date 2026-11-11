"""EXPLORATORY: independent check of the Screen M drafts' stored-row numbers (S6 rows, cell S, 240 paired seeds). Read-only; prints scalars."""
import json
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
REF = 100.0 / 3.6
ARMS = ("p333", "r4a1", "z33133", "grid_r4a2", "grid_z31333", "os0_10_10", "nc")
T = {}
for line in open(ROWS):
    i = line.find('"name": "')
    if i < 0 or not line[i + 9:i + 11] == "S|":
        continue
    arm = line[i + 11:line.index('"', i + 11)]
    if arm not in ARMS:
        continue
    r = json.loads(line)
    tot = lambda p: sum(p.values()) if isinstance(p, dict) else float(np.sum(p))
    vs = {g: tot(p) for g, p in r["m_road_vs"].items()}
    ds = {g: tot(p) for g, p in r["m_road_dist"].items()}
    dl = {g: vs[g] - ds.get(g, 0.0) / REF for g in vs}
    rate = lambda g: dl[g] / (ds[g] / 1000.0)
    m1 = dl["3a"] - rate("2") * ds["3a"] / 1000.0
    m2 = dl["4a"] - rate("3") * ds["4a"] / 1000.0
    q = dl.get("pending_ramp", 0.0) + dl.get("pending_ramp2", 0.0)
    T.setdefault(arm, {})[r["seed"]] = (r["all_delay"], m1, m2, q)
seeds = sorted(T["p333"])
print("seeds", len(seeds), seeds[0], seeds[-1], "arms", sorted(T))
col = lambda a, k=0: np.array([T[a][s][k] for s in seeds], float)
P = col("p333"); med = float(np.median(P))
print("p333 median all_delay %.0f" % med)
rng = np.random.default_rng(424242)
def ci(x, lev, B=10000):
    b = np.median(x[rng.integers(0, len(x), (B, len(x)))], axis=1)
    a = (100 - lev) / 2
    return np.percentile(b, a), np.percentile(b, 100 - a)
E = 100 * (col("p333", 1) + col("p333", 2) + col("p333", 3)) / P
print("merge excess %% of delay: %.2f, 95 %% [%.2f, %.2f], 97.5 %% [%.2f, %.2f]; merge1 %.2f merge2 %.2f" % ((np.median(E),) + ci(E, 95) + ci(E, 97.5) + (np.median(100 * col("p333", 1) / P), np.median(100 * col("p333", 2) / P))))
D = {}
for a in ARMS[1:]:
    d = 100 * (P - col(a)) / med
    D[a] = d
    print("%-12s edge %+.2f 95 %% [%+.2f, %+.2f] 97.5 %% [%+.2f, %+.2f] paired sd %.1f" % ((a, np.median(d)) + ci(d, 95) + ci(d, 97.5) + (d.std(ddof=1),)))
def study(d, n, e, thr, lev, STUD=600, B=1000):
    d0 = d - np.median(d) + e
    a = (100 - lev) / 2
    out = np.zeros(3)
    for _ in range(STUD):
        x = d0[rng.integers(0, len(d0), n)]
        b = np.median(x[rng.integers(0, n, (B, n))], axis=1)
        lo, hi, pt = np.percentile(b, a), np.percentile(b, 100 - a), np.median(x)
        out[0 if (pt >= thr and lo > 0) else 1 if hi < thr else 2] += 1
    return 100 * out / STUD
print("rule: PASS = point >= thr and lower bound > 0; BOUNDED = upper bound < thr; else not shown. Columns PASS/BOUNDED/not shown, %")
for a in ("z33133", "r4a1"):
    for (n, thr, lev, tag) in ((120, 3.0, 97.5, "cheap"), (240, 5.0, 97.5, "rigor"), (360, 3.0, 99.6875, "opponent")):
        for e in (0.0, 3.0, 5.0):
            p = study(D[a], n, e, thr, lev)
            print("  %-8s noise %-7s n %3d thr %.0f level %.2f true %+.0f: %5.1f / %5.1f / %5.1f" % (tag, a, n, thr, lev, e, p[0], p[1], p[2]))
