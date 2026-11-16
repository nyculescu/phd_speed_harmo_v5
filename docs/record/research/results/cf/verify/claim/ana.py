"""Zone, throughput and per-learner edges with the C-D5 statistic on the extracted CF rows."""
import numpy as np
z = np.load("arr.npz")
V = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
c = lambda a, k: z[f"{a}__{k}"]
n = len(z["seeds"])
idx = np.random.default_rng(20261108).integers(0, n, (20000, n))
P975 = (1.25, 98.75)
def edge(opp, k, learners=V, sign=-1.0):
    O = c(opp, k); m = np.median(O)
    D = [sign * (c(w, k) - O) / m * 100 for w in learners]
    pt = np.mean([np.median(d) for d in D])
    b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
    lo, hi = np.percentile(b, P975)
    return pt, lo, hi
f = lambda t: "%+.2f [%+.2f, %+.2f]" % t
print("check lr400_16_1 E", f(edge("lr400_16_1", "ttc_net")), "reader +9.93 [+6.16, +14.97]")
print("check p333 D", f(edge("p333", "all_delay")), "reader -0.31 [-1.07, +0.52]")
print("check lr400_16_1 away", f(edge("lr400_16_1", "ttc_away")), "reader -8.62 [-14.73, -1.41]")
opps = ["lr400_16_1", "grid_lr400_13_1", "os0_10_10", "p333", "3ex2", "MPC-F", "3E-C_TRUCK", "lr1000_10_1", "nc"]
print("\nedge, positive = v3w less (passed: positive = v3w more served)")
print("opp | ttc_net | away | merge2 | merge1 | junction | passed | TTT(N) | delay")
for o in opps:
    row = [f(edge(o, k)) for k in ("ttc_net", "ttc_away", "ttc_m2", "ttc_m1", "ttc_jn")] + [f(edge(o, "passed", sign=1.0)), f(edge(o, "N")), f(edge(o, "all_delay"))]
    print(o, "|", " | ".join(row))
print("\nzone shares of road TTC<3 count (median over seeds of per-seed share); v3w = learner mean")
for a in ["v3w"] + opps:
    names = V if a == "v3w" else (a,)
    tot = np.mean([c(w, "ttc_road_sum") for w in names], axis=0)
    sh = {g: np.median(np.mean([c(w, "ttc_" + g) for w in names], axis=0) / np.maximum(tot, 1)) for g in ("m2", "m1", "away", "jn")}
    med = {g: np.median(np.mean([c(w, "ttc_" + g) for w in names], axis=0)) for g in ("m2", "m1", "away", "jn")}
    print(a, {g: round(float(v), 3) for g, v in sh.items()}, "medians", {g: round(float(v), 1) for g, v in med.items()},
          "road_sum/ttc_net", round(float(np.median(tot / np.mean([c(w, 'ttc_net') for w in names], axis=0))), 3))
print("\nper learner alone vs lr400_16_1 / grid_lr400_13_1 / os0_10_10 on ttc_net and away")
for o in ["lr400_16_1", "grid_lr400_13_1", "os0_10_10"]:
    for k in ("ttc_net", "ttc_away", "ttc_m2"):
        print(o, k, [(w, f(edge(o, k, (w,)))) for w in V])
print("\nlr400_16_1 as the subject vs p333 (positive = lr400_16_1 less):")
for k in ("ttc_net", "ttc_away", "ttc_m2", "all_delay", "b45_step"):
    O = c("p333", k); d = -(c("lr400_16_1", k) - O) / np.median(O) * 100
    b = np.median(d[idx], axis=1); print(k, "%+.2f [%+.2f, %+.2f]" % (np.median(d), *np.percentile(b, P975)))
print("\nmedians served passed:", {a: float(np.median(np.mean([c(w, 'passed') for w in (V if a == 'v3w' else (a,))], axis=0))) for a in ["v3w"] + opps})
