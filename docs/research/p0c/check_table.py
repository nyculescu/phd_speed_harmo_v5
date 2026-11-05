"""V370 reading of the P0c check. usage: check_table.py check.jsonl check_r2.jsonl table.csv"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for f in sys.argv[1:3]:
    for line in open(f):
        r = json.loads(line)
        r["fuel_km_step"] = r["fuel_step"] / max(r["dist_step"], 1.0) * 1000.0
        for k in ("alks_full_events", "pass_straight", "pass_side_by_side", "pass_merging", "pass_lane_change", "b45_step", "b7_step", "free_brake_alks_step"):
            r.setdefault(k, 0.0)     # counted only when they occur
        T[(r["name"], r["q"])][r["seed"]] = r
HIGH = {"passed"}
M = ("passed", "delay", "delay_ramp", "fuel_km_step", "ttc_net", "b3_step", "b45_step", "b7_step", "alks_full_events", "free_brake_alks_step", "pass_straight", "pass_side_by_side", "pass_merging", "pass_lane_change", "undertakes", "end_stop", "jerk_step")


def med(n, q, k):
    return float(np.median([x[k] for x in T[(n, q)].values()]))


def diff(a, b, q, key):
    A, B = T[(a, q)], T[(b, q)]
    ds = sorted(set(A) & set(B))
    sign = 1 if key in HIGH else -1
    ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
    d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
    lo, hi = np.percentile(np.median(d[np.random.default_rng(20261104).integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)


def blind(n, q):
    return round(float(np.median([x["brake_net"] / max(x["b3_step"], 1.0) for x in T[(n, q)].values()])), 3)


rows, ok = [], {}
for q in (4090.0, 4600.0, 5300.0, 6000.0):
    print("==", q)
    for key in M:
        d = diff("p0c", "base", q, key)
        rows.append({"q": q, "metric": key, "base": round(med("base", q, key), 1), "p0": round(med("p0", q, key), 1), "p0c": round(med("p0c", q, key), 1), "pct": d[0], "lo": d[1], "hi": d[2]})
        print(f" {key}: base {rows[-1]['base']} p0 {rows[-1]['p0']} p0c {rows[-1]['p0c']} | p0c vs base {d}")
    print(" 1-Hz/step braking ratio: base", blind("base", q), "p0", blind("p0", q), "p0c", blind("p0c", q))
    ok[f"C2 ramp {q:.0f}"] = med("p0c", q, "delay_ramp") <= med("base", q, "delay_ramp")
    ok[f"C4 full events {q:.0f}"] = med("p0c", q, "alks_full_events") <= med("base", q, "alks_full_events") + 5
    ok[f"C5 blind spot {q:.0f}"] = abs(blind("p0c", q) - 1.0) <= 0.05
Q = 5300.0
ok["C1 collisions, teleports"] = sum(x["collisions"] + x["teleports"] for q in (4090.0, 4600.0, 5300.0, 6000.0) for x in T[("p0c", q)].values()) == 0
for key in ("passed", "delay", "fuel_km_step", "ttc_net", "b3_step"):
    ok[f"C3 {key} 5300"] = diff("p0c", "base", Q, key)[1] > 0
d = diff("p0c", "base", Q, "free_brake_alks_step")
ok["C6 free-road 5300"] = d[0] >= 50 and d[1] > 0
ok["C7 undertakes 5300"] = diff("p0c", "base", Q, "pass_straight")[2] >= 0
for k, v in ok.items():
    print(k, "PASS" if v else "FAIL")
print("collisions p0c by level", {q: sum(x["collisions"] for x in T[("p0c", q)].values()) for q in (4090.0, 4600.0, 5300.0, 6000.0)})
print("== r2m3, report only")
for q in (4600.0, 5300.0):
    for key in ("passed", "delay", "delay_ramp", "delay_ramp2", "ttc_net", "b3_step", "b7_step", "alks_full_events", "free_brake_alks_step", "pass_straight", "end_stop", "end_stop2"):
        print(f" {q:.0f} {key}: p0 {med('r2_p0', q, key):.1f} p0c {med('r2_p0c', q, key):.1f}")
    print(" ratio p0", blind("r2_p0", q), "p0c", blind("r2_p0c", q), "collisions p0c", sum(x["collisions"] for x in T[("r2_p0c", q)].values()), "p0", sum(x["collisions"] for x in T[("r2_p0", q)].values()))
with open(sys.argv[3], "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
