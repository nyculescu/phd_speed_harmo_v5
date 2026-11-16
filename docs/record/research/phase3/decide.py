"""Confirmatory 2 claim rules, as fixed in confirmatory_2.md. usage: decide.py rows.jsonl out.csv. Higher is better in every difference."""
import csv
import json
import sys
from collections import defaultdict

import numpy as np

T = defaultdict(dict)
for line in open(sys.argv[1]):
    r = json.loads(line)
    T[(r["name"], r["q"])][r["seed"]] = r
M = (("flow", "passed", 1), ("delay", "delay", -1), ("ttc", "ttc_net", -1), ("brake", "brake_net", -1), ("fuel", "fuel_km", -1), ("ramp", "delay_ramp", -1), ("hard", "b45_net", -1))
PCT = {20: (0.125, 99.875), 8: (0.3125, 99.6875), 1: (2.5, 97.5)}


def diff(a, b, q, key, sign, n=20):
    A, B = T[(a, q)], T[(b, q)]
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([B[k][key] for k in ds])), 1e-9)
    d = np.array([sign * (A[k][key] - B[k][key]) / ref * 100 for k in ds])
    rng = np.random.default_rng(20261104)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), PCT[n])
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1)


def med(n, q, k):
    return float(np.median([a[k] for a in T[(n, q)].values()]))


def coll(n, q):
    return sum(a["collisions"] for a in T[(n, q)].values())


def show(n, q):
    return f"flow {med(n, q, 'passed'):.0f} delay {med(n, q, 'delay'):.1f} fuel {med(n, q, 'fuel_km') / 1000:.1f} ttc {med(n, q, 'ttc_net'):.0f} b3 {med(n, q, 'brake_net'):.0f} b45 {med(n, q, 'b45_net'):.0f} coll {coll(n, q)}"


rows, wins = [], []
for plant in ("r1m3", "r2m3"):
    for cond in ("S", "X1", "X2", "H1", "H2"):
        for q in (4600.0, 5300.0):
            key = f"{plant}|{cond}|"
            opp = min((key + "p333", key + "lr"), key=lambda n: med(n, q, "delay"))
            print(f"=== {plant} {cond} {q:g}: opponent {opp.split('|')[2]}")
            for n in ("nc", "p333", "lr"):
                print(f"  {n}: {show(key + n, q)}")
            nd = ns = 0
            for i in range(3):
                n = key + f"d{i}"
                x = {l: diff(n, opp, q, k, s) for l, k, s in M}
                x95 = {l: diff(n, opp, q, k, s, 1) for l, k, s in M}
                c, oc = coll(n, q), coll(opp, q)
                dw = x["delay"][0] >= 5 and x["delay"][1] > 0 and x["flow"][0] >= -0.5 and x["ttc"][0] >= -10 and x["brake"][0] >= -10 and c <= oc + 1
                drop = med(opp, q, "ttc_net") - med(n, q, "ttc_net")
                sw = x["ttc"][0] >= 30 and x["ttc"][1] > 0 and drop >= 20 and x["delay"][0] >= -2 and x["flow"][0] >= -0.5 and x["brake"][0] >= -5 and c <= oc + 1
                nd += dw
                ns += sw
                rows.append({"plant": plant, "cond": cond, "q": q, "policy": f"d{i}", "opponent": opp.split("|")[2], "delay_win": dw, "safety_win": sw, "delay_s": round(med(n, q, "delay"), 1), "opp_delay_s": round(med(opp, q, "delay"), 1), "ttc": med(n, q, "ttc_net"), "opp_ttc": med(opp, q, "ttc_net"), "coll": c, "opp_coll": oc, **{l: v[0] for l, v in x.items()}, **{l + "_lo": v[1] for l, v in x.items()}, **{l + "_hi": v[2] for l, v in x.items()}, **{l + "_lo95": v[1] for l, v in x95.items()}, **{l + "_hi95": v[2] for l, v in x95.items()}})
                print(f"  d{i}: {show(n, q)} | " + " ".join(f"{l} {v[0]:+.1f}[{v[1]:+.1f},{v[2]:+.1f}]" for l, v in x.items() if l in ("flow", "delay", "ttc", "brake", "fuel")) + (" DELAY-WIN" if dw else "") + (" SAFETY-WIN" if sw else ""))
            if nd >= 2:
                wins.append((plant, cond, q, "delay"))
            if ns >= 2:
                wins.append((plant, cond, q, "safety"))
print("DRL cells won:", wins)
print("--- adaptive rule against p333, safety rule, Bonferroni over 8")
rule = []
for plant in ("r1m3", "r2m3"):
    for cond in ("X1", "X2"):
        for q in (4600.0, 5300.0):
            a, b, key = f"{plant}|{cond}|lr", f"{plant}|{cond}|p333", f"{plant}|{cond}"
            t, d, f, br = diff(a, b, q, "ttc_net", -1, 8), diff(a, b, q, "delay", -1, 8), diff(a, b, q, "passed", 1, 8), diff(a, b, q, "brake_net", -1, 8)
            drop = med(b, q, "ttc_net") - med(a, q, "ttc_net")
            ok = t[0] >= 30 and t[1] > 0 and drop >= 20 and d[0] >= -5 and f[0] >= -0.5 and br[0] >= -5 and coll(a, q) <= coll(b, q) + 1
            if ok:
                rule.append((plant, cond, q))
            print(f" {key} {q:g}: ttc {med(a, q, 'ttc_net'):.0f} v {med(b, q, 'ttc_net'):.0f} {t} delay {d} flow {f[0]} brake {br[0]} coll {coll(a, q)} v {coll(b, q)}", "WIN" if ok else "")
print("adaptive rule cells won:", rule)
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0]))
    w.writeheader()
    w.writerows(rows)
