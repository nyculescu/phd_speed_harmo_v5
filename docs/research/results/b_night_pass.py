"""V283 bar. usage: b_night_pass.py rows.jsonl RULE L0,L1,L2 (levels 4,600 and 5,300; higher is better everywhere)."""
import json
import sys
from collections import defaultdict

import numpy as np

ARMS = ("a111", "a222", "a333", "a101", "a202", "a303", "a300", "a030", "a003", "p101", "p202", "p303")     # p: per-vehicle patterns, V286
T = defaultdict(dict)
for f in sys.argv[1].split(","):
    for line in open(f):
        r = json.loads(line)
        T[(r["name"], r["q"])][r["seed"]] = r


def diff(a, b, q, m, s):
    A, B = T[(a, q)], T[(b, q)]
    ds = sorted(set(A) & set(B))
    base = np.median([B[k][m] for k in ds])
    d = np.array([s * (A[k][m] - B[k][m]) / base * 100 for k in ds])
    rng = np.random.default_rng(20261102)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return float(np.median(d)), float(lo), float(hi)


rule, pols = sys.argv[2], sys.argv[3].split(",")
for q in (4600.0, 5300.0):
    passed = 0
    for p in pols:
        fl = diff(p, "a000", q, "passed", 1)
        coll = sum(r["collisions"] for r in T[(p, q)].values())
        gaps = sum(r["gap25"] for r in T[(p, q)].values())
        fails = []
        if fl[1] <= 0:
            fails.append(f"flow v delay {fl[0]:+.1f}[{fl[1]:+.1f},{fl[2]:+.1f}]")
        if coll:
            fails.append(f"collisions {coll}")
        if gaps > 100:
            fails.append(f"moving gaps {gaps}")
        for c in (rule,) + ARMS:
            f = diff(p, c, q, "passed", 1)
            if f[0] > 0.5:
                continue     # the comparator's flow is lower by more than 0.5 %: no safety requirement against it
            t, b = diff(p, c, q, "E30", -1), diff(p, c, q, "brake3", -1)
            if t[1] <= 0 or b[1] <= 0:
                fails.append(f"{c}: flow {f[0]:+.1f} TTC {t[0]:+.0f}[{t[1]:+.0f},{t[2]:+.0f}] brake {b[0]:+.0f}[{b[1]:+.0f},{b[2]:+.0f}]")
        print(f"{p} {q:g}: flow v delay {fl[0]:+.1f}[{fl[1]:+.1f},{fl[2]:+.1f}] coll {coll} gaps {gaps}", "PASS" if not fails else "FAIL " + "; ".join(fails))
        passed += not fails
    print(f"level {q:g}: {passed} of {len(pols)} policies pass; bar met" if passed >= 2 else f"level {q:g}: {passed} of {len(pols)} policies pass; bar not met")
