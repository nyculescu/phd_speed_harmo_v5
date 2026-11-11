"""EXPLORATORY planning proxy: null and power of Screen M's verdict rule from stored S rows (5,300, 240 seeds).
Effect = median(p333 - arm) / median(p333) * 100, positive = arm has less delay. Interval: percentile bootstrap, 97.5 % two-sided."""
import pickle, sys
import numpy as np
D = pickle.load(open(sys.argv[1], "rb"))
iD = list(D["keys"]).index("all_delay")
seeds = list(range(7480400, 7480640))
col = lambda name: np.array([D["s6"][name][s][iD] for s in seeds], float)
P = col("S|p333"); den = np.median(P)
rng = np.random.default_rng(20261110)
TH, STUD, B = 5.0, 2000, 1000
PROX = ("S|r4a1", "S|grid_r4a2", "S|z33133", "S|grid_z31333")
DELTAS = (0.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 9.2)

def studies(c, n, flip=False):
    out = np.empty((STUD, 3))
    for k in range(STUD):
        x = c[rng.integers(0, len(c), n)]
        if flip:
            x = x * rng.choice((-1.0, 1.0), n)
        m = np.median(x[rng.integers(0, n, (B, n))], axis=1)
        out[k] = np.median(x), np.percentile(m, 1.25), np.percentile(m, 98.75)
    return out

print("A. verdict rule per cell. PASS = point >= 5 and lower bound > 0; bounded KILL = upper bound < 5; else 'not shown'")
for name in PROX:
    d = (P - col(name)) / den * 100
    c = d - np.median(d)
    for n in (40, 80, 120, 240):
        s = studies(c, n)
        hw = np.median(s[:, 2] - s[:, 0]), np.median(s[:, 0] - s[:, 1])
        line = []
        for dl in DELTAS:
            ps = np.mean((s[:, 0] + dl >= TH) & (s[:, 1] + dl > 0)) * 100
            kb = np.mean(s[:, 2] + dl < TH) * 100
            lb = np.mean(s[:, 1] + dl > 0) * 100
            line.append("d=%.1f P%5.1f K%5.1f L%5.1f" % (dl, ps, kb, lb))
        print("%-14s n=%3d se %.2f up-half %.2f low-half %.2f | " % (name[2:], n, s[:, 0].std(), hw[0], hw[1]) + " | ".join(line))

print("\nB. sign-flip null at n = 240 (true effect 0, symmetric): rate of lower bound > 0 (nominal 1.25 %), of PASS, of bounded KILL")
for name in PROX:
    d = (P - col(name)) / den * 100
    s = studies(d, 240, flip=True)
    print("  %-14s LB>0 %.2f %%  PASS %.2f %%  boundedKILL %.1f %%  UB>... median UB %.2f" % (name[2:], np.mean(s[:, 1] > 0) * 100, np.mean((s[:, 0] >= TH) & (s[:, 1] > 0)) * 100, np.mean(s[:, 2] < TH) * 100, np.median(s[:, 2])))

print("\nC. selection stage: 8 arms on n_sel seeds, pick the largest point. Joint seed resampling of 8 stored proxies.")
P8 = ("S|r4a1", "S|grid_r4a2", "S|z33133", "S|grid_z31333", "S|grid_a41000_10_2", "S|a4400_10_1", "S|3e", "S|3ex1")
M = np.stack([(P - col(n)) / den * 100 for n in P8], axis=1)
med = np.median(M, axis=0)
C = M - med
print("  proxies' stored medians", np.round(med, 2))
for nsel in (20, 40, 60, 80):
    idx = rng.integers(0, 240, (4000, nsel))
    m0 = np.median(C[idx], axis=1)          # studies x arms, all true 0
    best = m0.max(axis=1)
    print("  n_sel=%2d all eight at 0: best-of-8 point median %+.2f, p95 %+.2f, P(best >= 5) %.1f %%" % (nsel, np.median(best), np.percentile(best, 95), np.mean(best >= 5) * 100))
    for good in (2, 0):                     # the good arm has z33133's noise (2) or r4a1's (0)
        res = []
        for dl in (3.0, 5.0, 6.0, 7.0, 9.2):
            eff = med.copy(); eff[good] = dl  # the others stay at their stored (losing) effects
            pick = (m0 + eff).argmax(axis=1)
            eff0 = np.zeros(8); eff0[good] = dl  # harder: the others at 0
            pick0 = (m0 + eff0).argmax(axis=1)
            res.append("d=%.1f %5.1f/%5.1f" % (dl, np.mean(pick == good) * 100, np.mean(pick0 == good) * 100))
        print("     good arm noise %-8s P(pick good) others stored / others at 0: " % P8[good][2:] + " | ".join(res))
