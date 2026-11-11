"""EXPLORATORY zero-run re-check of D19 on r2m3 and phase 3 rows (P0). 95 % intervals, not Bonferroni."""
import gzip, json
from collections import defaultdict
import numpy as np
R = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/"
REF = 100/3.6
def load(f):
    T = defaultdict(dict)
    for l in gzip.open(R + f, "rt"):
        r = json.loads(l); r["allp"] = r["N"] - r["dist"]/REF
        T[(r["name"], r["q"])][r["seed"]] = r
    return T
def diff(A, B, key):
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
    d = np.array([-(A[k][key] - B[k][key]) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261110)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (10000, len(d)))], axis=1), [2.5, 97.5])
    return np.median(d), lo, hi, len(ds)
def s(x): return f"{x[0]:+.1f} [{x[1]:+.1f},{x[2]:+.1f}]"
def show(T, a, b, q):
    A, B = T[(a, q)], T[(b, q)]
    x, y = diff(A, B, "delay"), diff(A, B, "allp")
    print(f"  {a} vs {b} @{q:g} n={x[3]}: finishers {s(x)} | all-vehicle {s(y)}")
    return x, y
print("V355 r2m3 test"); T = load("r2m3/test_rows.jsonl.gz")
for q in (4600.0, 5300.0):
    for a in ("p13333", "p31333", "p22222", "p31313", "p33313"):
        if (a, q) in T: show(T, a, "p33333", q)
    show(T, "p33333", "nc", q)
print("V359 confirmatory 2: policies vs p333, 20 cells"); T = load("phase3/eval_rows.jsonl.gz")
cnt = {"fin_pos": 0, "all_pos": 0, "fin_neg": 0, "all_neg": 0, "n": 0}
for g in ("r1m3", "r2m3"):
    for c in ("S", "X1", "X2", "H1", "H2"):
        for q in (4600.0, 5300.0):
            for d in ("d0", "d1", "d2"):
                x, y = show(T, f"{g}|{c}|{d}", f"{g}|{c}|p333", q)
                cnt["n"] += 1; cnt["fin_pos"] += x[1] > 0; cnt["all_pos"] += y[1] > 0; cnt["fin_neg"] += x[2] < 0; cnt["all_neg"] += y[2] < 0
print("  count of policy-cell pairs with 95 % CI above 0 / below 0:", cnt)
for g in ("r1m3", "r2m3"):
    for c in ("S", "X1", "X2"):
        for q in (4600.0, 5300.0):
            show(T, f"{g}|{c}|lr", f"{g}|{c}|p333", q); show(T, f"{g}|{c}|p333", f"{g}|{c}|nc", q)
print("V361 rule check"); T = load("phase3/rulecheck_rows.jsonl.gz")
for c in ("S", "X1", "X2"):
    for a in ("d0", "d1", "d2", "r4a1", "mimic"): show(T, f"{c}|{a}", f"{c}|p333", 5300.0)
print("V368 shot"); T = load("phase3/shot_rows.jsonl.gz")
for c in ("S", "X1", "X2"):
    for a in ("d0", "d1", "d2", "d3", "d4", "d5", "d6", "r4a1"): show(T, f"{c}|{a}", f"{c}|p333", 5300.0)
    show(T, f"{c}|p333", f"{c}|nc", 5300.0)
