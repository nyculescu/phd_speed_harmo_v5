"""V360 reading, in X1 at 5,300. A policy is clearly ahead of a rule if TTC is at least 10 % better, CI excluding 0, with delay at most 2 % worse, or delay at least 5 % better, CI excluding 0, with TTC at most 10 % worse. DRL stays ahead if at least 2 of 3 policies are clearly ahead of every rule; otherwise a rule matches. usage: rulecheck_table.py rows.jsonl out.csv"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    T[r["name"]][r["seed"]] = r
RULES = ("p333", "r4a0", "r4a1", "r4a2", "z0", "z1", "mimic")


def diff(a, b, key, sign):
    A, B = T[a], T[b]
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
    d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261104)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)


def med(n, k):
    return float(np.median([a[k] for a in T[n].values()]))


def show(n):
    return f"flow {med(n, 'passed'):.0f} delay {med(n, 'delay'):.1f} ramp2 {med(n, 'delay_ramp2'):.1f} fuel {med(n, 'fuel_km') / 1000:.1f} ttc {med(n, 'ttc_net'):.0f} b3 {med(n, 'brake_net'):.0f} b45 {med(n, 'b45_net'):.0f} coll {sum(a['collisions'] for a in T[n].values())}"


for c in ("S", "X1", "X2"):
    print("===", c)
    for n in RULES + ("d0", "d1", "d2"):
        print(f" {n}: {show(f'{c}|{n}')}")
rows, ahead = [], {}
for r in RULES:
    k = 0
    for i in range(3):
        a, b = f"X1|d{i}", f"X1|{r}"
        t, d = diff(a, b, "ttc_net", -1), diff(a, b, "delay", -1)
        ok = (t[0] >= 10 and t[1] > 0 and d[0] >= -2) or (d[0] >= 5 and d[1] > 0 and t[0] >= -10)
        k += ok
        rows.append({"rule": r, "policy": f"d{i}", "ahead": ok, "ttc": t[0], "ttc_lo": t[1], "ttc_hi": t[2], "delay": d[0], "delay_lo": d[1], "delay_hi": d[2]})
        print(f" d{i} v {r}: ttc {t} delay {d} {'AHEAD' if ok else ''}")
    ahead[r] = k
print("policies clearly ahead of each rule:", ahead, "DRL stays ahead" if all(v >= 2 for v in ahead.values()) else "a rule matches")
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
