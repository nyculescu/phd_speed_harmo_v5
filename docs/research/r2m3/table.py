"""V354 reading. Coordination matters if the pattern chosen on 5 seeds beats uniform 0.8 s on 20 other seeds: delay at least 5 % better, CI excluding 0; flow at most 0.5 % worse; network TTC and braking at most 10 % worse; 0 collisions; or the same with TTC at least 30 % better, CI excluding 0, and delay at most 5 % worse. Interaction: the delay of 1.2 s at both merges minus each alone. usage: table.py out_dir out.csv"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

D = Path(sys.argv[1])
M = (("flow", "passed", 1), ("delay", "delay", -1), ("ramp", "delay_ramp", -1), ("ramp2", "delay_ramp2", -1), ("fuel", "fuel_km", -1), ("ttc", "ttc_net", -1), ("brake", "brake_net", -1), ("hard", "b45_net", -1))


def load(f):
    T = defaultdict(dict)
    for line in open(D / f):
        r = json.loads(line)
        T[(r["name"], r["q"])][r["seed"]] = r
    return T


def diff(T, a, b, q, key, sign):
    A, B = T[(a, q)], T[(b, q)]
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
    x = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261103)
    lo, hi = np.percentile(np.median(x[rng.integers(0, len(x), (20000, len(x)))], axis=1), [2.5, 97.5])
    return round(float(np.median(x)), 1), round(float(lo), 1), round(float(hi), 1)


def med(T, n, q, k):
    return float(np.median([a[k] for a in T[(n, q)].values()]))


def show(T, n, q):
    return f"flow {med(T, n, q, 'passed'):.0f} delay {med(T, n, q, 'delay'):.1f} ramp1 {med(T, n, q, 'delay_ramp'):.1f} ramp2 {med(T, n, q, 'delay_ramp2'):.1f} fuel {med(T, n, q, 'fuel_km') / 1000:.1f} ttc {med(T, n, q, 'ttc_net'):.0f} b3 {med(T, n, q, 'brake_net'):.0f} b45 {med(T, n, q, 'b45_net'):.0f} b7 {med(T, n, q, 'b7_net'):.0f} stop1 {med(T, n, q, 'end_stop'):.0f} stop2 {med(T, n, q, 'end_stop2'):.0f} coll {sum(a['collisions'] for a in T[(n, q)].values())}"


L = load("ladder.jsonl")
print("=== ladder, no control: settings of P0 against plain")
for q in sorted({k[1] for k in L}):
    print(f" {q:g} plain: {show(L, 'plain', q)}\n {q:g} P0:    {show(L, 'p0', q)}\n   % better: " + " ".join(f"{l} {diff(L, 'p0', 'plain', q, k, s)[0]:+.1f}" for l, k, s in M))
S = load("select.jsonl")
chosen = json.load(open(D / "chosen.json"))
for q in (4600.0, 5300.0):
    print(f"=== select {q:g}: top by delay", sorted((round(med(S, k[0], q, "delay"), 1), k[0]) for k in S if k[1] == q)[:6], "nc", round(med(S, "nc", q, "delay"), 1), "chosen", chosen[str(q)])
T = load("test.jsonl")
rows = []
for q in (4600.0, 5300.0):
    print(f"=== test {q:g}")
    for n in sorted({k[0] for k in T if k[1] == q}):
        print(f" {n}: {show(T, n, q)}")
    c = chosen[str(q)]
    x = {l: diff(T, c, "p33333", q, k, s) for l, k, s in M}
    coll = sum(a["collisions"] for a in T[(c, q)].values())
    a = x["delay"][0] >= 5 and x["delay"][1] > 0 and x["flow"][0] >= -0.5 and x["ttc"][0] >= -10 and x["brake"][0] >= -10 and not coll
    b = x["ttc"][0] >= 30 and x["ttc"][1] > 0 and x["delay"][0] >= -5 and x["flow"][0] >= -0.5 and x["brake"][0] >= -10 and not coll
    print(f" {c} against p33333: " + " ".join(f"{l} {v[0]:+.1f}[{v[1]:+.1f},{v[2]:+.1f}]" for l, v in x.items()), "MATTERS" if a or b else "no")
    print(" p33333 against nc: " + " ".join(f"{l} {diff(T, 'p33333', 'nc', q, k, s)[0]:+.1f}" for l, k, s in M))
    seeds = sorted(T[("p33333", q)])
    for key, sign in (("delay", 1), ("ttc_net", 1)):
        i = np.array([T[("p31313", q)][s][key] - T[("p31333", q)][s][key] - T[("p33313", q)][s][key] + T[("p33333", q)][s][key] for s in seeds])
        rng = np.random.default_rng(20261103)
        lo, hi = np.percentile(np.median(i[rng.integers(0, len(i), (20000, len(i)))], axis=1), [2.5, 97.5])
        print(f" interaction of the merges on {key}: {np.median(i):+.1f} [{lo:+.1f},{hi:+.1f}]; 1.2 s at merge 1 alone {diff(T, 'p31333', 'p33333', q, key, -1)[0]:+.1f} %, merge 2 alone {diff(T, 'p33313', 'p33333', q, key, -1)[0]:+.1f} %, both {diff(T, 'p31313', 'p33333', q, key, -1)[0]:+.1f} %")
    rows.append({"q": q, "chosen": c, "matters": bool(a or b), **{l: v[0] for l, v in x.items()}, **{l + "_lo": v[1] for l, v in x.items()}, **{l + "_hi": v[2] for l, v in x.items()}})
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
