"""EXPLORATORY: my own recomputation from the stored S6 rows (240 seeds, already read for a verdict). No simulation."""
import numpy as np
Z = np.load("f_scalars.npz")
KEYS = [str(k) for k in Z["keys"]]; N0 = len(Z["seeds"])
LEARN = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
col = lambda cell, arm, key: Z[f"{cell}|{arm}"][:, KEYS.index(key)]
r = np.random.default_rng(20261130)
IDX = r.integers(0, N0, (20000, N0))
def eff(p, o, lo, hi):
    d = -(p - o) / np.median(o) * 100
    b = np.median(d[IDX], axis=1)
    return np.median(d), np.percentile(b, lo), np.percentile(b, hi)
def offs(L, O):
    P = L.mean(0)
    def f(s):
        den = np.median(O)
        pe = -np.median(P[s] - O[s]) / den * 100
        le = np.mean([-np.median(L[i][s] - O[s]) / den * 100 for i in range(5)])
        return pe, le
    pe, le = f(np.arange(N0))
    bs = np.array([f(IDX[k]) for k in range(4000)])
    d = bs[:, 0] - bs[:, 1]
    return pe, le, pe - le, np.percentile(d, 2.5), np.percentile(d, 97.5), np.percentile(bs[:, 1], 1.25), np.percentile(bs[:, 1], 98.75)
print("A. pooled effects, 97.5 % (record: cf vs 3E-C +11.80 [+4.97, +19.71]; delay vs os0_10_10 -0.58 [-0.93, +0.20])")
for cell in ("TRUCK",):
    L = {k: np.array([col(cell, l, k) for l in LEARN]) for k in ("ttc_net", "all_delay", "fuel_km")}
    print("  cf vs 3E-C_TRUCK %+.2f [%+.2f, %+.2f]" % eff(L["ttc_net"].mean(0), col(cell, "3E-C_TRUCK", "ttc_net"), 1.25, 98.75))
    print("  delay vs os0_10_10 %+.2f [%+.2f, %+.2f]" % eff(L["all_delay"].mean(0), col(cell, "os0_10_10", "all_delay"), 1.25, 98.75))
print("B. pooled-arm offset = pooled effect minus mean of the 5 single-learner effects; 95 % interval of the offset; then the 97.5 % interval of the single-learner mean")
for key, opps in (("ttc_net", ["3E-C_TRUCK", "p333", "os0_10_10"]), ("all_delay", ["os0_10_10", "p333", "lr1000_10_1", "grid_os1_10_10", "os1_15_10", "3E-D_TRUCK", "lr1000_16_2", "grid_lr400_13_1", "lr400_13_2", "3E-C_TRUCK"])):
    L = np.array([col("TRUCK", l, key) for l in LEARN])
    for o in opps:
        print("  %-9s vs %-16s pooled %+.2f | learner mean %+.2f | offset %+.2f [%+.2f, %+.2f] | learner-mean 97.5 %% interval [%+.2f, %+.2f]" % ((key, o) + offs(L, col("TRUCK", o, key))))
print("C. fuel per km, pooled arm, 95 % (correction 5: TRUCK p333 +0.2 [+0.0, +0.3]; S -0.0 [-0.1, +0.1]; 3E-C +0.1 [-0.1, +0.2] and -0.1 [-0.3, +0.1]; nc +0.6 and +1.1)")
for cell in ("TRUCK", "S"):
    P = np.mean([col(cell, l, "fuel_km") for l in LEARN], axis=0)
    for o in ("p333", "3E-C_TRUCK", "nc", "os0_10_10", "3E-D_TRUCK"):
        print("  %-5s vs %-11s %+.2f [%+.2f, %+.2f]" % ((cell, o) + eff(P, col(cell, o, "fuel_km"), 2.5, 97.5)))
print("D. paired SD of the pooled cf difference against 3E-C, % of its median (critic: 37.8); delay against os0_10_10 (critic: 5.3 in TRUCK)")
Pc = np.mean([col("TRUCK", l, "ttc_net") for l in LEARN], axis=0); Oc = col("TRUCK", "3E-C_TRUCK", "ttc_net")
Pd = np.mean([col("TRUCK", l, "all_delay") for l in LEARN], axis=0); Od = col("TRUCK", "os0_10_10", "all_delay")
print("  cf SD %.1f %% ; delay SD vs os0_10_10 %.1f %% ; vs p333 %.1f %%" % (np.std(Pc - Oc, ddof=1) / np.median(Oc) * 100, np.std(Pd - Od, ddof=1) / np.median(Od) * 100, np.std(Pd - col("TRUCK", "p333", "all_delay"), ddof=1) / np.median(col("TRUCK", "p333", "all_delay")) * 100))
print("  medians: 3E-C cf %.0f, v3w pooled cf %.0f; 10 %% of 3E-C median = %.0f s; stored median paired reduction %.0f s" % (np.median(Oc), np.median(Pc), 0.1 * np.median(Oc), np.median(Oc - Pc)))
