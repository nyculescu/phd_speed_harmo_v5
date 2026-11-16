"""(C) S and TRUCK: p333 against v3w, os0_10_10, 3E-C_TRUCK, no control under alternative definitions. EXPLORATORY.
Entry = median over seeds of (X - p333) as % of p333's median of that measure; for flow-type measures (p333 - X). Positive = p333 better.
95 % percentile bootstrap, 10,000 resamples, RNG 20261110."""
import pickle, numpy as np
from meas import *
T = pickle.load(open("s6.pkl", "rb"))
seeds = list(range(7480400, 7480640))
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
OPP = ["v3w", "os0_10_10", "3E-C_TRUCK", "3E-D_TRUCK", "nc"]
PCT = ["all_delay", "delay_s", "TTT", "innet", "per_passed", "per_arrived", "main_roads", "merge_roads", "r1", "r2", "r3a", "r3", "r4a", "r4", "r5", "caralks", "truck25", "class_ref", "own_mean", "own_p95", "own_ramp", "own_ramp2", "own_total",
       "h1", "h2", "first5_m", "last5_m", "minus_endstop", "passed", "arrived", "passed_h1", "passed_h2", "passed_last5", "dist_km", "truck_km"]
ABS = ["pend_total", "pend_main", "pend_ramps", "ramp_all", "junction", "unfinished", "pending_end", "in_net_end", "endstop", "endstop2", "truck_offset", "collisions", "teleports", "stuck", "dropped", "full_moving", "finished_pct"]
f = lambda e, p=2: f"{e[0]:+.{p}f} [{e[1]:+.{p}f}, {e[2]:+.{p}f}]"
for cell in ("S", "TRUCK"):
    M = table(T, cell, ["p333", "os0_10_10", "3E-C_TRUCK", "3E-D_TRUCK", "nc"], LEARN, seeds)
    print(f"\n##### {cell}: medians per arm")
    for k in PCT + ABS:
        print(f"{k:14s} " + " | ".join(f"{a} {np.median(M[a][k]):.1f} (mean {np.mean(M[a][k]):.1f})" for a in ["p333"] + OPP))
    print(f"\n##### {cell}: X against p333, % of p333's median, positive = p333 better")
    print("measure | " + " | ".join(OPP))
    for k in PCT:
        ref = np.median(M["p333"][k]); sg = 1.0 if k in LOW else -1.0
        print(f"{k:14s} | " + " | ".join(f(boot(sg * (M[a][k] - M["p333"][k]) / ref * 100)) for a in OPP))
    print(f"\n##### {cell}: X minus p333, absolute units (median of paired differences)")
    for k in ABS:
        print(f"{k:14s} | " + " | ".join(f(boot(M[a][k] - M["p333"][k]), 1) for a in OPP))
    print(f"\n##### {cell}: per learner, X minus p333 on all_delay, TTT, own_mean (% of p333 median; positive = p333 better)")
    for k in ("all_delay", "TTT", "own_mean", "per_passed"):
        ref = np.median(M["p333"][k])
        es = [boot((M[l][k] - M["p333"][k]) / ref * 100) for l in LEARN]
        print(f"{k:12s} | " + " | ".join(f(e) for e in es) + f" | mean of the five medians {np.mean([e[0] for e in es]):+.2f} | pooled {f(boot((M['v3w'][k] - M['p333'][k]) / ref * 100))}")
        # mean-based statistic for the pooled arm
        d = (M["v3w"][k] - M["p333"][k]) / ref * 100
        print(f"             mean of paired differences, pooled arm: {d.mean():+.2f}; skew of single-learner paired diff: " + ", ".join(f"{((x - x.mean())**3).mean() / x.std()**3:+.2f}" for x in [(M[l][k] - M['p333'][k]) for l in LEARN]))
    # decomposition of the all_delay difference: d(all_delay) = d(N) - d(dist)/REF
    print(f"\n##### {cell}: all_delay difference = TTT difference - distance difference / REF (veh-s, medians and means of paired X - p333)")
    for a in OPP:
        dN = M[a]["TTT"] - M["p333"]["TTT"]; dD = (M[a]["dist_km"] - M["p333"]["dist_km"]) * 1000.0 / REF; dA = M[a]["all_delay"] - M["p333"]["all_delay"]
        print(f"{a:12s} d all_delay {f(boot(dA), 0)} mean {dA.mean():+.0f} | d TTT {f(boot(dN), 0)} mean {dN.mean():+.0f} | d dist/REF {f(boot(dD), 0)} mean {dD.mean():+.0f}")
    # served more and delayed less?
    print(f"\n##### {cell}: agreement of signs across seeds (X - p333): share of seeds where the arm with less all_delay also passed more / arrived more")
    for a in OPP:
        dA = M[a]["all_delay"] - M["p333"]["all_delay"]; dP = M[a]["passed"] - M["p333"]["passed"]; dR = M[a]["arrived"] - M["p333"]["arrived"]
        print(f"{a:12s} passed: agree {np.mean((dA * dP) < 0):.2f} tie {np.mean(dP == 0):.2f}; arrived: agree {np.mean((dA * dR) < 0):.2f} tie {np.mean(dR == 0):.2f}; Spearman(dA, dP) {np.corrcoef(np.argsort(np.argsort(dA)), np.argsort(np.argsort(dP)))[0, 1]:+.2f}; Spearman(dA, d unfinished) {np.corrcoef(np.argsort(np.argsort(dA)), np.argsort(np.argsort(M[a]['unfinished'] - M['p333']['unfinished'])))[0, 1]:+.2f}")
