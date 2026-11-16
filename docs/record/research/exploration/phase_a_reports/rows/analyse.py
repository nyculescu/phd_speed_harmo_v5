"""EXPLORATORY analysis of the stored Plan B S6 rows (already read for the verdict). Paired seeds, median of paired differences,
95 % percentile bootstrap, 10,000 resamples, rng 20261110. No simulation."""
import json, sys
import numpy as np
Z = np.load("s6_scalars.npz")
KEYS = list(Z["keys"]); seeds = Z["seeds"]; n = len(seeds)
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
OPP = ["3E-C_TRUCK", "3E-D_TRUCK", "3e", "3ex1", "3ex2", "MPC-F", "a4400_10_1", "copy", "grid_a41000_10_2", "grid_lr400_13_1", "grid_os1_10_10", "grid_r4a2", "grid_z31333", "lr1000_10_1", "lr1000_16_2", "lr400_13_2", "lr400_16_1", "os0_10_10", "os1_10_0", "os1_15_10", "p333", "r4a1", "z33133"]
B = 10_000
IDX = np.random.default_rng(20261110).integers(0, n, (B, n))
def col(cell, arm, key): return Z[f"{cell}|{arm}"][:, KEYS.index(key)]
def pooled(cell, key): return np.mean([col(cell, l, key) for l in LEARN], axis=0)
def eff(P, O, sign=-1):
    d = sign * (P - O) / np.median(O) * 100.0
    b = np.median(d[IDX], axis=1)
    lo, hi = np.percentile(b, (2.5, 97.5))
    return float(np.median(d)), float(lo), float(hi)
def meddiff(d):
    b = np.median(d[IDX], axis=1); lo, hi = np.percentile(b, (2.5, 97.5))
    return float(np.median(d)), float(lo), float(hi)
