"""V324: the follow-up table against r1m3 as adopted; absolute medians, paired CIs, the V271 capacity-drop estimate. usage: table.py stage_d.jsonl stage_d2.jsonl out.csv"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for f in sys.argv[1:3]:
    for line in open(f):
        r = json.loads(line)
        T[(r["name"], r["q"])][r["seed"]] = r
NAMES = ("base", "as1.2", "as1.3", "as1.4", "as1.5", "as1.6", "as1.75", "as1.5_s0.5", "all96", "s0.5_lane600", "all")
M = (("flow", "passed", 1), ("ttt", "N", -1), ("delay", "delay", -1), ("p95", "delay_p95", -1), ("ramp", "delay_ramp", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake3", "brake_net", -1), ("brake45", "b45_net", -1), ("brake7", "b7_net", -1), ("jerk", "jerk_vs", -1), ("stop", "end_stop", -1))


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
        A = T.get((n, q))
        if not A:
            continue
        for a in list(A.values()) + list(B.values()):
            a["jerk_vs"] = a["jerk"] / max(a["vs"], 1)
        ds = sorted(set(A) & set(B))
        s = {"name": n, "q": q, "n": len(ds), "collisions": sum(A[k]["collisions"] for k in ds), "teleports": sum(A[k]["teleports"] for k in ds), "finished": round(float(np.median([A[k]["finished_pct"] for k in ds])), 1)}
        dr = [x for x in (drop(A[k]) for k in ds) if x is not None]
        s["drop_pct"], s["drop_n"] = (round(float(np.median(dr)), 1), len(dr)) if dr else (None, 0)
        s["v3a1"] = round(float(np.median([A[k]["nv_3a_1"] / max(A[k]["n_3a_1"], 1) for k in ds])), 1)
        s["v3a3"] = round(float(np.median([A[k]["nv_3a_3"] / max(A[k]["n_3a_3"], 1) for k in ds])), 1)
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
with open(sys.argv[3], "w", newline="") as f:
    w = csv.DictWriter(f, list(out[0]))
    w.writeheader()
    w.writerows(out)
for q in sorted({r["q"] for r in out}):
    print(f"--- {q:g}: name | flow ttt delay p95 ramp fuel ttc brake3 brake45 brake7 jerk stop | coll drop(n) v3a1 v3a3 lanes3 fin")
    for s in (r for r in out if r["q"] == q):
        print(s["name"], "|", s["flow_abs"], round(s["ttt_abs"] / 1500), s["delay_abs"], s["p95_abs"], s["ramp_abs"], round(s["fuel_abs"] / 1000, 1), s["ttc_abs"], s["brake3_abs"], s["brake45_abs"], s["brake7_abs"], s["jerk_abs"], s["stop_abs"], "| pct", s["flow"], s["ttt"], s["delay"], s["ramp"], s["fuel"], s["ttc"], s["brake3"], s["brake45"], "| coll", s["collisions"], "drop", s["drop_pct"], s["drop_n"], s["v3a1"], s["v3a3"], s["flow3_0"], s["flow3_1"], s["flow3_2"], s["finished"])
