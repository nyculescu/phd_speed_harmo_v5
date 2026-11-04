"""V343 reading. For each level and X: resilience (loss against own no-X run), and the best oracle against p333 under the same X.
Headroom if delay is at least 5 % better than p333 under X, CI excluding 0. usage: oracle_table.py rows.jsonl out.csv"""
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


def diff(A, B, key, sign):
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
    d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261103)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)


def med(A, k):
    return float(np.median([a[k] for a in A.values()]))


def fmt(x):
    return " ".join(f"{k} {v[0]:+.1f}[{v[1]:+.1f},{v[2]:+.1f}]" for k, v in x.items())


out = []
for q in sorted({k[1] for k in T}):
    print(f"=== {q:g}: delay no X: no control {med(T[('nc', q)], 'delay'):.1f} s, p333 {med(T[('p333', q)], 'delay'):.1f} s")
    for lim in (25, 40):
        nx, px = T[(f"nc_slow{lim}", q)], T[(f"p333_slow{lim}", q)]
        print(f" slow{lim}: under X no control {med(nx, 'delay'):.1f} s coll {sum(a['collisions'] for a in nx.values())}, p333 {med(px, 'delay'):.1f} s coll {sum(a['collisions'] for a in px.values())}")
        print("  no control loss to X:", fmt({l: diff(nx, T[("nc", q)], k, s) for l, k, s in M}))
        print("  p333 loss to X:      ", fmt({l: diff(px, T[("p333", q)], k, s) for l, k, s in M}))
        print("  p333 against no control, both under X:", fmt({l: diff(px, nx, k, s) for l, k, s in M}))
        for h in ("nc", "p333"):
            names = sorted(k[0] for k in T if k[1] == q and k[0].startswith(f"{h}_slow{lim}_o"))
            best = min(names, key=lambda n: med(T[(n, q)], "delay"))
            for n in names:
                x = {l: diff(T[(n, q)], px, k, s) for l, k, s in M}
                head = x["delay"][0] >= 5 and x["delay"][1] > 0
                rec = (med(T[(f"{h}_slow{lim}", q)], "delay") - med(T[(n, q)], "delay")) / max(med(T[(f"{h}_slow{lim}", q)], "delay") - med(T[(h, q)], "delay"), 1e-9)
                out.append({"q": q, "x": f"slow{lim}", "head": h, "name": n, "delay_s": round(med(T[(n, q)], "delay"), 1), "fuel_g_km": round(med(T[(n, q)], "fuel_km") / 1000, 1), "collisions": sum(a["collisions"] for a in T[(n, q)].values()), "recovered_share": round(rec, 2), "headroom": head, **{f"{l}_v_p333": v[0] for l, v in x.items()}, **{f"{l}_lo": v[1] for l, v in x.items()}, **{f"{l}_hi": v[2] for l, v in x.items()}})
                if n == best:
                    print(f"  best oracle on {h}: {n} delay {med(T[(n, q)], 'delay'):.1f} s, recovers {rec:.2f} of its own loss, coll {out[-1]['collisions']}; against p333 under X: {fmt(x)}{' HEADROOM' if head else ''}")
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(out[0]))
    w.writeheader()
    w.writerows(out)
