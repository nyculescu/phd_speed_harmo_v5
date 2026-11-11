"""EXPLORATORY: conf-2 policies d0-d2 (hand-scaled, P0, r2m3, 5,300) against p333 on delay, pooled over the two P0 seed sets
(7,440,100-119 confirmatory 2; 7,440,120-139 rule check). Also the 7 shot policies on 7,440,140-159. 95 % percentile bootstrap, 10,000, seed 20261110."""
import gzip, json
from collections import defaultdict
import numpy as np
R = "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/phase3/"
REF = 100/3.6
T = defaultdict(dict)
for f, pre in (("eval_rows.jsonl.gz", "r2m3|"), ("rulecheck_rows.jsonl.gz", "")):
    for l in gzip.open(R + f, "rt"):
        r = json.loads(l)
        if r["q"] != 5300.0 or not r["name"].startswith(pre): continue
        n = r["name"][len(pre):]
        r["allp"] = r["N"] - r["dist"]/REF
        assert r["seed"] not in T[n]
        T[n][r["seed"]] = r
def diff(A, B, key):
    ds = sorted(set(A) & set(B))
    ref = float(np.median([B[k][key] for k in ds]))
    d = np.array([-(A[k][key] - B[k][key]) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261110)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (10000, len(d)))], axis=1), [2.5, 97.5])
    return f"{np.median(d):+.1f} [{lo:+.1f},{hi:+.1f}] n={len(ds)}"
for c in ("S", "X1", "X2"):
    for d in ("d0", "d1", "d2"):
        A, B = T[f"{c}|{d}"], T[f"{c}|p333"]
        print(f"{c} {d} vs p333: finishers {diff(A, B, 'delay')} | all-vehicle {diff(A, B, 'allp')}")
    if f"{c}|r4a1" in T:
        A, B = T[f"{c}|r4a1"], T[f"{c}|p333"]
        print(f"{c} r4a1 vs p333 (rule-check seeds only): finishers {diff(A, B, 'delay')} | all-vehicle {diff(A, B, 'allp')}")
