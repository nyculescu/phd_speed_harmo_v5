"""Served throughput (passed, positive = v3w more) and TTT (N, positive = v3w less) against every non-learning arm, C-D5 statistic."""
import numpy as np
z = np.load("arr.npz")
V = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
arms = [a for a in z["arms"] if a not in V]
n = len(z["seeds"]); idx = np.random.default_rng(20261108).integers(0, n, (20000, n))
def edge(o, k, s):
    O = z[f"{o}__{k}"]; m = np.median(O)
    D = [s * (z[f"{w}__{k}"] - O) / m * 100 for w in V]
    b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0)
    return np.mean([np.median(d) for d in D]), *np.percentile(b, (1.25, 98.75))
for o in arms:
    p = edge(o, "passed", 1.0); t = edge(o, "N", -1.0)
    print(f"{o}: passed %+.2f [%+.2f, %+.2f]  TTT %+.2f [%+.2f, %+.2f]" % (*p, *t))
