# EXPLORATORY: label-swap null of one comparison and the 5 % bar at n = 240; interval half-widths.
import numpy as np
import check1 as c
N = c.N
d0 = c.d[:, 0]
med = c.med[0]
g = np.random.default_rng(2024)
for n in (160, 240):
    cr = c.crit(n)
    R = 40000
    lb = pt3 = 0
    for _ in range(R // 4000):
        ii = g.integers(0, N, (4000, n))
        sg = g.choice([-1.0, 1.0], (4000, n))
        dd = d0[ii] * sg
        ok = (dd <= 0).sum(axis=1) <= cr
        lb += ok.sum()
        pt3 += (ok & (100 * np.median(dd, axis=1) / med >= 3.0)).sum()
    print(f"label-swap null, v3w against p333, n = {n}: lower bound above 0 in {lb / R:.4f} (nominal 0.0125); with the 3 % point clause {pt3 / R:.4f}")
    r5, _ = c.study(c.O, n, R=4000, tau=5.0)
    r3, _ = c.study(c.O, n, R=4000, tau=3.0)
    print(f"as stored, n = {n}: 3 % bar PASS {r3[3]:.3f}; 5 % bar PASS {r5[3]:.3f}")
    lo, hi = [], []
    for _ in range(300):
        x = d0[g.integers(0, N, n)]
        b = np.median(x[g.integers(0, n, (2000, n))], axis=1)
        q = np.percentile(b, [1.25, 98.75])
        lo.append(100 * (np.median(x) - q[0]) / med); hi.append(100 * (q[1] - np.median(x)) / med)
    print(f"half-widths of the 97.5 % interval against p333, n = {n}: -{np.mean(lo):.2f} / +{np.mean(hi):.2f}")
