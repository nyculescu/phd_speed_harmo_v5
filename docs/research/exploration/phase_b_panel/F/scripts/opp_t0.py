"""EXPLORATORY (S6 rows already read for a verdict). T0-type statements, lane-change split and delay non-inferiority from stored rows."""
import numpy as np
B = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/"
Z = np.load(B + "panel/F/opp_t0.npz"); K = list(Z["keys"]); n = len(Z["seeds"])
S6 = np.load(B + "s6/s6_safety.npz"); K6 = list(S6["keys"])
L = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda c, a, k: Z[f"{c}|{a}"][:, K.index(k)]
c6 = lambda c, a, k: S6[f"{c}|{a}"][:, K6.index(k)]
rng = np.random.default_rng(20261110); IDX = rng.integers(0, n, (10000, n))
def eff(P, O, lev=97.5, sign=-1.0):
    d = sign * (P - O) / np.median(O) * 100.0
    b = np.median(d[IDX], axis=1)
    return float(np.median(d)), float(np.percentile(b, (100 - lev) / 2)), float(np.percentile(b, 100 - (100 - lev) / 2))
f = lambda t: "%+.2f [%+.2f, %+.2f]" % t
arms = sorted({k.split("|", 1)[1] for k in Z.files if "|" in k})
print("arms:", len(arms))
print("== readback (tau): all rows of each cell")
for c in ("TRUCK", "S"):
    mm = sum(col(c, a, "tau_mismatch").sum() for a in arms if a != "nc" and not np.isnan(col(c, a, "tau_mismatch")).any())
    tot = [(a, np.nansum(col(c, a, "tau_on_match")), np.nansum(col(c, a, "tau_on_n"))) for a in arms]
    worst = min(((m / t, a) for a, m, t in tot if t > 0), default=None)
    print(" ", c, "sum tau_mismatch over arms:", mm, "| lowest tau_on_match/tau_on_n:", worst, "| arms with tau_on_n = 0:", [a for a, m, t in tot if not t > 0])
    for a in ("nc", "p333", "3E-C_TRUCK", "os0_10_10", "w0u250"):
        lv = np.nansum(col(c, a, "lv_sum")) / max(np.nansum(col(c, a, "lv_n")), 1)
        print("    %-11s mean commanded level %.3f (0..3), tau_on share of ALKS-seconds %.3f, mismatch %s" % (a, lv, np.nansum(col(c, a, "tau_on_n")) / max(np.nansum(col(c, a, "lv_n")), 1), np.nansum(col(c, a, "tau_mismatch"))))
print("== p333 against no control, positive = p333 higher (flow, mean speed) / lower (vehicle-seconds N, delay); 95 %")
for c in ("TRUCK", "S"):
    print(" ", c, "served flow", f(eff(col(c, "p333", "passed"), col(c, "nc", "passed"), 95, +1.0)), "| vehicle-seconds N", f(eff(col(c, "p333", "N"), col(c, "nc", "N"), 95)),
          "| mean speed", f(eff(col(c, "p333", "mean_v"), col(c, "nc", "mean_v"), 95, +1.0)), "| delay", f(eff(col(c, "p333", "all_delay"), col(c, "nc", "all_delay"), 95)))
print("== close-following outside the 5 s after a lane change (m_ttc3_all - m_ttc3_lc), and inside; 97.5 %")
nolc = lambda c, a: col(c, a, "m_ttc3_all") - col(c, a, "m_ttc3_lc")
lc = lambda c, a: col(c, a, "m_ttc3_lc")
offm = lambda c, a: sum(c6(c, a, f"rt_{r}") for r in ("1", "2", "3", "4", "5"))
hi = lambda c, a: c6(c, a, "ttc3_s_hi")
for c in ("TRUCK", "S"):
    for o in ("3E-C_TRUCK", "os0_10_10", "p333"):
        for tag, fn in (("no lane change", nolc), ("within 5 s of a lane change", lc), ("outside both merge sections", offm), (">= 10 m/s", hi)):
            per = [eff(fn(c, l), fn(c, o)) for l in L]
            pooled = eff(np.mean([fn(c, l) for l in L], axis=0), fn(c, o))
            print("  %-5s vs %-11s %-28s per learner %+.1f..%+.1f, LB>0 %d/5 | pooled %s | medians v3w %.0f-%.0f, opp %.0f" % (c, o, tag, min(p[0] for p in per), max(p[0] for p in per), sum(p[1] > 0 for p in per), f(pooled), min(np.median(fn(c, l)) for l in L), max(np.median(fn(c, l)) for l in L), np.median(fn(c, o))))
print("== delay non-inferiority of single learners, margin 2 %: learners with the 97.5 % lower bound above -2 %, per opponent (all 23)")
OPP = [a for a in arms if a not in L and a != "nc" and not a.startswith(("w", "C"))]
print("opponents:", len(OPP), OPP)
for c in ("TRUCK", "S"):
    worst = []
    for o in OPP:
        if f"{c}|{o}" not in Z.files: continue
        per = [eff(col(c, l, "all_delay"), col(c, o, "all_delay")) for l in L]
        worst.append((sum(p[1] > -2.0 for p in per), sum(p[1] > -1.0 for p in per), min(p[1] for p in per), min(p[0] for p in per), o))
    worst.sort()
    print(" ", c, "opponents with fewer than 5 of 5 learners non-inferior at 2 %:", [(w[4], w[0]) for w in worst if w[0] < 5])
    print(" ", c, "opponents with fewer than 4 of 5 at 2 %:", [(w[4], w[0]) for w in worst if w[0] < 4], "| at 1 %: fewer than 4 of 5:", [(w[4], w[1]) for w in worst if w[1] < 4])
    print(" ", c, "lowest single-learner lower bound:", min((w[2], w[4]) for w in worst), "| lowest single-learner point:", min((w[3], w[4]) for w in worst))
    # admission of rules: point delay change against p333 at most 2 % worse, and its 97.5 % lower bound
    for o in ("3E-C_TRUCK", "3E-D_TRUCK", "os0_10_10", "lr400_16_1", "3ex2", "grid_lr400_13_1", "os1_15_10"):
        if f"{c}|{o}" in Z.files:
            print("     rule %-16s delay against p333 %s (97.5 %%) | close-following against p333 %s" % (o, f(eff(col(c, o, "all_delay"), col(c, "p333", "all_delay"))), f(eff(col(c, o, "ttc_net"), col(c, "p333", "ttc_net")))))
