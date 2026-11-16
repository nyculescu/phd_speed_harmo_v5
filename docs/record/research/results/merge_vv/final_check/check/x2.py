# Final check: recompute the plan's expectation numbers from the stored E30 rows (own rng).
import numpy as np
from math import erf, sqrt
Z = np.load("cols.npz"); arms = list(Z["arms"]); A = {a: i for i, a in enumerate(arms)}
V = [a for a in arms if a.split("|")[1][0] == "w" and a.split("|")[1][1].isdigit()]
R = [a for a in arms if a not in V]
c = lambda a, k: Z[k][A[a]]
n = Z["ttc_net"].shape[1]
rng = np.random.default_rng(20261115); B = 10000
IDX = rng.integers(0, n, (B, n))
Phi = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
def edge(opp, f, idx=IDX):
    O = f(opp); m = np.median(O)
    D = [-(f(w) - O) / m * 100 for w in V]
    return np.mean([np.median(d) for d in D]), np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
K = lambda k: (lambda a: c(a, k))
print("learners", V)
print("ttc_net == E30+out_E30:", np.array_equal(Z["ttc_net"], Z["e30"] + Z["oute30"]), "; == road sum:", np.array_equal(Z["ttc_net"], Z["roadsum"]))
print("\n[1] edges on ttc_net and delay, all non-learning arms, sorted by ttc edge (point; 97.5 % interval = pct 1.25-98.75)")
rows = []
small = IDX[:3000]
for r in R:
    pt, b = edge(r, K("ttc_net"), small); dp, db = edge(r, K("delay"), small)
    rows.append((pt, r, np.percentile(b, 1.25), np.percentile(b, 98.75), dp, np.percentile(db, 1.25)))
for pt, r, lo, hi, dp, dlo in sorted(rows):
    print("  %-22s E %+6.2f [%+6.2f,%+6.2f]  D %+5.2f (lower %+5.2f) %s" % (r, pt, lo, hi, dp, dlo, "competitor" if dlo <= 1 or r.endswith("p333") else "trade point"))
LR, GR = "E30|lr400_16_1", "E30|grid_lr400_13_1"
print("\n[2] composition, medians per run and shares of sums")
for a in V + [LR, GR, "E30|p333", "E30|nc"]:
    tot = c(a, "ttc_net").sum()
    print("  %-20s med ttc %7.1f m1 %6.1f m2 %6.1f edge1 %5.1f rest %6.1f junction %5.1f | share merge(3a,4a,ramps) %.3f junction %.3f edge1 %.3f rest %.3f | es %6.1f es2 %6.1f" % (
        a, *(np.median(c(a, k)) for k in ["ttc_net", "m1", "m2", "e1", "rest", "jn"]), (c(a, "m1") + c(a, "m2")).sum() / tot, c(a, "jn").sum() / tot, c(a, "e1").sum() / tot, c(a, "rest").sum() / tot, np.median(c(a, "es")), np.median(c(a, "es2"))))
print("\n[3] merge-scaling model: merge-area counts (3a, 4a, ramps) x k in every arm, the rest unchanged")
def model(k, drop_e1=False):
    return lambda a: k * (c(a, "m1") + c(a, "m2")) + c(a, "rest") + c(a, "jn") + (0 if drop_e1 else c(a, "e1"))
for opp in (LR, GR):
    for k in (1.0, 0.34, 0.2, 0.1, 0.02):
        pt, b = edge(opp, model(k)); se = b.std(); lo, hi = np.percentile(b, [1.25, 98.75]); hi2 = np.percentile(b, 99.375)
        print("  %-20s k=%.2f edge %+6.2f SE %.2f 97.5%% [%+6.2f,%+6.2f] | P(lower>0) normal %.3f | P(98.75%% upper<0) normal %.3f | edge with power .9: n=480 %.1f, n=960 %.1f | P(lower>0) at n=960 %.3f" % (
            opp.split("|")[1], k, pt, se, lo, hi, Phi(pt / se - 2.2414), Phi(-pt / se - 2.4977), 3.523 * se, 3.523 * se / sqrt(2), Phi(pt / (se / sqrt(2)) - 2.2414)))
