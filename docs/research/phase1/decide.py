"""V334 rules. usage: decide.py rows.jsonl screen|final. Higher is better everywhere; 2 of 3 policies at one level must meet the rule."""
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    T[(r["name"], r["q"])][r["seed"]] = r
M = (("flow", "passed", 1), ("delay", "delay", -1), ("p95", "delay_p95", -1), ("ramp", "delay_ramp", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake", "brake_net", -1), ("hard", "b45_net", -1))


def diff(A, B, key, sign):
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
    d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261103)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return float(np.median(d)), float(lo), float(hi)


def med(A, k):
    return float(np.median([a[k] for a in A.values()]))


for q in sorted({k[1] for k in T}):
    rule = min(("p333", "a333"), key=lambda n: med(T[(n, q)], "delay"))
    print(f"--- {q:g}: no control delay {med(T[('p0', q)], 'delay'):.1f}, p333 {med(T[('p333', q)], 'delay'):.1f}, a333 {med(T[('a333', q)], 'delay'):.1f}; opponent {rule if sys.argv[2] == 'final' else 'p333'}")
    opp = T[(rule if sys.argv[2] == "final" else "p333", q)]
    n = 0
    for name in ("d0", "d1", "d2"):
        A = T[(name, q)]
        x = {lab: diff(A, opp, key, s) for lab, key, s in M}
        coll = sum(a["collisions"] for a in A.values())
        if sys.argv[2] == "screen":
            ok = x["delay"][0] >= 5 and x["flow"][0] >= -0.5 and x["ttc"][0] >= -10 and x["brake"][0] >= -10 and not coll
        else:
            ok = x["delay"][0] >= 5 and x["delay"][1] > 0 and x["flow"][2] >= 0 and x["ttc"][2] >= 0 and x["brake"][2] >= 0 and not coll
        n += ok
        print(f" {name}: coll {coll} delay_s {med(A, 'delay'):.1f} flow {med(A, 'passed'):.0f} fuel {med(A, 'fuel_km') / 1000:.1f} changes {med(A, 'changes') if 'changes' in next(iter(A.values())) else 0} | " + " ".join(f"{k} {v[0]:+.1f}[{v[1]:+.1f},{v[2]:+.1f}]" for k, v in x.items()), "MEETS" if ok else "")
    print(f" level {q:g}: {n} of 3", "MET" if n >= 2 else "not met")
