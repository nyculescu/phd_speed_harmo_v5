"""V350 reading: the V348 match for lr against p333 on its 30-s clock; p333 on the rule's 10-s clock is reported only. usage: confirm_table.py rows.jsonl out.csv"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    T[(r["name"], r["q"])][r["seed"]] = r
LEVELS = (4090.0, 4600.0)
M = (("flow", "passed", 1), ("delay", "delay", -1), ("ramp", "delay_ramp", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake", "brake_net", -1), ("hard", "b45_net", -1))


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


def fmt(x):
    return " ".join(f"{k} {v[0]:+.1f}[{v[1]:+.1f},{v[2]:+.1f}]" for k, v in x.items())


def show(n, q):
    return f"delay {med(n, q, 'delay'):.1f} flow {med(n, q, 'passed'):.0f} fuel {med(n, q, 'fuel_km') / 1000:.1f} ttc {med(n, q, 'ttc_net'):.0f} b3 {med(n, q, 'brake_net'):.0f} b45 {med(n, q, 'b45_net'):.0f} coll {sum(a['collisions'] for a in T[(n, q)].values())}"


rows, match = [], []
for q in LEVELS:
    print(f"=== {q:g}")
    for n in ("nc", "p333", "p333h10", "lr"):
        print(f" {n} no X: {show(n, q)}")
    nox = diff("lr", "p333", q, "delay", -1)
    print(" lr v p333 no X:", fmt({l: diff("lr", "p333", q, k, s) for l, k, s in M}))
    print(" lr v p333h10 no X:", fmt({l: diff("lr", "p333h10", q, k, s) for l, k, s in M}))
    for x in ("slow25", "slow40"):
        for n in ("nc", "p333", "p333h10", "oracle", "lr"):
            print(f" {x} {n}: {show(f'{n}_{x}', q)}")
        n, p = f"lr_{x}", f"p333_{x}"
        v = {l: diff(n, p, q, k, s) for l, k, s in M}
        vs = diff(n, f"nc_{x}", q, "delay", -1)
        drop = med(p, q, "ttc_net") - med(n, q, "ttc_net")
        coll = sum(a["collisions"] for a in T[(n, q)].values())
        ok = v["delay"][0] >= -5 and vs[0] >= 5 and v["ttc"][0] >= 30 and v["ttc"][1] > 0 and drop >= 20 and v["brake"][0] >= -5 and v["flow"][0] >= -0.5 and not coll
        print(f"  lr v p333 under {x}: {fmt(v)} | v nc delay {vs[0]:+.1f} | {'PASS' if ok else 'fail'}")
        print(f"  lr v p333h10 under {x}: {fmt({l: diff(n, f'p333h10_{x}', q, k, s) for l, k, s in M})}")
        print(f"  oracle v p333 under {x}: {fmt({l: diff(f'oracle_{x}', p, q, k, s) for l, k, s in M})}")
        rows.append({"q": q, "x": x, "pass": ok, "no_x_delay": nox[0], **{l: v[l][0] for l in v}, **{l + "_lo": v[l][1] for l in v}, **{l + "_hi": v[l][2] for l in v}})
        if x == "slow25":
            match.append(ok and nox[0] >= -2)
print("MATCH at both levels:" , all(match), match)
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
