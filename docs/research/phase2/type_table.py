"""V352 reading. A variant passes the V346 rule against p333 in the same condition. Hidden type has value if a hidden-type variant
(tau, sigma, either, sf) passes and, against each of p222 and the visible-only variants (any, truck): delay at least 2 % better with
TTC at most 10 % worse, or TTC at least 20 % better with delay at most 2 % worse. usage: type_table.py rows.jsonl out.csv"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    T[(r["name"], r["q"])][r["seed"]] = r
M = (("flow", "passed", 1), ("delay", "delay", -1), ("ramp", "delay_ramp", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake", "brake_net", -1), ("hard", "b45_net", -1))
HIDDEN, VISIBLE = ("t_tau", "t_sigma", "t_either", "t_sf"), ("p222", "t_any", "t_truck")


def diff(a, b, q, key, sign):
    A, B = T[(a, q)], T[(b, q)]
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
    d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261103)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)


def med(n, q, k):
    return float(np.median([a[k] for a in T[(n, q)].values()]))


def beats(a, b, q):
    d, t = diff(a, b, q, "delay", -1)[0], diff(a, b, q, "ttc_net", -1)[0]
    return (d >= 2 and t >= -10) or (t >= 20 and d >= -2)


rows = []
for q in sorted({k[1] for k in T}):
    for sfx in ("", "_slow25"):
        print(f"=== {q:g} {sfx or 'no X'}")
        p, nc = "p333" + sfx, "nc" + sfx
        for base in ("nc", "p333", "p222", "lr", "t_any", "t_truck", "t_tau", "t_sigma", "t_either", "t_sf"):
            n = base + sfx
            x = {l: diff(n, p, q, k, s) for l, k, s in M}
            vs = diff(n, nc, q, "delay", -1)
            drop = med(p, q, "ttc_net") - med(n, q, "ttc_net")
            coll = sum(a["collisions"] for a in T[(n, q)].values())
            ok = x["delay"][0] >= -5 and vs[0] >= 5 and x["ttc"][0] >= 30 and x["ttc"][1] > 0 and drop >= 20 and x["brake"][0] >= -5 and x["flow"][0] >= -0.5 and not coll
            val = ok and base in HIDDEN and all(beats(n, v + sfx, q) for v in VISIBLE)
            rows.append({"q": q, "cond": sfx or "none", "name": base, "pass": ok, "hidden_value": val, "delay_s": round(med(n, q, "delay"), 1), "ttc": med(n, q, "ttc_net"), "fuel": round(med(n, q, "fuel_km") / 1000, 1), "coll": coll, **{l: v[0] for l, v in x.items()}, "ttc_lo": x["ttc"][1], "ttc_hi": x["ttc"][2], "delay_lo": x["delay"][1], "delay_hi": x["delay"][2]})
            print(f" {base}: delay {med(n, q, 'delay'):.1f} ttc {med(n, q, 'ttc_net'):.0f} b3 {med(n, q, 'brake_net'):.0f} flow {med(n, q, 'passed'):.0f} fuel {med(n, q, 'fuel_km') / 1000:.1f} coll {coll} | v p333 delay {x['delay'][0]:+.1f}[{x['delay'][1]:+.1f},{x['delay'][2]:+.1f}] ttc {x['ttc'][0]:+.1f}[{x['ttc'][1]:+.1f},{x['ttc'][2]:+.1f}] brake {x['brake'][0]:+.1f}{' PASS' if ok else ''}{' HIDDEN-VALUE' if val else ''}")
print("hidden value:", [(r["q"], r["cond"], r["name"]) for r in rows if r["hidden_value"]])
for name in ("p333",):
    for q in sorted({k[1] for k in T}):
        tot = defaultdict(lambda: np.zeros(3))
        for r in T[(name, q)].values():
            for k, v in r["attrib"].items():
                tot[k] += np.array(v, float)
        all_e = sum(tot[c][0] for c in ("alks", "hdv_car", "truck"))
        all_t = sum(tot[c][1] for c in ("alks", "hdv_car", "truck"))
        print(f"--- attribution {name} {q:g}, no X; rate per 1,000 vehicle-seconds, TTC / braking, share of exposure")
        for k in sorted(tot):
            e, t, b = tot[k]
            print(f"  {k}: TTC {1000 * t / e:.2f} brake {1000 * b / e:.2f} exposure {100 * e / all_e:.1f}% ttc share {100 * t / max(all_t, 1):.1f}%")
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
