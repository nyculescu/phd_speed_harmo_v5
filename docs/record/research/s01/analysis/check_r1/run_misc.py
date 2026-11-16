"""Oracle gates, section 1 numbers, braking, per-learner and X1-vs-X2 checks."""
import sys
sys.path.insert(0, ".")
import numpy as np
from mylib import *
T = load()
q = 5300
# Oracle: positive = fewer close-following seconds than nc
for c in ("X1", "X2"):
    nc = arm(T, c, "nc", q, "ttc_net")
    A = {g: arm(T, c, g, q, "ttc_net") for g in ("v3w", "tail", "sw")}
    seeds = sorted(nc)
    armgate = {s: min(A[g][s] for g in A) for s in seeds}
    lrn = {s: np.mean([min(T[(c, G[g][i], q)][s]["ttc_net"] for g in ("v3w", "tail", "sw")) for i in range(5)]) for s in seeds}
    print(c, "v3w", fmt(eff(A["v3w"], nc)), "| arm gate", fmt(eff(armgate, nc)), "| learner gate", fmt(eff(lrn, nc)))
    print(c, "3E-T vs nc", fmt(eff(arm(T, c, "3e", q, "ttc_net"), nc)))
    # which arm the arm-level gate picks
    pick = [min(A, key=lambda g: A[g][s]) for s in seeds]
    print(c, "arm gate picks", {g: pick.count(g) for g in A})
# Section 1(i) rules vs nc X1 ttc_net
nc = arm(T, "X1", "nc", q, "ttc_net")
for a in ("3e", "os1_15_10", "p333", "copy", "lr400_16_1", "a4400_10_1", "3ex1"):
    print("X1 ttc", a, "vs nc", fmt(eff(arm(T, "X1", a, q, "ttc_net"), nc)))
# all rules range of excess
ex = {}
for a in ("3e", "3ex1", "a4400_10_1", "copy", "lr1000_10_1", "lr1000_16_2", "lr400_13_2", "lr400_16_1", "os0_10_10", "os1_10_0", "os1_15_10", "p333", "r4a1", "z33133"):
    ex[a] = round(-eff(arm(T, "X1", a, q, "ttc_net"), nc)[0], 1)
print("X1 rule excess range", min(ex.values()), max(ex.values()), sorted(ex.items(), key=lambda x: x[1]))
# X1 vs X2 per arm (positive = fewer in X1)
for a in ("nc", "v3w", "p333", "os1_15_10", "3e", "tail", "sw", "bv3"):
    print("X1 vs X2", a, fmt(eff(arm(T, "X1", a, q, "ttc_net"), arm(T, "X2", a, q, "ttc_net"))))
# braking robust counts: ev4 = m_peak bins 2+
def ev4(cls):
    def f(r):
        s = 0.0
        for c in cls:
            pk = r.get(f"m_peak_{c}")
            if pk: s += sum(pk[2:])
        return s
    return f
ev4all = ev4(("car", "alks", "truck")); ev4ca = ev4(("car", "alks"))
for c in ("X1", "X2"):
    print(c, "ev4 all v3w vs nc", fmt(eff(arm(T, c, "v3w", q, ev4all), arm(T, c, "nc", q, ev4all))))
    print(c, "ev4 all v3w vs 3E-T", fmt(eff(arm(T, c, "v3w", q, ev4all), arm(T, c, "3e", q, ev4all))))
print("X1 ev4 car+alks v3w vs nc", fmt(eff(arm(T, "X1", "v3w", q, ev4ca), arm(T, "X1", "nc", q, ev4ca))))
perserved = lambda r: ev4all(r) / float(r["passed"])
print("X1 ev4 all per served", fmt(eff(arm(T, "X1", "v3w", q, perserved), arm(T, "X1", "nc", q, perserved))))
# past-limit ALKS events, bins 4-7
ev5 = lambda r: float(sum(r["m_peak_alks"][4:8])) if r.get("m_peak_alks") else 0.0
for c in ("X1", "X2"):
    meds = {}
    for a in sorted({a for (cc, a, qq) in T if cc == c}):
        if any(a in v for v in G.values()):
            continue
        meds[a] = med(arm(T, c, a, q, ev5)) if False else float(np.median(list(arm(T, c, a, q, ev5).values())))
    for g in G:
        meds[g] = float(np.median(list(arm(T, c, g, q, ev5).values())))
    print(c, "ev5_alks medians", sorted((round(v, 1), k) for k, v in meds.items()))
    print(c, "ev5 v3w-3E-T", fmt(mdiff(arm(T, c, "v3w", q, ev5), arm(T, c, "3e", q, ev5))), "v3w-p333", fmt(mdiff(arm(T, c, "v3w", q, ev5), arm(T, c, "p333", q, ev5))))
# per-learner delay vs p333 (positive = learner better)
for (c, lv) in (("X1", 5300), ("X2", 5300), ("B", 5500), ("B", 6000), ("B", 7000), ("B", 3500), ("B", 4500), ("B", 5000), ("B", 5250)):
    p = arm(T, c, "p333", lv, "all_delay")
    res = [eff(arm(T, c, n, lv, "all_delay"), p) for n in G["v3w"]]
    print("per learner delay vs p333", c, lv, "v3w shown", sum(r[1] > 0 for r in res), "p333 shown", sum(r[2] < 0 for r in res), [f"{r[0]:+.2f}[{r[1]:+.2f},{r[2]:+.2f}]" for r in res])
# 4,500 b3 vs 3E-T
print("B4500 b3 vs 3E-T", eff(arm(T, "B", "v3w", 4500, "b3_step"), arm(T, "B", "3e", 4500, "b3_step")))
# X1 b45, b3 vs no control / 3E-T / copy; flow vs rules
for a in ("nc", "3e", "copy", "3ex1", "a4400_10_1"):
    print("X1 b45 v3w vs", a, fmt(eff(arm(T, "X1", "v3w", q, "b45_step"), arm(T, "X1", a, q, "b45_step"))))
print("X1 b45 v3w vs p333", fmt(eff(arm(T, "X1", "v3w", q, "b45_step"), arm(T, "X1", "p333", q, "b45_step"))))
