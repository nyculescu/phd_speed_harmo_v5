"""V363 reading, cells X1 and X2 at 5,300, CIs corrected for 2 cells (97.5 %). A policy is clearly ahead of r4a1 if TTC is at least 10 % better, CI excluding 0, with delay at most 2 % worse, or delay at least 5 % better, CI excluding 0, with TTC at most 10 % worse. The edge is real in a cell if at least 4 of 7 are. usage: shot_table.py rows.jsonl out.csv"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    T[r["name"]][r["seed"]] = r


def diff(a, b, key, sign):
    A, B = T[a], T[b]
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
    d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261104)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [1.25, 98.75])
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)


def med(n, k):
    return float(np.median([a[k] for a in T[n].values()]))


def show(n):
    return f"flow {med(n, 'passed'):.0f} delay {med(n, 'delay'):.1f} ramp2 {med(n, 'delay_ramp2'):.1f} fuel {med(n, 'fuel_km') / 1000:.1f} ttc {med(n, 'ttc_net'):.0f} b3 {med(n, 'brake_net'):.0f} b45 {med(n, 'b45_net'):.0f} coll {sum(a['collisions'] for a in T[n].values())}"


rows = []
for c in ("S", "X1", "X2"):
    print("===", c)
    for n in ("nc", "p333", "r4a1") + tuple(f"d{i}" for i in range(7)):
        print(f" {n}: {show(f'{c}|{n}')}")
    if c == "S":
        continue
    k = 0
    for i in range(7):
        a, b = f"{c}|d{i}", f"{c}|r4a1"
        t, d = diff(a, b, "ttc_net", -1), diff(a, b, "delay", -1)
        ok = (t[0] >= 10 and t[1] > 0 and d[0] >= -2) or (d[0] >= 5 and d[1] > 0 and t[0] >= -10)
        k += ok
        rows.append({"cell": c, "policy": f"d{i}", "ahead": ok, "ttc": t[0], "ttc_lo": t[1], "ttc_hi": t[2], "delay": d[0], "delay_lo": d[1], "delay_hi": d[2], "fuel": diff(a, b, "fuel_km", -1)[0], "brake": diff(a, b, "brake_net", -1)[0], "flow": diff(a, b, "passed", 1)[0]})
        print(f" d{i} v r4a1: ttc {t} delay {d} fuel {rows[-1]['fuel']} brake {rows[-1]['brake']} flow {rows[-1]['flow']}{' AHEAD' if ok else ''}")
    print(f" cell {c}: {k} of 7 clearly ahead:", "EDGE REAL" if k >= 4 else "not confirmed")
    print(" r4a1 v p333:", {x: diff(f"{c}|r4a1", f"{c}|p333", kk, s) for x, kk, s in (("ttc", "ttc_net", -1), ("delay", "delay", -1))})
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