f = lambda t: "%+.2f [%+.2f, %+.2f]" % tuple(t)
out = {}
for cell in ("TRUCK", "S"):
    print(f"\n##### {cell}  n paired seeds = {n}")
    P = {k: pooled(cell, k) for k in ("all_delay", "ttc_net", "passed")}
    O = {o: {k: col(cell, o, k) for k in ("all_delay", "ttc_net", "passed", "m_planned_window", "delay")} for o in OPP + ["nc"]}
    # check the normaliser is the same in every arm
    pw = np.array([col(cell, a, "m_planned_window") for a in OPP + ["nc"] + LEARN])
    print("planned_window identical across arms:", bool((pw == pw[0]).all()), "median", np.median(pw[0]), "min", pw.min(), "max", pw.max())
    # (1) table, positive = v3w better
    print("\n(1) v3w against each opponent, % of the opponent's median, positive = v3w better; 95 % CI")
    print("opp | med delay veh-s | pooled delay | pooled flow | pooled cf | per-learner delay points | learners delay CI>0 / CI<0 | learners cf CI>0")
    tab = {}
    for o in sorted(OPP, key=lambda o: np.median(O[o]["all_delay"])):
        d = eff(P["all_delay"], O[o]["all_delay"]); fl = eff(P["passed"], O[o]["passed"], 1); c = eff(P["ttc_net"], O[o]["ttc_net"])
        per = [eff(col(cell, l, "all_delay"), O[o]["all_delay"]) for l in LEARN]
        perc = [eff(col(cell, l, "ttc_net"), O[o]["ttc_net"]) for l in LEARN]
        tab[o] = {"delay": d, "flow": fl, "cf": c, "per_delay": per, "per_cf": perc}
        print(o, "|", "%.0f" % np.median(O[o]["all_delay"]), "|", f(d), "|", f(fl), "|", f(c), "|", " ".join("%+.2f" % p[0] for p in per), "|",
              sum(p[1] > 0 for p in per), "/", sum(p[2] < 0 for p in per), "|", sum(p[1] > 0 for p in perc))
    block = [o for o in OPP if tab[o]["delay"][1] <= 0]
    print("opponents whose 95 % delay CI does not exclude 0 or is below (block the delay claim):", block)
    # (2) headroom
    med = {o: float(np.median(O[o]["all_delay"])) for o in OPP}
    best = min(med, key=med.get)
    bm = min(OPP, key=lambda o: float(np.mean(O[o]["all_delay"])))
    nc = O["nc"]["all_delay"]; bo = O[best]["all_delay"]; pw0 = pw[0]
    print("\n(2) headroom; best single opponent by median:", best, "; by mean:", bm)
    for nm, x in (("nc", nc), (best, bo), ("v3w pooled", P["all_delay"])) + tuple((l, col(cell, l, "all_delay")) for l in LEARN):
        print(f"  {nm}: median all_delay {np.median(x):.0f} veh-s, mean {np.mean(x):.0f}; per planned vehicle median {np.median(x / pw0):.2f} s, mean {np.mean(x / pw0):.2f} s")
    print("  row field 'delay' (mean over finished vehicles, s): nc %.2f, best %.2f" % (np.nanmedian(O["nc"]["delay"]), np.nanmedian(O[best]["delay"])))
    print("  share of nc delay removed by best opponent (median paired (nc-best)/median(nc)):", f(eff(bo, nc)))
    print("  share removed by v3w pooled:", f(eff(P["all_delay"], nc)))
    print("  ratio of medians: best/nc = %.4f, v3w/nc = %.4f" % (np.median(bo) / np.median(nc), np.median(P["all_delay"]) / np.median(nc)))
    print("  served: nc %.1f, best %.1f, v3w %.1f (median passed)" % (np.median(O["nc"]["passed"]), np.median(O[best]["passed"]), np.median(P["passed"])))
    # (3) hindsight oracle over the 23 non-learning opponents
    M = np.array([O[o]["all_delay"] for o in OPP])
    orc = M.min(axis=0)
    print("\n(3) hindsight oracle over 23 opponents vs best single (%s): gain %% of best median, positive = oracle lower:" % best, f(eff(orc, bo)))
    print("  oracle median %.0f veh-s; mean gain %.0f veh-s (%.2f %% of best mean)" % (np.median(orc), np.mean(bo - orc), 100 * np.mean(bo - orc) / np.mean(bo)))
    orc2 = np.minimum(orc, nc); print("  with nc added to the pool:", f(eff(orc2, bo)))
    print("  v3w pooled vs oracle (positive = v3w lower):", f(eff(P["all_delay"], orc)))
    lm = np.array([col(cell, l, "all_delay") for l in LEARN])
    bl = LEARN[int(np.argmin(np.median(lm, axis=1)))]
    print("  noise yardstick: per-seed min over the 5 learners vs best single learner (%s):" % bl, f(eff(lm.min(axis=0), lm[LEARN.index(bl)])))
    top5 = sorted(OPP, key=med.get)[:5]
    T5 = np.array([O[o]["all_delay"] for o in top5])
    print("  oracle over the 5 lowest-median opponents", top5, "vs best single:", f(eff(T5.min(axis=0), bo)))
    # split-half: best single picked on half A, the oracle gain it implies on half B, and a difficulty-conditioned scheduler
    rng = np.random.default_rng(20261111); g_sel, g_sched, g_orc = [], [], []
    ncd = nc; R = 2000
    for _ in range(R):
        perm = rng.permutation(n); A, Bh = perm[: n // 2], perm[n // 2:]
        bA = int(np.argmin(np.median(M[:, A], axis=1)))
        # scheduler: terciles of no-control delay on the same seed (a controller-independent difficulty proxy), best opponent per tercile on A
        q = np.quantile(ncd[A], (1 / 3, 2 / 3)); binA = np.digitize(ncd[A], q); binB = np.digitize(ncd[Bh], q)
        pick = [int(np.argmin(np.median(M[:, A[binA == k]], axis=1))) for k in range(3)]
        sched = np.array([M[pick[b], s] for b, s in zip(binB, Bh)])
        ref = M[bA, Bh]
        g_sched.append(np.median(ref - sched) / np.median(ref) * 100); g_orc.append(np.median(ref - M[:, Bh].min(axis=0)) / np.median(ref) * 100)
        g_sel.append(np.median(M[bA, Bh]) / min(np.median(M[:, Bh], axis=1)) * 100 - 100)
    print("  split-half (2,000 random splits): out-of-sample gain of a 3-bin scheduler on no-control delay vs best single chosen on the other half: mean %+.2f %%, 2.5-97.5 pct [%+.2f, %+.2f]" % (np.mean(g_sched), *np.percentile(g_sched, (2.5, 97.5))))
    print("  same splits, hindsight oracle gain on the held-out half: mean %+.2f %%; winner's curse of best single (its held-out median over the held-out best): mean %+.2f %%" % (np.mean(g_orc), np.mean(g_sel)))
    # permutation check of the oracle: shuffle each opponent's seed-wise deviation from the best single across seeds (breaks any shared per-seed structure, keeps each opponent's marginal difference)
    D = M - bo; gp = []
    for _ in range(500):
        Dp = np.array([rng.permutation(dv) for dv in D]); gp.append(np.median(-(Dp.min(axis=0))) / np.median(bo) * 100)
    print("  permutation check (each opponent's difference to the best shuffled across seeds, 500 draws): oracle gain mean %+.2f %% [%+.2f, %+.2f]; observed %+.2f %%" % (np.mean(gp), *np.percentile(gp, (2.5, 97.5)), np.median(bo - orc) / np.median(bo) * 100))
    # twin-noise null: two rule pairs give the same run on most seeds; where they diverge, the difference is run-to-run chaos, not design
    tw = []
    for a, b in (("p333", "lr1000_10_1"), ("grid_r4a2", "grid_a41000_10_2")):
        da = O[a]["all_delay"] - O[b]["all_delay"]; tw.append(da[da != 0])
        print("  twins %s / %s: delay differs on %d of %d seeds; on those, SD of the difference %.0f veh-s (%.2f %% of best median), median |diff| %.0f" % (a, b, int((da != 0).sum()), n, np.std(da[da != 0], ddof=1), 100 * np.std(da[da != 0], ddof=1) / np.median(bo), np.median(np.abs(da[da != 0]))))
    tw = np.concatenate(tw) / np.sqrt(2.0)     # one run's share of a difference of two
    gn = {}
    for K in (5, 23):
        g = []
        for _ in range(500):
            x = rng.choice(tw, (K, n)); g.append(np.median(x[0] - x.min(axis=0)) / np.median(bo) * 100)
        gn[K] = (np.mean(g), *np.percentile(g, (2.5, 97.5)))
        print("  twin-noise null, K = %d identical controllers with that noise: oracle gain %+.2f %% [%+.2f, %+.2f]" % (K, *gn[K]))
    # (4) per-seed winner counts (ties split)
    win = np.zeros(len(OPP))
    for s in range(n):
        w = np.flatnonzero(M[:, s] == M[:, s].min()); win[w] += 1.0 / len(w)
    order = np.argsort(-win)
    print("\n(4) per-seed lowest-delay opponent, share of %d seeds (ties split):" % n, ", ".join("%s %.1f%%" % (OPP[i], 100 * win[i] / n) for i in order if win[i] > 0))
    print("  best single (%s) is the per-seed best on %.1f %% of seeds; number of distinct winners %d" % (best, 100 * win[OPP.index(best)] / n, int((win > 0).sum())))
    # twin pairs
    for a, b in (("p333", "lr1000_10_1"), ("grid_r4a2", "grid_a41000_10_2")):
        da = O[a]["all_delay"] - O[b]["all_delay"]
        print("  twins %s / %s: identical delay on %d of %d seeds; cf identical on %d" % (a, b, int((da == 0).sum()), n, int((O[a]["ttc_net"] == O[b]["ttc_net"]).sum())))
    # (5) frontier
    print("\n(5) frontier: median all_delay (veh-s) and median close-following (ttc_net) per arm")
    arms = {"v3w": (P["all_delay"], P["ttc_net"]), "nc": (nc, O["nc"]["ttc_net"])} | {o: (O[o]["all_delay"], O[o]["ttc_net"]) for o in OPP} | {l: (col(cell, l, "all_delay"), col(cell, l, "ttc_net")) for l in LEARN}
    pts = {a: (float(np.median(d)), float(np.median(c))) for a, (d, c) in arms.items()}
    for a in sorted(pts, key=lambda a: pts[a][0]): print("  %-18s %9.0f %7.1f" % (a, *pts[a]))
    par = [a for a in pts if a not in LEARN and not any(pts[b][0] <= pts[a][0] and pts[b][1] <= pts[a][1] and pts[b] != pts[a] for b in pts if b not in LEARN and b != a)]
    print("  Pareto set by medians (v3w pooled, 23 opponents, nc):", par)
    dom = [o for o in OPP + ["nc"] if meddiff(O[o]["all_delay"] - P["all_delay"])[2] < 0 and meddiff(O[o]["ttc_net"] - P["ttc_net"])[2] < 0]
    domd = [o for o in OPP + ["nc"] if meddiff(O[o]["all_delay"] - P["all_delay"])[1] > 0 and meddiff(O[o]["ttc_net"] - P["ttc_net"])[1] > 0]
    print("  opponents shown better than v3w on both (paired 95 % CIs):", dom)
    print("  opponents v3w is shown better than on both (paired 95 pct CIs): %d of 24:" % len(domd), domd)
    lowcf = sorted(OPP, key=lambda o: pts[o][1])[:4]
    for o in lowcf: print("  lowest-cf opponents: %s cf diff (o - v3w) %s s per run; delay diff (o - v3w) %s veh-s" % (o, f(meddiff(O[o]["ttc_net"] - P["ttc_net"])), f(meddiff(O[o]["all_delay"] - P["all_delay"]))))
    # (6) variance and power
    print("\n(6) variance of the paired delay difference v3w - best opponent (%s)" % best)
    for nm, x in (("pooled 5-learner mean", P["all_delay"]),) + tuple((l, col(cell, l, "all_delay")) for l in LEARN):
        d = (x - bo) / np.median(bo) * 100.0
        sd = float(np.std(d, ddof=1)); se_mean = sd / np.sqrt(n)
        bmed = np.median(d[IDX], axis=1); se_med = float(np.std(bmed, ddof=1))
        iqr = np.subtract(*np.percentile(d, (75, 25)))
        print("  %-22s SD %.2f %% (%.0f veh-s), IQR %.2f %%, mean %+.2f, median %+.2f; SE(mean) %.3f, bootstrap SE(median) %.3f" % (nm, sd, np.std(x - bo, ddof=1), iqr, d.mean(), np.median(d), se_mean, se_med))
        if nm.startswith("pooled") or nm == LEARN[0]:
            for lab, za in (("95 % two-sided", 1.959964), ("97.5 % two-sided (S6's m = 2 level)", 2.241403)):
                k = za + 0.841621
                print("     %s: MDE at 80 %% power, n = %d: mean-based %.2f %%, median-based %.2f %%" % (lab, n, k * se_mean, k * se_med))
                print("     seeds needed (median-based SE scaled by sqrt(n)):", {g: int(np.ceil((k * se_med * np.sqrt(n) / g) ** 2)) for g in (1, 2, 3, 5)}, "; mean-based:", {g: int(np.ceil((k * sd / g) ** 2)) for g in (1, 2, 3, 5)})
