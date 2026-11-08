"""Spot checks of r3's section 1, 4.2, 6 braking lines, 6.4, 6.5 and the 7(c) oracle."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib2 import *

T = load()
LV = {"X1": [5300], "X2": [5300], "B": [3500, 4500, 5000, 5250, 5500, 6000, 7000]}
SIGN = {"all_delay": -1, "ttc_net": -1, "b3_step": -1, "b45_step": -1, "passed": 1, "finished_pct": 1}


def arms_in(cell, q):
    return sorted({a for (c, a, qq) in T if c == cell and qq == q})


def opps(cell, q):
    return [a for a in arms_in(cell, q) if a not in DRL]


def E(cell, q, a, o, k, pct=(2.5, 97.5)):
    return eff(arm(T, cell, a, q, k), arm(T, cell, o, q, k), SIGN[k], pct)


def mark(t):
    return "A" if t[1] > 0 else ("R" if t[2] < 0 else "=")


print("== marks of v3w against every opponent, b3/b45/passed (R = opponent better) ==")
for cell, qs in LV.items():
    for q in qs:
        for k in ("b3_step", "b45_step", "passed"):
            r = [(o, E(cell, q, "v3w", o, k)) for o in opps(cell, q)]
            Rs = [f"{o} {f1(t)}" for o, t in r if mark(t) == "R"]
            eq = [o for o, t in r if mark(t) == "="]
            print(cell, q, k, "R:", Rs, "| =:", eq)

print("\n== delay / ttc mark counts over 9 settings ==")
cnt = {}
for cell, qs in LV.items():
    for q in qs:
        for o in opps(cell, q):
            for k in ("all_delay", "ttc_net"):
                m = mark(E(cell, q, "v3w", o, k))
                cnt[(k, m)] = cnt.get((k, m), 0) + 1
print(cnt)

print("\n== section 6.4 tail/sw ==")
print("tail vs nc B4500 ttc", f1(E("B", 4500, "tail", "nc", "ttc_net")))
print("tail vs nc X2 ttc", f1(E("X2", 5300, "tail", "nc", "ttc_net")))
print("tail vs 3ex2 X2 delay", f1(E("X2", 5300, "tail", "3ex2", "all_delay")))
print("sw vs nc X2 ttc", f1(E("X2", 5300, "sw", "nc", "ttc_net")), "sw vs 3ex2 X2 ttc", f1(E("X2", 5300, "sw", "3ex2", "ttc_net"), 3))
for a in ("tail", "sw"):
    for cell, qs in LV.items():
        for q in qs:
            if not arms_in(cell, q) or GROUPS[a][0] not in arms_in(cell, q):
                continue
            for k in ("all_delay", "ttc_net", "b3_step", "b45_step", "passed"):
                Rs = [o for o in opps(cell, q) if mark(E(cell, q, a, o, k)) == "R"]
                if Rs:
                    print(a, cell, q, k, "R:", Rs)
print("B4500 b3 v3w vs 3e", f1(E("B", 4500, "v3w", "3e", "b3_step"), 3))
for (cell, q, a, o, k) in [("B", 4500, "v3w", "3e", "all_delay"), ("B", 5250, "tail", "3e", "passed"),
                           ("X2", 5300, "v3w", "lr400_16_1", "b3_step"), ("B", 3500, "v3w", "3e", "passed"),
                           ("B", 5000, "v3w", "os1_15_10", "passed")]:
    print("marginal", cell, q, a, o, k, "95", f1(E(cell, q, a, o, k), 3), "97.5", f1(E(cell, q, a, o, k, (1.25, 98.75)), 3),
          "99", f1(E(cell, q, a, o, k, (0.5, 99.5)), 3))

print("\n== medians (strongest rule) ==")
for cell, qs in LV.items():
    for q in qs:
        md = {o: float(np.median(list(arm(T, cell, o, q, "all_delay").values()))) for o in opps(cell, q) if o != "nc"}
        mc = {o: float(np.median(list(arm(T, cell, o, q, "ttc_net").values()))) for o in opps(cell, q) if o != "nc"}
        vd = float(np.median(list(arm(T, cell, "v3w", q, "all_delay").values())))
        bd = sorted(md.items(), key=lambda t: t[1])[:2]
        bc = sorted(mc.items(), key=lambda t: t[1])[:2]
        print(cell, q, "delay best", bd, "v3w", round(vd, 1), "| cf best", bc)
allarm = {}
for q in [3500, 4500, 5000, 5250, 5500, 6000]:
    names = arms_in("B", q)
    groups = [g for g in GROUPS if GROUPS[g][0] in names] + [a for a in names if a not in DRL]
    med = sorted(((float(np.median(list(arm(T, "B", g, q, "all_delay").values()))), g) for g in groups))
    print("unpaired median delay B", q, [(g, round(m, 1)) for m, g in med[:4]], "v3w", [round(m, 1) for m, g in med if g == "v3w"])

print("\n== oracle ==")
def oracle(cell, mode):
    nc = arm(T, cell, "nc", 5300, "ttc_net")
    if mode == "arm":
        A = [arm(T, cell, g, 5300, "ttc_net") for g in ("v3w", "tail", "sw")]
        o = {s: min(x[s] for x in A) for s in nc}
    else:
        o = {}
        for s in nc:
            vals = []
            for i in range(5):
                vals.append(min(v(T[(cell, GROUPS[g][i], 5300)][s], "ttc_net") for g in ("v3w", "tail", "sw")))
            o[s] = float(np.mean(vals))
    return eff(o, nc, -1)
for cell in ("X1", "X2"):
    print(cell, "v3w", f1(E(cell, 5300, "v3w", "nc", "ttc_net")), "arm", f1(oracle(cell, "arm")), "learner", f1(oracle(cell, "lrn")),
          "3E-T", f1(E(cell, 5300, "3e", "nc", "ttc_net")))

print("\n== section 1 ==")
print("X1 v3w vs nc delay", f1(E("X1", 5300, "v3w", "nc", "all_delay")))
rr = {o: E("X1", 5300, o, "nc", "ttc_net")[0] for o in opps("X1", 5300) if o != "nc"}
print("X1 rules vs nc ttc range", round(min(rr.values()), 1), round(max(rr.values()), 1), sorted((round(x, 1), o) for o, x in rr.items()))
for o in ("3e", "os1_15_10", "p333"):
    print(o, "vs nc X1 ttc", f1(E("X1", 5300, o, "nc", "ttc_net")))
rise = {}
both = sorted(set(arms_in("X1", 5300)) & set(arms_in("X2", 5300)))
for a in list(GROUPS) + [x for x in both if x not in DRL]:
    A1 = arm(T, "X1", a, 5300, "ttc_net"); A2 = arm(T, "X2", a, 5300, "ttc_net")
    rise[a] = eff(A1, A2, -1)
print("X1 vs X2 (neg = more in X1):", {a: f1(t) for a, t in rise.items()})
print("controlled range", min(-t[0] for a, t in rise.items() if a != "nc"), max(-t[0] for a, t in rise.items() if a != "nc"))

print("\n== braking events (m_peak bins: -3,-3.5,-4,-4.5,-5,-6,-7,-8,-9) ==")
def ev(cls, lo):
    return lambda r: sum(sum(r[f"m_peak_{c}"][lo:]) for c in cls)
ALL = ("car", "alks", "truck"); CA = ("car", "alks")
for cell in ("X1", "X2"):
    for name, fn in (("ge40 all", ev(ALL, 2)), ("ge40 car+alks", ev(CA, 2)), ("alks past -5", ev(("alks",), 4)), ("ge45 all", ev(ALL, 3))):
        for o in ("nc", "3e", "p333"):
            P = arm(T, cell, "v3w", 5300, fn); O = arm(T, cell, o, 5300, fn)
            print(cell, name, "v3w vs", o, "diff", f1(mdiff(P, O)), "pct", f1(eff(P, O, 1)),
                  "medians", round(float(np.median(list(P.values()))), 1), round(float(np.median(list(O.values()))), 1))
pl = ev(("alks",), 4)
meds = []
for g in list(GROUPS) + opps("X1", 5300):
    meds.append((round(float(np.median(list(arm(T, "X1", g, 5300, pl).values()))), 2), g))
print("X1 past-limit medians", sorted(meds))
meds2 = sorted((round(float(np.median(list(arm(T, "X2", g, 5300, pl).values()))), 2), g) for g in list(GROUPS) + opps("X2", 5300))
print("X2 past-limit medians, lowest 5", meds2[:5])

print("\n== section 6.5 ==")
for q in (3500, 4500, 5250, 5500):
    print("p333 vs 3e delay", q, f1(E("B", q, "p333", "3e", "all_delay")))
print("os0_10_10 vs p333 X2 delay", f1(E("X2", 5300, "os0_10_10", "p333", "all_delay")))
for o in ("v3w", "3e", "os1_15_10", "p333"):
    P = arm(T, "B", o, 7000, "ttc_net"); O = arm(T, "B", "nc", 7000, "ttc_net")
    print("7000 abs ttc vs nc", o, f1(mdiff(P, O), 0), "| 3500:", f1(mdiff(arm(T, "B", o, 3500, "ttc_net"), arm(T, "B", "nc", 3500, "ttc_net"))))
print("nc 7000 ttc median", np.median(list(arm(T, "B", "nc", 7000, "ttc_net").values())))
print("finished_pct 5000 p333 - v3w (pp)", f1(mdiff(arm(T, "B", "p333", 5000, "finished_pct"), arm(T, "B", "v3w", 5000, "finished_pct")), 2))
tal = {}
for cell, qs in LV.items():
    for q in qs:
        for k in SIGN:
            m = mark(E(cell, q, "v3w", "p333", k))
            tal[m] = tal.get(m, 0) + 1
print("v3w vs p333 tally over 6 metrics", tal)
pl_d = {"A": 0, "R": 0}; pl_c = {"A": 0, "R": 0}
for cell, qs in LV.items():
    for q in qs:
        for n in GROUPS["v3w"]:
            for k, acc in (("all_delay", pl_d), ("ttc_net", pl_c)):
                t = eff(arm(T, cell, n, q, k), arm(T, cell, "p333", q, k), -1)
                m = mark(t)
                if m in acc:
                    acc[m] += 1
                if m == "R":
                    print("per-learner R", cell, q, n, k, f1(t, 2))
print("per-learner tally delay", pl_d, "ttc", pl_c)
for q in (3500, 4500, 5000, 5250, 5500, 6000, 7000):
    print("v3w vs p333 b3/b45", q, f1(E("B", q, "v3w", "p333", "b3_step")), f1(E("B", q, "v3w", "p333", "b45_step")))
print("3500 delay vs nc:", {o: round(E("B", 3500, o, "nc", "all_delay")[0], 1) for o in ("v3w", "p333", "3e")})
print("3500 b45 vs nc (pct, abs):", {o: (round(-E("B", 3500, o, "nc", "b45_step")[0], 1), round(mdiff(arm(T, "B", o, 3500, "b45_step"), arm(T, "B", "nc", 3500, "b45_step"))[0], 1)) for o in ("v3w", "p333", "3e")})
