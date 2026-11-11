"""EXPLORATORY zero-run re-check of D19 on phase 2 and 3 rows (P0). Same statistic as d19.py."""
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
print("V344 oracle"); T = load("phase2/oracle_rows.jsonl.gz")
for q in (4090.0, 4600.0):
    for X in ("slow25", "slow40"):
        show(T, f"p333_{X}_o500_80", f"p333_{X}", q)
        show(T, f"nc_{X}_o500_80", f"nc_{X}", q)
print("V347 headway oracle"); T = load("phase2/hw_rows.jsonl.gz")
for q in (4090.0, 4600.0):
    for a in ("hw25_d500_l1", "hw25_d1000_l1", "hw25_d500_l0"): show(T, a, "p333_slow25", q)
    show(T, "p333_slow25", "nc_slow25", q)
print("V349 step A"); T = load("phase2/stepa_rows.jsonl.gz")
for q in (4090.0, 4600.0):
    for a in ("p222_slow25", "p111_slow25", "lr1000_10_slow25"):
        if (a, q) in T: show(T, a, "p333_slow25", q)
    for a in ("p222", "p111"): show(T, a, "p333", q)
print("V351 confirm"); T = load("phase2/confirm_rows.jsonl.gz")
for q in (4090.0, 4600.0):
    show(T, "lr_slow25", "p333_slow25", q); show(T, "oracle_slow25", "p333_slow25", q); show(T, "lr", "p333", q); show(T, "lr", "p333h10", q)
print("V355 r2m3 test"); T = load("r2m3/test_rows.jsonl.gz")
names = sorted({k[0] for k in T}); print("  names", names)
