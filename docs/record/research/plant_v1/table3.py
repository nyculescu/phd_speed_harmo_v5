"""V327: the smooth-rule sweep against r1m3 as adopted; medians, paired CIs, hard limits, V271 drop. usage: table3.py stage_d3.jsonl out.csv"""
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
NAMES = sorted({k[0] for k in T}, key=lambda n: (n != "base", n))
M = (("flow", "passed", 1), ("ttt", "N", -1), ("delay", "delay", -1), ("p95", "delay_p95", -1), ("ramp", "delay_ramp", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake3", "brake_net", -1), ("brake45", "b45_net", -1), ("brake7", "b7_net", -1), ("free", "free_brake_alks", -1), ("jerk", "jerk_vs", -1), ("stop", "end_stop", -1), ("undertakes", "undertakes", -1))


def drop(r):
    v, f = r["v20_min"], r["flow_min"]
    on = next((i for i, x in enumerate(v) if x < 15 and i >= 10), None)
    if on is None or on + 5 >= len(f) - 3:
        return None
    return float((np.mean(f[on - 10:on]) - np.mean(f[on + 5:])) / np.mean(f[on - 10:on]) * 100)


out = []
for q in sorted({k[1] for k in T}):
    B = T[("base", q)]
    for n in NAMES:
        A = T[(n, q)]
        ds = sorted(set(A) & set(B))
        s = {"name": n, "q": q, "n": len(ds), "collisions": sum(A[k]["collisions"] for k in ds), "teleports": sum(A[k]["teleports"] for k in ds)}
        dr = [x for x in (drop(A[k]) for k in ds) if x is not None]
        s["drop_pct"], s["drop_n"] = (round(float(np.median(dr)), 1), len(dr)) if dr else (None, 0)
        for x in ("3a_1", "3a_3"):
            s["v" + x] = round(float(np.median([A[k]["nv_" + x] / max(A[k]["n_" + x], 1) for k in ds])), 1)
        for x in ("3_0", "3_1", "3_2"):
            s["flow" + x] = round(float(np.median([A[k]["nv_" + x] / 1500 / 1196 * 3600 for k in ds])))
        for lab, key, sign in M:
            s[lab + "_abs"] = round(float(np.median([A[k][key] for k in ds])), 3)
            ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
            d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
            rng = np.random.default_rng(20261103)
            lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
            s[lab], s[lab + "_lo"], s[lab + "_hi"] = round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)
        out.append(s)
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(out[0]))
    w.writeheader()
    w.writerows(out)
for q in sorted({r["q"] for r in out}):
    print(f"--- {q:g}: name | flow veh delay p95 ramp fuel ttc b3 b45 b7 free jerk stop under | coll drop(n) v3a1 lanes3")
    for s in (r for r in out if r["q"] == q):
        print(s["name"], "|", int(s["flow_abs"]), round(s["ttt_abs"] / 1500), round(s["delay_abs"], 1), round(s["p95_abs"]), round(s["ramp_abs"], 1), round(s["fuel_abs"] / 1000, 1), int(s["ttc_abs"]), int(s["brake3_abs"]), int(s["brake45_abs"]), int(s["brake7_abs"]), int(s["free_abs"]), s["jerk_abs"], int(s["stop_abs"]), int(s["undertakes_abs"]), "|", s["collisions"], s["drop_pct"], s["drop_n"], s["v3a_1"], s["flow3_0"], s["flow3_1"], s["flow3_2"])
