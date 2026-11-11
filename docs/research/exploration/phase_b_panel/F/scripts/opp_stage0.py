"""EXPLORATORY (S6 rows already read for a verdict). Stage-0 statements for screen F, opponent and plant-validity draft. Reads npz extracts only."""
import numpy as np
B = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/"
Z = np.load(B + "s6/s6_safety.npz"); K = list(Z["keys"]); n = len(Z["seeds"])
L = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda c, a, k: Z[f"{c}|{a}"][:, K.index(k)]
rng = np.random.default_rng(20261110); IDX = rng.integers(0, n, (10000, n))
def eff(P, O, lev=97.5):
    d = -(P - O) / np.median(O) * 100.0
    b = np.median(d[IDX], axis=1)
    return float(np.median(d)), float(np.percentile(b, (100 - lev) / 2)), float(np.percentile(b, 100 - (100 - lev) / 2))
f = lambda t: "%+.1f [%+.1f, %+.1f]" % t
def comp(c, a, fn):
    """fn(cell, arm) -> per-seed vector"""
    O = fn(c, a); per = [eff(fn(c, l), O) for l in L]
    pooled = eff(np.mean([fn(c, l) for l in L], axis=0), O)
    return per, pooled
def line(tag, c, a, fn):
    per, pooled = comp(c, a, fn)
    pts = [p[0] for p in per]
    print("  %-34s %-5s vs %-11s per learner %+.1f..%+.1f, LB>0: %d/5, UB<0: %d/5 | pooled %s | medians v3w %s, opp %.1f" % (
        tag, c, a, min(pts), max(pts), sum(p[1] > 0 for p in per), sum(p[2] < 0 for p in per), f(pooled),
        "/".join("%.0f" % np.median(fn(c, l)) for l in L), np.median(fn(c, a))))
ROADS = ("1", "2", "3a", "3", "4a", "4", "5", "ramp1", "ramp2", "junction")
allr = lambda c, a: sum(col(c, a, f"rt_{r}") for r in ROADS)
m2 = lambda c, a: sum(col(c, a, f"rt_{r}") for r in ("4a", "ramp2", "junction"))
off = lambda c, a: sum(col(c, a, f"rt_{r}") for r in ("1", "2", "3a", "3", "4", "5", "ramp1"))
off_strict = lambda c, a: sum(col(c, a, f"rt_{r}") for r in ("1", "2", "3", "4", "5"))
print("intervals 97.5 %, 10,000 resamples, rng 20261110; positive = v3w lower")
for c in ("TRUCK", "S"):
    for a in ("3E-C_TRUCK", "os0_10_10", "p333", "nc"):
        line("ttc_net (deciding count)", c, a, lambda c, a: col(c, a, "ttc_net"))
        line("road sum (pack m_road_ttc3)", c, a, allr)
        line("merge 2: 4a+ramp2+junction", c, a, m2)
        line("off merge 2 (all other roads)", c, a, off)
        line("off both merges (1,2,3,4,5)", c, a, off_strict)
        line("ttc3 at >= 10 m/s (s_hi)", c, a, lambda c, a: col(c, a, "ttc3_s_hi"))
        line("ttc3 below 5 m/s (s_lo)", c, a, lambda c, a: col(c, a, "ttc3_s_lo"))
        line("delay", c, a, lambda c, a: col(c, a, "all_delay"))
        line("fuel per km", c, a, lambda c, a: col(c, a, "fuel_km"))
        print()
# check: does the road sum equal ttc_net?
for c in ("TRUCK", "S"):
    for a in ("p333", "w0u250"):
        print("check", c, a, "median ttc_net %.1f, road sum %.1f, m_ttc3_all %.1f, ttc3 %.1f; max |ttc_net - road sum| %.1f" % (np.median(col(c, a, "ttc_net")), np.median(allr(c, a)), np.median(col(c, a, "m_ttc3_all")), np.median(col(c, a, "ttc3")), np.max(np.abs(col(c, a, "ttc_net") - allr(c, a)))))
