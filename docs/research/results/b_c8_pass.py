"""V302 pass rule. usage: b_c8_pass.py eval_rows.jsonl select.json (higher is better everywhere)."""
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    T[(r["name"], r["q"])][r["seed"]] = r
sel = json.load(open(sys.argv[2]))


def diff(a, b, q, m, s):
    A, B = T[(a, q)], T[(b, q)]
    ds = sorted(set(A) & set(B))
    base = np.median([B[k][m] for k in ds])
    d = np.array([s * (A[k][m] - B[k][m]) / base * 100 for k in ds])
    rng = np.random.default_rng(20261103)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return float(np.median(d)), float(lo), float(hi)


def f(x):
    return f"{x[0]:+.1f}[{x[1]:+.1f},{x[2]:+.1f}]"


for q in (4600.0, 5300.0):
    best = sel[str(int(q))]["best"]
    print(f"level {q:g}: opponent {best}, selected on other seeds; n per policy {len(T[(best, q)])}")
    for s in "FGHB":
        n = 0
        for i in range(3):
            p = f"{s}{i}"
            fl, tt, br = diff(p, best, q, "passed", 1), diff(p, best, q, "E30", -1), diff(p, best, q, "brake3", -1)
            coll = sum(r["collisions"] for r in T[(p, q)].values())
            ok = fl[1] >= -0.5 and tt[1] > 0 and br[1] > 0 and not coll
            n += ok
            print(f" {p}: flow {f(fl)} TTC {f(tt)} brake {f(br)} coll {coll} v_delay {f(diff(p, 'a000', q, 'passed', 1))} speed_v_delay {diff(p, 'a000', q, 'mean_v', 1)[0]:+.1f} v_a333 flow {diff(p, 'a333', q, 'passed', 1)[0]:+.1f} TTC {diff(p, 'a333', q, 'E30', -1)[0]:+.0f}", "PASS" if ok else "")
        print(f" setting {s}: {n} of 3", "PASS" if n >= 2 else "no pass")
    for o in sorted({k[0] for k in T if k[1] == q and k[0][0] in "par"}):
        print(f"  {o}: flow v delay {f(diff(o, 'a000', q, 'passed', 1))} TTC {diff(o, 'a000', q, 'E30', -1)[0]:+.0f} brake {diff(o, 'a000', q, 'brake3', -1)[0]:+.0f} speed {diff(o, 'a000', q, 'mean_v', 1)[0]:+.1f} coll {sum(r['collisions'] for r in T[(o, q)].values())} | v {best}: flow {diff(o, best, q, 'passed', 1)[0]:+.1f} TTC {diff(o, best, q, 'E30', -1)[0]:+.0f}")
