"""V374 reading of the P0d check, criteria as V370 with 20 seeds. usage: check2_table.py out_dir table.csv"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

T = defaultdict(dict)
for f in ("check.jsonl", "check_p0c.jsonl", "check_r2.jsonl"):
    for line in open(Path(sys.argv[1]) / f):
        r = json.loads(line)
        r["fuel_km_step"] = r["fuel_step"] / max(r["dist_step"], 1.0) * 1000.0
        for k in ("alks_full_events", "pass_straight", "pass_side_by_side", "pass_merging", "pass_lane_change", "b45_step", "b7_step", "free_brake_alks_step"):
            r.setdefault(k, 0.0)     # counted only when they occur
        T[(r["name"], r["q"])][r["seed"]] = r
HIGH = {"passed"}
L = (4090.0, 4600.0, 5300.0, 6000.0)
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
for q in L:
    print("==", q)
    for key in M:
        d = diff("p0d", "base", q, key)
        c = round(med("p0c", q, key), 1) if ("p0c", q) in T else ""
        rows.append({"q": q, "metric": key, "base": round(med("base", q, key), 1), "p0c": c, "p0d": round(med("p0d", q, key), 1), "pct": d[0], "lo": d[1], "hi": d[2]})
        print(f" {key}: base {rows[-1]['base']} p0c {c} p0d {rows[-1]['p0d']} | p0d vs base {d}")
    print(" 1-Hz/step braking ratio: base", blind("base", q), "p0d", blind("p0d", q))
    ok[f"C2 ramp {q:.0f}"] = med("p0d", q, "delay_ramp") <= med("base", q, "delay_ramp")
    ok[f"C4 full events {q:.0f}"] = med("p0d", q, "alks_full_events") <= med("base", q, "alks_full_events") + 5
    ok[f"C5 blind spot {q:.0f}"] = abs(blind("p0d", q) - 1.0) <= 0.05
Q = 5300.0
ok["C1 collisions, teleports"] = sum(x["collisions"] + x["teleports"] for q in L for x in T[("p0d", q)].values()) == 0
for key in ("passed", "delay", "fuel_km_step", "ttc_net", "b3_step"):
    ok[f"C3 {key} 5300"] = diff("p0d", "base", Q, key)[1] > 0
d = diff("p0d", "base", Q, "free_brake_alks_step")
ok["C6 free-road 5300"] = d[0] >= 50 and d[1] > 0
ok["C7 undertakes 5300"] = diff("p0d", "base", Q, "pass_straight")[2] >= 0
for k, v in ok.items():
    print(k, "PASS" if v else "FAIL")
print("collisions by level, base", {q: sum(x["collisions"] for x in T[("base", q)].values()) for q in L}, "p0d", {q: sum(x["collisions"] for x in T[("p0d", q)].values()) for q in L})
print("P0d vs P0c, % better, report only")
for q in (4600.0, 5300.0):
    print(q, {k: diff("p0d", "p0c", q, k) for k in ("passed", "delay", "ttc_net", "b3_step", "pass_straight", "alks_full_events")})
print("== r2m3 P0d, report only")
for q in (4600.0, 5300.0):
    print(q, {k: round(med("r2_p0d", q, k), 1) for k in ("passed", "delay", "delay_ramp", "delay_ramp2", "ttc_net", "b3_step", "b7_step", "alks_full_events", "free_brake_alks_step", "pass_straight", "end_stop", "end_stop2")}, "ratio", blind("r2_p0d", q), "collisions", sum(x["collisions"] for x in T[("r2_p0d", q)].values()))
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
