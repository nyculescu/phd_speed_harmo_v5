"""V331: r1m2 with the P0 settings against plain r1m2, with the V330 rule. usage: table.py check.jsonl out.csv"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    T[(r["name"], r["q"])][r["seed"]] = r
M = (("flow", "passed", 1), ("vehicles", "N", -1), ("delay", "delay", -1), ("ramp", "delay_ramp", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake3", "brake_net", -1), ("brake45", "b45_net", -1), ("free", "free_brake_alks", -1), ("stop", "end_stop", -1), ("undertakes", "undertakes", -1))
RULE = ("flow", "delay", "ramp", "fuel", "ttc", "brake3", "free")
out, ok = [], True
for q in sorted({k[1] for k in T}):
    A, B = T[("r1m2_p0", q)], T[("r1m2_plain", q)]
    ds = sorted(set(A) & set(B))
    s = {"q": q, "n": len(ds), "demand_window": round(q * 1500 / 3600), "collisions_p0": sum(A[k]["collisions"] for k in ds), "collisions_plain": sum(B[k]["collisions"] for k in ds), "teleports_p0": sum(A[k]["teleports"] for k in ds)}
    for lab, key, sign in M:
        s[lab + "_plain"], s[lab + "_p0"] = round(float(np.median([B[k][key] for k in ds])), 1), round(float(np.median([A[k][key] for k in ds])), 1)
        ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
        d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
        rng = np.random.default_rng(20261103)
        lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
        s[lab], s[lab + "_lo"], s[lab + "_hi"] = round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)
    bad = [m for m in RULE if s[m] < -1.0]
    if s["collisions_p0"] or s["teleports_p0"] or bad:
        ok = False
    s["fails"] = " ".join(bad)
    out.append(s)
    print(f"{q:g} (window {s['demand_window']}) coll {s['collisions_p0']} vs {s['collisions_plain']} fails [{s['fails']}] | " + " | ".join(f"{m} {s[m + '_plain']:g}>{s[m + '_p0']:g} {s[m]:+.1f}[{s[m + '_lo']:+.1f},{s[m + '_hi']:+.1f}]" for m, _, _ in M))
print("transfers" if ok else "does not transfer as written")
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(out[0]))
    w.writeheader()
    w.writerows(out)
