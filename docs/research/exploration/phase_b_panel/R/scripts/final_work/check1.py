# EXPLORATORY: own recomputation of the skeptics' numbers for screen R (stored X1 rows, 120 seeds, already read for verdicts).
import numpy as np
from math import comb
from load import RULES
Z = np.load(__file__.replace("check1.py", "x1.npz"))
L, O = Z["L"], Z["O"]
N = len(L)
arm = L.mean(axis=1)
d = O - arm[:, None]
med = np.median(O, axis=0)
pt = 100 * np.median(d, axis=0) / med
order = np.argsort(pt)
rng = np.random.default_rng(424242)
print("A. stored points, 97.5 % CI (direct bootstrap, B = 20,000)")
idx = rng.integers(0, N, (20000, N))
for j in order:
    b = 100 * np.median(d[idx, j], axis=1) / med[j]
    print(f"  {RULES[j]}: {pt[j]:+.2f} [{np.percentile(b, 1.25):+.2f}, {np.percentile(b, 98.75):+.2f}]")


def crit(n, q=0.0125):
    """largest count c of non-positive differences for which the bootstrap chance of a median at or below 0 stays under q"""
    out = -1
    for c in range(n + 1):
        p = c / n
        pm = [comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(n + 1)]
        pr = sum(pm[n // 2 + 1:]) + (0.5 * pm[n // 2] if n % 2 == 0 else 0.0)
        if pr < q:
            out = c
        else:
            break
    return out


def study(Ou, n, R=10000, tau=3.0, seed=0):
    g = np.random.default_rng(777 + seed)
    c = crit(n)
    res = np.zeros(4)
    close = np.zeros(Ou.shape[1])
    for _ in range(R // 500):
        ii = g.integers(0, N, (500, n))
        Lr, Or = L[ii], Ou[ii]
        dd = Or - Lr.mean(axis=2)[:, :, None]
        p = 100 * np.median(dd, axis=1) / np.median(Or, axis=1)
        k1p = (p >= tau).all(axis=1)
        k1b = ((dd <= 0).sum(axis=1) <= c).all(axis=1)
        pos = np.median(Or[:, :, None, :] - Lr[:, :, :, None], axis=1) > 0
        k2 = pos.all(axis=2).sum(axis=1) >= 4
        res += [k1p.sum(), k1b.sum(), k2.sum(), (k1p & k1b & k2).sum()]
        close += np.bincount(p.argmin(axis=1), minlength=Ou.shape[1])
    return res / R, close / R


def shift(js, e):
    Ou = O.copy()
    for j in js:
        Ou[:, j] = O[:, j] - (pt[j] - e) / 100 * med[j]
    return Ou


n = 160
print(f"\nB. pass chance, n = {n}, k nearest stored rules shifted to one true edge (others as stored)")
for k in (1, 3, 5, 12):
    js = order[:k]
    print(f"  k={k}: " + " | ".join(f"e={e}: {study(shift(js, e), n)[0][3]:.3f}" for e in (0, 2, 3, 3.5, 4, 4.24, 4.5, 5, 6)))
print("\nC. as stored")
r, cl = study(O, n)
print(f"  3 % bar: point {r[0]:.3f}, bound {r[1]:.3f}, K2 {r[2]:.3f}, PASS {r[3]:.3f}; closest: " + ", ".join(f"{RULES[j]} {cl[j]:.2f}" for j in order[:4]))
r5, _ = study(O, n, tau=5.0)
print(f"  5 % bar at arm level: PASS {r5[3]:.3f}")
print("\nD. direct percentile bootstrap of the bound, 600 studies, B = 2,000, as stored and k = 5 at 4.24")
for name, Ou in (("as stored", O), ("k=5 at 4.24", shift(order[:5], 4.24))):
    g = np.random.default_rng(99)
    hit = 0
    for _ in range(600):
        ii = g.integers(0, N, n)
        Lr, Or = L[ii], Ou[ii]
        dd = Or - Lr.mean(axis=1)[:, None]
        p = 100 * np.median(dd, axis=0) / np.median(Or, axis=0)
        bb = g.integers(0, n, (2000, n))
        lb = np.percentile(np.median(dd[bb], axis=1), 1.25, axis=0)
        pos = np.median(Or[:, None, :] - Lr[:, :, None], axis=0) > 0
        hit += (p >= 3.0).all() and (lb > 0).all() and pos.all(axis=1).sum() >= 4
    print(f"  {name}: PASS {hit / 600:.3f}")
print("\nE. selection noise: best of 11 stored rules against p333, a candidate truly x % below p333")
p333 = O[:, 0]
D = 100 * (p333[:, None] - O[:, 1:]) / np.median(p333)
Dc = D - np.median(D, axis=0)
for ns in (20, 40, 50, 80):
    g = np.random.default_rng(5)
    m = np.median(Dc[g.integers(0, N, (20000, ns))], axis=1)
    line = f"  n={ns}: apparent gain of the best of 11 when none is better: median {np.median(m.max(axis=1)):+.2f}, 95th {np.percentile(m.max(axis=1), 95):+.2f};"
    for x in (2.0, 3.0):
        hit = top3 = 0
        for j in range(Dc.shape[1]):
            mm = m.copy(); mm[:, j] += x
            hit += (mm.argmax(axis=1) == j).mean()
            top3 += ((mm > mm[:, [j]]).sum(axis=1) < 3).mean()
        line += f" true {x:.0f} %: picked first {hit / Dc.shape[1]:.2f}, in the best 3 {top3 / Dc.shape[1]:.2f};"
    print(line)
print("\nF. os0_10_10 against p333 on delay (positive = os0_10_10 less delay): pooled", round(float(np.median(D[:, 1])), 2))
