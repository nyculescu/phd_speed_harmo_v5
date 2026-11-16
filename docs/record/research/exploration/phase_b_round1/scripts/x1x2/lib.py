import json, numpy as np
from collections import defaultdict
RUNS = "/home/catalin/work/phd/v5b1_runs/"
FILES = {"r2test": RUNS + "round2/test/rows_6c49e7e.jsonl",
         "r2test_remote": RUNS + "round2_evalremote/test/rows_6c49e7e.jsonl",
         "s01test": RUNS + "measure_s01_remote/rows_test.jsonl",
         "s01s1": RUNS + "measure_s01_remote/rows_s1.jsonl",
         "s01band": RUNS + "measure_s01_remote/rows_band.jsonl"}
def load(f):
    T = defaultdict(dict)
    with open(f) as h:
        for line in h:
            r = json.loads(line)
            T[(r["name"], r["q"])][r["seed"]] = r
    return T
def val(row, key):
    v = row.get(key)
    return 0.0 if v is None else float(v)
def eff(A, B, key="all_delay", sign=-1, pct=(2.5, 97.5), nb=10000, f=val):
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([f(B[k], key) for k in ds])), 1e-9)
    d = np.array([sign * (f(A[k], key) - f(B[k], key)) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261110)
    b = np.median(d[rng.integers(0, len(d), (nb, len(d)))], axis=1)
    lo, hi = np.percentile(b, pct)
    return float(np.median(d)), float(lo), float(hi), len(ds), float(np.std(d, ddof=1)), float(np.mean(d))
def arm_mean(T, names, q):
    rows = [T[(n, q)] for n in names]
    seeds = sorted(set.intersection(*(set(r) for r in rows)))
    keys = {k for r in rows for s in seeds for k, v in r[s].items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    return {s: {"seed": s, **{k: sum(val(r[s], k) for r in rows) / len(rows) for k in keys}} for s in seeds}
