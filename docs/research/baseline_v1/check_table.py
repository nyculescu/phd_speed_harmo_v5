"""V329: P0 against the earlier plant on the check seeds, with the V328 pass rule. usage: check_table.py check.jsonl out.csv"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    T[(r["name"], r["q"])][r["seed"]] = r
M = (("flow", "passed", 1), ("vehicles", "N", -1), ("delay", "delay", -1), ("p95", "delay_p95", -1), ("ramp", "delay_ramp", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake3", "brake_net", -1), ("brake45", "b45_net", -1), ("brake7", "b7_net", -1), ("free", "free_brake_alks", -1), ("stop", "end_stop", -1), ("undertakes", "undertakes", -1))
out = []
for q in sorted({k[1] for k in T}):
    A, B = T[("p0", q)], T[("base", q)]
    ds = sorted(set(A) & set(B))
    s = {"q": q, "n": len(ds), "collisions_p0": sum(A[k]["collisions"] for k in ds), "collisions_old": sum(B[k]["collisions"] for k in ds), "teleports_p0": sum(A[k]["teleports"] for k in ds)}
    for lab, key, sign in M:
        s[lab + "_old"], s[lab + "_p0"] = round(float(np.median([B[k][key] for k in ds])), 2), round(float(np.median([A[k][key] for k in ds])), 2)
        ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
        d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
        rng = np.random.default_rng(20261103)
        lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
        s[lab], s[lab + "_lo"], s[lab + "_hi"] = round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)
    out.append(s)
    print(f"{q:g} coll {s['collisions_p0']} vs {s['collisions_old']} tele {s['teleports_p0']} | " + " | ".join(f"{m} {s[m + '_old']:g}>{s[m + '_p0']:g} {s[m]:+.1f}[{s[m + '_lo']:+.1f},{s[m + '_hi']:+.1f}]" for m, _, _ in M))
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(out[0]))
    w.writeheader()
    w.writerows(out)
s = [x for x in out if x["q"] == 5300.0][0]
ok = all(x["collisions_p0"] == 0 and x["teleports_p0"] == 0 and x["ramp"] >= 0 and x["undertakes"] >= -5 for x in out) and all(s[m + "_lo"] > 0 for m in ("flow", "delay", "fuel", "ttc", "brake3"))
print("all levels: ramp", [x["ramp"] for x in out], "undertakes", [x["undertakes"] for x in out], "pass" if ok else "FAIL")
