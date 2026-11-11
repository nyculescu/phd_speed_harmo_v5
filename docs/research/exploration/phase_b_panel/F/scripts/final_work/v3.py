"""EXPLORATORY: operating characteristics of screen F's K1-K3 at 480 verdict seeds, resampled from the 240 stored S6 TRUCK seeds
(already read for a verdict). Two statistic forms: P = pooled arm (planb.md:424), L = mean of the five single-learner effects.
v3w is shifted by a constant so the stored-sample statistic equals the stated truth. No simulation."""
import sys
import numpy as np
Z = np.load("f_scalars.npz")
KEYS = [str(k) for k in Z["keys"]]; N0 = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda arm, key: Z[f"TRUCK|{arm}"][:, KEYS.index(key)]
TIED = ["os0_10_10", "p333", "lr1000_10_1", "grid_os1_10_10", "os1_15_10", "3E-D_TRUCK", "lr1000_16_2", "grid_lr400_13_1", "lr400_13_2"]
ARMS = ["3E-C_TRUCK"] + TIED     # 10 rule arms
N, B, ST = 480, 1000, int(sys.argv[1]) if len(sys.argv) > 1 else 1500
Lc = np.array([col(l, "ttc_net") for l in LEARN]); Ld = np.array([col(l, "all_delay") for l in LEARN])
Sc = np.vstack([Lc.mean(0)[None], Lc]); Sd = np.vstack([Ld.mean(0)[None], Ld])     # row 0 = pooled arm, rows 1-5 = learners
Oc = {o: col(o, "ttc_net") for o in ARMS}; Od = {o: col(o, "all_delay") for o in ARMS}
def stats(S, O, s, bi):
    """point and 97.5 % lower bound for the pooled form and for the single-learner mean; per-learner points. In % of the rule's median."""
    m = np.median(O[s])
    d = -(S[:, s] - O[s][None]) / m * 100.0     # (6, N)
    pts = np.median(d, axis=1)
    bs = np.median(d[:, bi], axis=2)     # (6, B)
    lm = bs[1:].mean(0)
    return m, pts[0], np.percentile(bs[0], 1.25), pts[1:].mean(), np.percentile(lm, 1.25), pts[1:]
base = {}
for o in ARMS:
    a = np.arange(N0)[None].repeat(2, 0)
    mc, pc, _, lc, _, _ = stats(Sc, Oc[o], np.arange(N0), a); md, pd_, _, ld, _, lpd = stats(Sd, Od[o], np.arange(N0), a)
    base[o] = dict(mc=mc, pc=pc, lc=lc, md=md, pd=pd_, ld=ld)
r = np.random.default_rng(20261131)
R = {o: [] for o in ARMS}
for k in range(ST):
    s = r.integers(0, N0, N); bi = r.integers(0, N, (B, N))
    for o in ARMS:
        R[o].append((stats(Sc, Oc[o], s, bi), stats(Sd, Od[o], s, bi)))
def arr(o, which, j):
    return np.array([x[which][j] for x in R[o]])
print(f"n = {N}, {ST} studies, B = {B}. Stored-sample statistics (240 seeds):")
for o in ARMS:
    b = base[o]
    print("  %-16s cf pooled %+.2f, learner mean %+.2f | delay pooled %+.2f, learner mean %+.2f" % (o, b["pc"], b["lc"], b["pd"], b["ld"]))
