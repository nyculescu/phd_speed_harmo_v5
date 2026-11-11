"""EXPLORATORY zero-run re-check of D19 (finishers-only delay) on P0 rows.
all-vehicle proxy = N - dist/27.78 (1-Hz), validated on plant_c3 rows against all_delay (ratio 0.9997-1.0002).
Statistic: paired seeds, (A-B)/median(B)*100, sign so that + = A better; median; 95 % percentile bootstrap, 10,000 resamples, seed 20261110."""
import gzip, json, sys
from collections import defaultdict
import numpy as np
R = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/"
REF = 100/3.6

def load(f):
    T = defaultdict(dict)
    for l in gzip.open(R + f, "rt"):
        r = json.loads(l)
        r["allp"] = r["N"] - r["dist"]/REF
        T[(r["name"], r["q"])][r["seed"]] = r
    return T

def diff(A, B, key):
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
    d = np.array([-(A[k][key] - B[k][key]) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261110)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (10000, len(d)))], axis=1), [2.5, 97.5])
    return f"{np.median(d):+.1f} [{lo:+.1f},{hi:+.1f}] n={len(ds)}"

def fin(A):
    return f"{np.median([a['finished_pct'] for a in A.values()]):.1f}"

def show(T, a, b, q):
    A, B = T[(a, q)], T[(b, q)]
    print(f"  {a} vs {b} @{q:g}: finishers {diff(A, B, 'delay')} | all-vehicle {diff(A, B, 'allp')} | finished % {fin(A)} vs {fin(B)}")

print("V333 step1 test"); T = load("phase1/step1_test.jsonl.gz")
for q in (4600.0, 5300.0):
    for a in ("p333", "a333", "p303", "alinea16", "alinea24"):
        if (a, q) in T: show(T, a, "p0", q)
print("V337 step2"); T = load("phase1/step2_eval.jsonl.gz")
for q in (4600.0, 5300.0):
    show(T, "p333", "p0", q)
    for a in ("d0", "d1", "d2", "a333"): show(T, a, "p333", q)
print("V339 step3"); T = load("phase1/step3_eval.jsonl.gz")
for q in (4600.0, 5300.0):
    for a in ("d0", "d1", "d2", "p333v90", "p333v80"): show(T, a, "p333", q)