print("  same model without edge 1 (entry) samples, against lr400_16_1:")
for k in (1.0, 0.34, 0.2, 0.1, 0.02):
    pt, b = edge(LR, model(k, True)); print("    k=%.2f edge %+6.2f SE %.2f [%+6.2f,%+6.2f]" % (k, pt, b.std(), *np.percentile(b, [1.25, 98.75])))
print("\n[4] V2 proxy: ttc_half edge minus ttc_net edge, same runs")
for opp in (LR, GR):
    p1, b1 = edge(opp, K("ttc_net")); p2, b2 = edge(opp, K("ttc_half")); d = b2 - b1; se = d.std()
    print("  %-20s net %+6.2f (SE %.2f) half %+6.2f diff %+5.2f SE %.3f 95%% [%+5.2f,%+5.2f]; corr of boot edges %.3f" % (opp.split("|")[1], p1, b1.std(), p2, p2 - p1, se, *np.percentile(d, [2.5, 97.5]), np.corrcoef(b1, b2)[0, 1]))
    for se_x in (se, 2 * se, 3 * se):
        print("     SE %.2f: P(95%% interval inside +-3) for true diff 0/1/2/2.5/3 = %s" % (se_x, " ".join("%.3f" % (Phi((3 - 1.96 * se_x - t) / se_x) - Phi((-3 + 1.96 * se_x - t) / se_x)) for t in (0, 1, 2, 2.5, 3))))
    r_ = [np.corrcoef(c(a, "ttc_net"), c(a, "ttc_half"))[0, 1] for a in V + [opp]]
    print("     per-run corr net vs half: %.4f-%.4f; ratio of sums half/net %.4f-%.4f" % (min(r_), max(r_), min(c(a, "ttc_half").sum() / c(a, "ttc_net").sum() for a in V + [opp]), max(c(a, "ttc_half").sum() / c(a, "ttc_net").sum() for a in V + [opp])))
print("\n[5] 0 of n bounds")
for m in (20, 40): print("  0 of %d: 95 %% upper bound %.4f" % (m, 1 - 0.05 ** (1 / m)))
for w in (0.80, 0.85):
    # stratified 20 + 20, 0 found in both: max of w*p1+(1-w)*p2 subject to (1-p1)^20 (1-p2)^20 >= 0.05
    best = max(w * p1 + (1 - w) * (1 - (0.05 / (1 - p1) ** 20) ** (1 / 20)) for p1 in np.linspace(0, 1 - 0.05 ** (1 / 20), 2001))
    print("  stratified 20 merge-area + 20 elsewhere, merge share %.2f: 95 %% bound on the overall non-event share %.4f" % (w, best))
print("\n[6] other measures, edge against the two rules (97.5 % interval)")
for opp in (LR, GR):
    print("  ", opp.split("|")[1], " ".join("%s %+.1f [%+.1f,%+.1f]" % ((k,) + (lambda pb: (pb[0], *np.percentile(pb[1], [1.25, 98.75])))(edge(opp, K(k), small))) for k in ("ttc2", "ttc15", "sev3", "b45")))
print("\n[7] gate: lane-end standing; no-effect behaviour of the cut (random halves of one arm, 240 vs 240)")
r2 = np.random.default_rng(7)
for a in ("E30|nc", LR, GR, "E30|w1u500"):
    for k in ("es", "es2"):
        s = c(a, k); cuts = []
        for _ in range(4000):
            p = r2.permutation(n); cuts.append(1 - np.median(s[p[240:]]) / np.median(s[p[:240]]))
        print("  %-20s %-3s median %6.1f  null cut 2.5/97.5 pct %+.3f %+.3f" % (a.split("|")[1], k, np.median(s), *np.percentile(cuts, [2.5, 97.5])))
print("  v3w learners es medians %s es2 %s" % ([float(np.median(c(a, "es"))) for a in V], [float(np.median(c(a, "es2"))) for a in V]))
print("\n[8] replication line: P(both 97.5 % lower bounds > 0) on 480 fresh seeds, normal approx, if the true edges equal the stored ones, or the stored lower bound")
p1, b1 = edge(LR, K("ttc_net")); p2, b2 = edge(GR, K("ttc_net"))
for t in (p1, np.percentile(b1, 1.25), 5.0, 3.0, 0.0):
    print("  true edge vs lr400_16_1 %+.2f: P(lower>0) %.3f" % (t, Phi(t / b1.std() - 2.2414)))