# K1 against the closest rule on close-following (3E-C as the proxy): KILL if point < 10 or lower bound <= 0
o = "3E-C_TRUCK"; b = base[o]
mc = arr(o, 0, 0)
print("\nK1 against 3E-C (proxy for every 3E-C arm): P(KILL)")
print("true edge | pooled statistic, truth pooled | pooled statistic, truth = learner mean | learner-mean statistic, truth = learner mean | planb.md:438 form (lb > 0 and >= 20 s), pooled")
K1ok = {}
for e in (0, 5, 8, 10, 11, 12, 13, 15, 20):
    shP = (b["pc"] - e) * b["mc"] / mc     # shift in % of the resampled median
    shL = (b["lc"] - e) * b["mc"] / mc
    okPP = (arr(o, 0, 1) - shP >= 10) & (arr(o, 0, 2) - shP > 0)
    okPL = (arr(o, 0, 1) - shL >= 10) & (arr(o, 0, 2) - shL > 0)
    okLL = (arr(o, 0, 3) - shL >= 10) & (arr(o, 0, 4) - shL > 0)
    alt = (arr(o, 0, 2) - shP > 0) & ((arr(o, 0, 1) - shP) / 100.0 * mc >= 20)
    K1ok[e] = (okPP, okPL, okLL)
    print("%5.1f | %.3f | %.3f | %.3f | %.3f" % (e, 1 - okPP.mean(), 1 - okPL.mean(), 1 - okLL.mean(), 1 - alt.mean()))
# K2: delay non-inferiority against every rule arm
def k2(form, truth, margin, arms):
    ok = np.ones(ST, bool)
    for o in arms:
        b = base[o]; md = arr(o, 1, 0)
        lb = arr(o, 1, 2 if form == "P" else 4)
        if truth == "stored":
            sh = 0.0
        else:
            kind, x = truth
            ref = b["pd"] if kind == "pooled" else b["ld"]
            sh = (ref + x) * b["md"] / md     # after the shift the stored-sample statistic (pooled or learner mean) equals -x
        ok &= (lb - sh) > -margin
    return ok
TR = [("stored", "stored differences"), (("learner", 0.0), "every learner ties every arm"), (("learner", 0.5), "every learner 0.5 % worse"),
      (("learner", 1.0), "every learner 1.0 % worse"), (("pooled", 0.0), "pooled arm ties every arm"), (("pooled", 1.0), "pooled arm 1.0 % worse"), (("learner", 2.0), "every learner 2.0 % worse")]
for arms, name in ((TIED + ["3E-C_TRUCK"], "10 rule arms"), (["os0_10_10", "p333", "3E-D_TRUCK", "3E-C_TRUCK"], "4 rule arms (the earlier text)")):
    print(f"\nK2 P(pass), {name}: truth | pooled, margin 1 % | pooled, margin 2 % | learner mean, margin 1 % | learner mean, margin 2 %")
    for t, lab in TR:
        print("  %-30s | %.3f | %.3f | %.3f | %.3f" % (lab, k2("P", t, 1, arms).mean(), k2("P", t, 2, arms).mean(), k2("L", t, 1, arms).mean(), k2("L", t, 2, arms).mean()))
# K3: at least 4 of 5 learners with, against every rule arm, cf point > 0 and delay point > -1
def k3(shift_d=0.0, edge=None):
    good = np.ones((ST, 5), bool)
    for o in ARMS:
        b = base[o]
        cp = np.array([x[0][5] for x in R[o]]); dp = np.array([x[1][5] for x in R[o]])
        if edge is not None and o == "3E-C_TRUCK":
            cp = cp - ((b["pc"] - edge) * b["mc"] / arr(o, 0, 0))[:, None]
        dp = dp - (shift_d * b["md"] / arr(o, 1, 0))[:, None]
        good &= (cp > 0) & (dp > -1.0)
    return good.sum(1) >= 4
print("\nK3 P(fires): stored %.3f | every learner 0.5 %% worse on delay %.3f | 1.0 %% worse %.3f | true pooled edge 0 against 3E-C %.3f" % (1 - k3().mean(), 1 - k3(0.5).mean(), 1 - k3(1.0).mean(), 1 - k3(0.0, 0.0).mean()))
print("\nAll of K1-K3 pass, delay at the stored differences, 10 rule arms: true pooled edge | pooled statistic | learner-mean statistic (truth = learner mean)")
k2P, k2L = k2("P", "stored", 1, ARMS), k2("L", "stored", 1, ARMS)
for e in (0, 5, 8, 10, 12, 15, 20):
    k = k3(0.0, float(e))
    print("%5.1f | %.3f | %.3f" % (e, (K1ok[e][0] & k2P & k).mean(), (K1ok[e][2] & k2L & k).mean()))
