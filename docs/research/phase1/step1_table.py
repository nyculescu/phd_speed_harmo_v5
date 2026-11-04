"""V333: step 1 test rows against no control on P0, with the V323 reading. usage: step1_table.py test.jsonl out.csv"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    r["jerk_vs"] = r["jerk"] / max(r["vs"], 1)
    T[(r["name"], r["q"])][r["seed"]] = r
M = (("flow", "passed", 1), ("vehicles", "N", -1), ("delay", "delay", -1), ("p95", "delay_p95", -1), ("ramp", "delay_ramp", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake3", "brake_net", -1), ("brake45", "b45_net", -1), ("jerk", "jerk_vs", -1))
out = []
for q in sorted({k[1] for k in T}):
    B = T[("p0", q)]
    print(f"--- {q:g}")
    for n in sorted({k[0] for k in T if k[1] == q}):
        A = T[(n, q)]
        ds = sorted(set(A) & set(B))
        s = {"name": n, "q": q, "n": len(ds), "collisions": sum(A[k]["collisions"] for k in ds)}
        for lab, key, sign in M:
            s[lab + "_abs"] = round(float(np.median([A[k][key] for k in ds])), 2)
            ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
            d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
            rng = np.random.default_rng(20261103)
            lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
            s[lab], s[lab + "_lo"], s[lab + "_hi"] = round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)
        s["clear"] = bool(s["delay"] >= 5 and s["delay_lo"] > 0 and s["flow_hi"] >= 0 and s["ttc_hi"] >= 0 and s["brake3_hi"] >= 0)
        out.append(s)
        print(n, f"coll {s['collisions']} clear {s['clear']} |", " ".join(f"{m} {s[m + '_abs']:g} {s[m]:+.1f}[{s[m + '_lo']:+.1f},{s[m + '_hi']:+.1f}]" for m, _, _ in M))
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(out[0]))
    w.writeheader()
    w.writerows(out)
