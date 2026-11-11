"""(D vii) statistic sensitivity in S and TRUCK: pooled-arm median, stacked single-learner median, mean of paired differences. EXPLORATORY.
X minus p333 in % of p333's median (flow-type: p333 minus X); positive = p333 better."""
import pickle, numpy as np
from meas import *
T = pickle.load(open("s6.pkl", "rb"))
seeds = list(range(7480400, 7480640))
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
f = lambda e, p=2: f"{e[0]:+.{p}f} [{e[1]:+.{p}f}, {e[2]:+.{p}f}]"
KS = ["all_delay", "TTT", "innet", "own_mean", "per_passed", "main_roads", "merge_roads", "r3", "r4a", "h1", "h2", "first5_m", "last5_m", "passed", "passed_h1", "passed_h2", "passed_last5", "arrived", "unfinished", "endstop2"]
for cell in ("S", "TRUCK"):
    M = table(T, cell, ["p333", "os0_10_10", "3E-C_TRUCK", "3E-D_TRUCK", "nc", "lr1000_10_1"], LEARN, seeds)
    print(f"\n##### {cell}: v3w against p333: pooled-arm median | stacked single-learner median | mean of paired (pooled arm) | learners with CI above 0 / below 0")
    for k in KS:
        ref = np.median(M["p333"][k]); sg = 1.0 if k in LOW else -1.0
        d = sg * (M["v3w"][k] - M["p333"][k]) / ref * 100
        D = np.array([sg * (M[l][k] - M["p333"][k]) / ref * 100 for l in LEARN])
        es = [boot(x) for x in D]
        print(f"{k:13s} | {f(boot(d))} | {f(boot_stack(D))} | {f(boot_mean(d))} | {sum(e[1] > 0 for e in es)} / {sum(e[2] < 0 for e in es)}")
    print(f"\n##### {cell}: single-run opponents against p333: median of paired | mean of paired | share of seeds with identical all_delay")
    for a in ("os0_10_10", "3E-C_TRUCK", "3E-D_TRUCK", "lr1000_10_1", "nc"):
        print(f"-- {a}: identical in {np.mean(M[a]['all_delay'] == M['p333']['all_delay']):.2f} of seeds")
        for k in ("all_delay", "TTT", "own_mean", "passed", "r4a", "unfinished"):
            ref = np.median(M["p333"][k]); sg = 1.0 if k in LOW else -1.0
            d = sg * (M[a][k] - M["p333"][k]) / ref * 100
            print(f"   {k:11s} | {f(boot(d))} | {f(boot_mean(d))}")
    # distribution shape of p333 all_delay and of single-learner runs
    x = M["p333"]["all_delay"]
    sk = lambda x: float(((x - x.mean()) ** 3).mean() / x.std() ** 3)
    print(f"\n{cell}: p333 all_delay: median {np.median(x):.0f}, mean {x.mean():.0f}, p10 {np.percentile(x, 10):.0f}, p90 {np.percentile(x, 90):.0f}, max {x.max():.0f}, skew {sk(x):+.2f}; single learners skew " + ", ".join(f"{sk(M[l]['all_delay']):+.2f}" for l in LEARN) + f"; pooled arm skew {sk(M['v3w']['all_delay']):+.2f}")
    sdl = np.std([M[l]["all_delay"] for l in LEARN], axis=0, ddof=1)
    print(f"{cell}: SD across the 5 learners within a seed: median {np.median(sdl):.0f} veh-s ({100 * np.median(sdl) / np.median(x):.1f} % of p333's median); SD of p333 across seeds {x.std(ddof=1):.0f}")
    # null check: one learner against the per-seed mean of the other four (same policy family, should be 0)
    out = []
    for i, l in enumerate(LEARN):
        others = np.mean([M[m]["all_delay"] for m in LEARN if m != l], axis=0)
        out.append(boot((others - M[l]["all_delay"]) / np.median(M[l]["all_delay"]) * 100))
    print(f"{cell}: NULL of the pooled-arm statistic: (mean of the other 4 learners) minus (one learner), % of that learner's median; positive = the single run looks better: " + " | ".join(f(e) for e in out) + f" | mean {np.mean([e[0] for e in out]):+.2f}")
