# HOLDS probability under the merge-scaling model by a double bootstrap (truth = the stored sample), both rules required; plus margins for V2.
import numpy as np
from math import erf, sqrt
Z = np.load("cols.npz"); arms = list(Z["arms"]); A = {a: i for i, a in enumerate(arms)}
V = [a for a in arms if a.split("|")[1][0] == "w" and a.split("|")[1][1].isdigit()]
c = lambda a, k: Z[k][A[a]]; n = 480
LR, GR = "E30|lr400_16_1", "E30|grid_lr400_13_1"
rng = np.random.default_rng(99)
def lb_ub(D, idx):
    b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
    return np.percentile(b, 1.25), np.percentile(b, 99.375)
for k in (0.34, 0.2, 0.1, 0.02):
    f = lambda a: k * (c(a, "m1") + c(a, "m2")) + c(a, "rest") + c(a, "jn") + c(a, "e1")
    holds = worse = lr_only = 0; OUT = 300
    for _ in range(OUT):
        o = rng.integers(0, n, n); res = []
        for opp in (LR, GR):
            O = f(opp)[o]; m = np.median(O)
            D = [-(f(w)[o] - O) / m * 100 for w in V]
            res.append(lb_ub(D, rng.integers(0, n, (400, n))))
        holds += res[0][0] > 0 and res[1][0] > 0; lr_only += res[0][0] > 0; worse += res[0][1] < 0 or res[1][1] < 0
    print("k=%.2f  P(HOLDS: both lower bounds > 0) %.3f  (lr400_16_1 alone %.3f)  P(WORSE: a 98.75 %% upper bound < 0) %.3f   [%d outer x 400 inner]" % (k, holds / OUT, lr_only / OUT, worse / OUT, OUT))
Phi = lambda x: 0.5 * (1 + erf(x / sqrt(2)))
print("V2 margins with the proxy SE 0.35: P(95 % interval inside +-m), one rule")
for m in (1.5, 2.0, 3.0):
    print("  m=%.1f:" % m, " ".join("true %.1f -> %.3f" % (t, Phi((m - 1.96 * 0.35 - t) / 0.35) - Phi((-m + 1.96 * 0.35 - t) / 0.35)) for t in (0, 0.5, 1.0, 1.5, 2.0, 3.0)))
