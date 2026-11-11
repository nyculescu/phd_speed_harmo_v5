"""EXPLORATORY planning, read-only: nulls for Screen M's interval and selection, from stored S6 rows (cell S)."""
import pickle
import numpy as np
T = pickle.load(open("mine.pkl", "rb"))
rng = np.random.default_rng(99173)
seeds = sorted(T["p333"]); n0 = len(seeds)
col = lambda a: np.array([T[a][s]["d"] for s in seeds], float)
P = col("p333"); medP = np.median(P)
B = 1000
for a in ("r4a1", "z33133", "grid_r4a2", "grid_z31333"):
    x = 100 * (P - col(a)) / medP; c = x - np.median(x)
    lo = hi = 0; ST = 4000
    for _ in range(ST):
        y = c[rng.integers(0, n0, 240)] * rng.choice([-1.0, 1.0], 240)
        b = np.median(y[rng.integers(0, 240, (B, 240))], axis=1)
        lo += np.percentile(b, 1.25) > 0; hi += np.percentile(b, 98.75) < 0
    # selection: best of 4 null arms on 60 seeds
    best5 = 0; S2 = 4000; mis = 0
    for _ in range(S2):
        m = [np.median(c[rng.integers(0, n0, 60)]) for _ in range(4)]
        best5 += max(m) >= 5.0
    print("%-12s sign-flip null: lower bound above 0 in %.2f %%, upper bound below 0 in %.2f %% (nominal 1.25 %% each); best of 4 null arms on 60 seeds reads 5 %% or more in %.1f %%" % (a, 100 * lo / ST, 100 * hi / ST, 100 * best5 / S2))
print("T0 null, 10 of 10 seeds by sign: %.2f %%" % (100 * 0.5 ** 10))
# 6,000 report rows at n = 60: half-width of the 97.5 % interval for a normal stand-in with SD 8 and 11
for sd in (8.0, 11.0):
    u = []
    for _ in range(600):
        y = rng.normal(0, sd, 60); b = np.median(y[rng.integers(0, 60, (B, 60))], axis=1)
        u.append((np.percentile(b, 98.75) - np.percentile(b, 1.25)) / 2)
    print("6,000 report rows, n 60, SD %.0f: median half-width %.1f points" % (sd, np.median(u)))
