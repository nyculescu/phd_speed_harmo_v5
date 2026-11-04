"""V348 reading. Pass under X: the V346 rule against p333 and no control under the same X. A setting matches if it passes for
slow25 at both levels and, without X, its delay is at most 2 % worse than p333's. The local rule is chosen on seeds 750-754 and
read on 755-759. usage: stepa_table.py rows.jsonl out.csv"""
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
SEL, TEST = range(7_419_750, 7_419_755), range(7_419_755, 7_419_760)
ALL = range(7_419_750, 7_419_760)
LOCAL = sorted({k[0] for k in T if k[0].startswith("lr") and "_slow" not in k[0]})


def diff(a, b, q, key, sign, seeds):
    A, B = T[(a, q)], T[(b, q)]
    ref = max(float(np.median([B[k][key] for k in seeds])), 1e-9)
    d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in seeds])
    rng = np.random.default_rng(20261103)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), [2.5, 97.5])
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)


def med(n, q, key, seeds):
    return float(np.median([T[(n, q)][k][key] for k in seeds]))


def under_x(n, x, q, seeds):
    p, nc = f"p333_{x}", f"nc_{x}"
    d, t, b, f = diff(n, p, q, "delay", -1, seeds), diff(n, p, q, "ttc_net", -1, seeds), diff(n, p, q, "brake_net", -1, seeds), diff(n, p, q, "passed", 1, seeds)
    vs = diff(n, nc, q, "delay", -1, seeds)
    drop = med(p, q, "ttc_net", seeds) - med(n, q, "ttc_net", seeds)
    coll = sum(T[(n, q)][k]["collisions"] for k in seeds)
    ok = d[0] >= -5 and vs[0] >= 5 and t[0] >= 30 and t[1] > 0 and drop >= 20 and b[0] >= -5 and f[0] >= -0.5 and not coll
    return ok, {"delay_s": round(med(n, q, "delay", seeds), 1), "ttc": med(n, q, "ttc_net", seeds), "fuel": round(med(n, q, "fuel_km", seeds) / 1000, 1), "brake": med(n, q, "brake_net", seeds), "flow": med(n, q, "passed", seeds), "coll": coll, "delay_v_p333": d, "ttc_v_p333": t, "brake_v_p333": b, "delay_v_nc": vs[0]}


def no_x(n, q, seeds):
    return diff(n, "p333", q, "delay", -1, seeds)


def matches(n, seeds):
    a = [under_x(f"{n}_slow25", "slow25", q, seeds)[0] for q in LEVELS]
    b = [no_x(n, q, seeds)[0] >= -2 for q in LEVELS]
    return all(a) and all(b), a, b


rows = []
for q in LEVELS:
    print(f"=== {q:g}, all 10 seeds")
    for n in ("nc", "p111", "p222", "p333"):
        print(f" {n} no X: delay {med(n, q, 'delay', ALL):.1f} ttc {med(n, q, 'ttc_net', ALL):.0f} fuel {med(n, q, 'fuel_km', ALL) / 1000:.1f} flow {med(n, q, 'passed', ALL):.0f} coll {sum(r['collisions'] for r in T[(n, q)].values())}")
    for x in ("slow25", "slow40"):
        for n in ("nc", "p111", "p222", "p333", "oracle"):
            nn = f"{n}_{x}"
            ok, s = under_x(nn, x, q, ALL)
            rows.append({"seeds": "all", "q": q, "x": x, "name": n, "pass": ok, **s})
            print(f" {x} {n}: {'PASS ' if ok else ''}{s}")
print("--- fixed settings, all 10 seeds, match:", {n: matches(n, ALL) for n in ("p111", "p222")})
score = {}
for n in LOCAL:
    a = [under_x(f"{n}_slow25", "slow25", q, SEL)[0] for q in LEVELS]
    b = [no_x(n, q, SEL)[0] >= -2 for q in LEVELS]
    score[n] = (sum(a) + sum(b), -np.mean([med(f"{n}_slow25", q, "delay", SEL) for q in LEVELS]), a, b)
    print(n, "selection seeds: pass under X", a, "no false alarm", b, "no X delay v p333", [no_x(n, q, SEL)[0] for q in LEVELS], "ttc under slow25", [med(f"{n}_slow25", q, "ttc_net", SEL) for q in LEVELS])
best = max(LOCAL, key=lambda n: score[n][:2])
print("chosen local rule:", best)
print("test seeds 755-759:", matches(best, TEST))
for q in LEVELS:
    print(f" {q:g} no X delay v p333", no_x(best, q, TEST), "ttc no X", med(best, q, "ttc_net", TEST), "p333", med("p333", q, "ttc_net", TEST))
    for x in ("slow25", "slow40"):
        for n in (best, "oracle", "p333", "nc"):
            ok, s = under_x(f"{n}_{x}", x, q, TEST)
            rows.append({"seeds": "test", "q": q, "x": x, "name": n, "pass": ok, **s})
            print(f"  {x} {n}: {'PASS ' if ok else ''}{s}")
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
