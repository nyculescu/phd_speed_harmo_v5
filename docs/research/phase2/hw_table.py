"""V346 rule, against p333 under the same X, at one level and X: delay at most 5 % worse and still at least 5 % better than no
control under X; network TTC at least 30 % better, CI excluding 0, and at least 20 per run lower; braking at 3 m/s² at most 5 %
worse; flow at most 0.5 % worse; 0 collisions. usage: hw_table.py rows.jsonl out.csv"""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

from upstream import beyond

T = defaultdict(dict)
ST = {}
for line in open(sys.argv[1]):
    r = json.loads(line)
    if "st_v" in r:
        ST[(r["name"], r["q"], r["seed"])] = (np.array(r.pop("st_v"), float).reshape(150, 65) / 10.0, np.array(r.pop("st_n"), float).reshape(150, 65))
    T[(r["name"], r["q"])][r["seed"]] = r
M = (("flow", "passed", 1), ("delay", "delay", -1), ("ramp", "delay_ramp", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake", "brake_net", -1), ("hard", "b45_net", -1), ("b7", "b7_net", -1))


def diff(A, B, key, sign):
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
    d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261103)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)


def med(A, k):
    return float(np.median([a[k] for a in A.values()]))


def show(n, q):
    A = T[(n, q)]
    return f"delay {med(A, 'delay'):.1f} flow {med(A, 'passed'):.0f} fuel {med(A, 'fuel_km') / 1000:.1f} ttc {med(A, 'ttc_net'):.0f} b3 {med(A, 'brake_net'):.0f} b45 {med(A, 'b45_net'):.0f} b7 {med(A, 'b7_net'):.0f} coll {sum(a['collisions'] for a in A.values())}"


out = []
for q in sorted({k[1] for k in T}):
    print(f"=== {q:g}\n nc: {show('nc', q)}\n p333: {show('p333', q)}")
    for lim in (25, 40):
        nx, px = T[(f"nc_slow{lim}", q)], T[(f"p333_slow{lim}", q)]
        up = [beyond(*ST[(f"nc_slow{lim}", q, s)], *ST[("nc", q, s)], 4989.02)[0] for s in sorted(nx)]
        print(f" slow{lim} tapered: upstream travel median {np.median(up):.0f} m, {sum(x >= 500 for x in up)} of {len(up)} reach 500 m\n  nc: {show(f'nc_slow{lim}', q)}\n  p333: {show(f'p333_slow{lim}', q)}")
        for d in (500, 1000, 2000):
            for lv in (0, 1):
                n = f"hw{lim}_d{d}_l{lv}"
                x = {l: diff(T[(n, q)], px, k, s) for l, k, s in M}
                vs_nc = diff(T[(n, q)], nx, "delay", -1)
                drop = med(px, "ttc_net") - med(T[(n, q)], "ttc_net")
                coll = sum(a["collisions"] for a in T[(n, q)].values())
                ok = x["delay"][0] >= -5 and vs_nc[0] >= 5 and x["ttc"][0] >= 30 and x["ttc"][1] > 0 and drop >= 20 and x["brake"][0] >= -5 and x["flow"][0] >= -0.5 and not coll
                out.append({"q": q, "x": lim, "d": d, "level": lv, "pass": ok, "delay_v_nc": vs_nc[0], "ttc_drop": drop, "collisions": coll, **{f"{l}": v[0] for l, v in x.items()}, **{f"{l}_lo": v[1] for l, v in x.items()}, **{f"{l}_hi": v[2] for l, v in x.items()}})
                print(f"  {n}: {show(n, q)} | v p333: " + " ".join(f"{l} {v[0]:+.1f}[{v[1]:+.1f},{v[2]:+.1f}]" for l, v in x.items() if l in ("delay", "fuel", "ttc", "brake", "hard")) + f" | v nc delay {vs_nc[0]:+.1f}" + (" PASS" if ok else ""))
print("cases passing:", [(r["q"], r["x"], r["d"], r["level"]) for r in out if r["pass"]])
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(out[0]))
    w.writeheader()
    w.writerows(out)
