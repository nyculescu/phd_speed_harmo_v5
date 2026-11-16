"""(C) X1 and X2: v3w against p333, os0_10_10, 3E-X, no control under alternative definitions. EXPLORATORY.
Entry = median over seeds of (X - v3w) as % of X's median of that measure (flow-type: v3w - X). Positive = v3w better.
95 % percentile bootstrap, 10,000 resamples, RNG 20261110. v3w = per-seed mean of 5 learners ("pooled"); "stack" = median over the 5 x n single-learner differences, seeds resampled together."""
import pickle, numpy as np
from meas import *
R2T, S01, R2V, R1 = (pickle.load(open(f, "rb")) for f in ("r2t.pkl", "s01.pkl", "r2v.pkl", "r1.pkl"))
f = lambda e, p=2: f"{e[0]:+.{p}f} [{e[1]:+.{p}f}, {e[2]:+.{p}f}]"
L2T = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]; L2V = ["w0u250", "w1u250", "w2u500", "w3u500", "w4u500"]; L1 = ["w0", "w1", "w2", "w3", "w4"]
PCT = ["all_delay", "delay_s", "TTT", "innet", "per_passed", "per_arrived", "own_mean", "own_p95", "own_ramp", "own_ramp2", "minus_endstop", "passed", "arrived", "passed_h1", "passed_h2", "passed_last5", "dist_km"]
PCT_M = ["caralks", "truck25", "class_ref", "h1", "h2", "first5_m", "last5_m", "m1only", "m2only"]
ABS = ["pend_total", "unfinished_pp", "endstop", "endstop2", "collisions", "teleports", "full_moving", "finished_pct"]
ABS_M = ["pend_ramps_min"]
# identity of the S0/S1 re-run and the round 2 test rows
mx = 0.0
for k, d in R2T.items():
    for s, r in d.items():
        mx = max(mx, abs(r["all_delay"] - S01[k][s]["all_delay"]), abs(r["N"] - S01[k][s]["N"]))
print("max |all_delay or N difference| between round2/test rows and measure_s01 rows_test, same arm and seed:", mx)
def run(tag, sets, pct, absk):
    for cell, ex in (("X1", "3ex1"), ("X2", "3ex2")):
        opp = ["p333", "os0_10_10", ex, "nc"]
        Ms = []
        for T, L in sets:
            seeds = sorted(T[(cell, "p333")])
            arms = [a for a in opp if (cell, a) in T]
            Ms.append((table(T, cell, arms, L, seeds), L))
        opp = [a for a in opp if all(a in M for M, _ in Ms)]
        cat = lambda a, k: np.concatenate([M[a][k] for M, _ in Ms])
        catL = lambda i, k: np.concatenate([M[L[i]][k] for M, L in Ms])
        n = len(cat("p333", "all_delay"))
        print(f"\n##### {tag} {cell} n={n}: medians: " + " | ".join(f"{k}: " + ", ".join(f"{a} {np.median(cat(a, k)):.1f}" for a in ["v3w"] + opp) for k in ("all_delay", "TTT", "innet", "pend_total", "passed", "arrived", "own_mean", "finished_pct", "endstop2")))
        print("measure | " + " | ".join(f"{a}: pooled / stack / mean-of-paired" for a in opp))
        for k in pct:
            sg = 1.0 if k in LOW else -1.0
            out = []
            for a in opp:
                ref = np.median(cat(a, k))
                d = sg * (cat(a, k) - cat("v3w", k)) / ref * 100
                D = np.array([sg * (cat(a, k) - catL(i, k)) / ref * 100 for i in range(5)])
                out.append(f"{f(boot(d))} / {f(boot_stack(D))} / {f(boot_mean(d))}")
            print(f"{k:14s} | " + " | ".join(out))
        print("absolute, X minus v3w (median of paired differences; pooled / stack)")
        for k in absk:
            out = []
            for a in opp:
                d = cat(a, k) - cat("v3w", k); D = np.array([cat(a, k) - catL(i, k) for i in range(5)])
                out.append(f"{f(boot(d), 1)} / {f(boot_stack(D), 1)}")
            print(f"{k:14s} | " + " | ".join(out))
        print("per learner all_delay, X=p333 (% of p333 median, positive = v3w better): " + " | ".join(f(boot((cat("p333", "all_delay") - catL(i, "all_delay")) / np.median(cat("p333", "all_delay")) * 100)) for i in range(5)))
        for a in opp:
            dA = cat(a, "all_delay") - cat("v3w", "all_delay"); dN = cat(a, "TTT") - cat("v3w", "TTT"); dD = (cat(a, "dist_km") - cat("v3w", "dist_km")) * 1000 / REF
            dP = cat(a, "passed") - cat("v3w", "passed"); dU = cat(a, "unfinished_pp") - cat("v3w", "unfinished_pp")
            rk = lambda x: np.argsort(np.argsort(x))
            print(f"  {a:10s} X - v3w: d all_delay {f(boot(dA), 0)} mean {dA.mean():+.0f} | d TTT {f(boot(dN), 0)} mean {dN.mean():+.0f} | d dist/REF {f(boot(dD), 0)} | d passed {f(boot(dP), 1)} | d unfinished pp {f(boot(dU), 2)} | sign agree delay-passed {np.mean(dA * dP < 0):.2f} | Spearman(dA, dU) {np.corrcoef(rk(dA), rk(dU))[0, 1]:+.2f}")
run("round 2 test (40 seeds)", [(R2T, L2T)], PCT, ABS)
run("round 2 test with pack (S0/S1 re-run, 40 seeds)", [(S01, L2T)], PCT_M, ABS_M)
run("three sets pooled (120 seeds)", [(R1, L1), (R2V, L2V), (R2T, L2T)], PCT, ABS)
