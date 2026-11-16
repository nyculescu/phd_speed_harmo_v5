"""EXPLORATORY planning proxy: verdict rule requiring both intervals (percentile bootstrap and exact order-statistic) at 97.5 % two-sided."""
import pickle, sys
import numpy as np
from scipy.stats import binom
D = pickle.load(open(sys.argv[1], "rb"))
iD = list(D["keys"]).index("all_delay")
seeds = list(range(7480400, 7480640))
col = lambda name: np.array([D["s6"][name][s][iD] for s in seeds], float)
P = col("S|p333"); den = np.median(P)
rng = np.random.default_rng(20261111)
TH, STUD, B = 5.0, 2000, 1000
PROX = ("S|r4a1", "S|grid_r4a2", "S|z33133", "S|grid_z31333")
DELTAS = (0.0, 3.0, 4.0, 5.0, 6.0, 7.0, 9.2)

def os_ranks(n, a=0.0125):
    k = int(binom.ppf(a, n, 0.5))          # largest k with P(X < k) <= a, checked below
    while binom.cdf(k - 1, n, 0.5) > a:
        k -= 1
    while binom.cdf(k, n, 0.5) <= a:
        k += 1
    return k, n - k + 1                      # 1-based ranks of the lower and upper bound

def studies(c, n, flip=False):
    lo, hi = os_ranks(n)
    out = np.empty((STUD, 5))
    for i in range(STUD):
        x = c[rng.integers(0, len(c), n)]
        if flip:
            x = x * rng.choice((-1.0, 1.0), n)
        m = np.median(x[rng.integers(0, n, (B, n))], axis=1)
        xs = np.sort(x)
        out[i] = np.median(x), np.percentile(m, 1.25), np.percentile(m, 98.75), xs[lo - 1], xs[hi - 1]
    return out

for n in (120, 240):
    print("n", n, "order-statistic ranks", os_ranks(n), "coverage", 1 - 2 * binom.cdf(os_ranks(n)[0] - 1, n, 0.5))
    for name in PROX:
        d = (P - col(name)) / den * 100
        s = studies(d - np.median(d), n)
        line = []
        for dl in DELTAS:
            pb = np.mean((s[:, 0] + dl >= TH) & (s[:, 1] + dl > 0) & (s[:, 3] + dl > 0)) * 100
            kb = np.mean((s[:, 2] + dl < TH) & (s[:, 4] + dl < TH)) * 100
            line.append("d=%.1f P%5.1f K%5.1f" % (dl, pb, kb))
        f = studies(d, n, flip=True)
        print("  %-12s | " % name[2:] + " | ".join(line) + " || flip: LBboot>0 %.2f LBos>0 %.2f both %.2f; UB half os %.2f boot %.2f" % (
            np.mean(f[:, 1] > 0) * 100, np.mean(f[:, 3] > 0) * 100, np.mean((f[:, 1] > 0) & (f[:, 3] > 0)) * 100, np.median(s[:, 4] - s[:, 0]), np.median(s[:, 2] - s[:, 0])))
