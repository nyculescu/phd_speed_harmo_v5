"""EXPLORATORY planning, read-only: Screen M's K1 as written, from stored S6 rows (cell S, 240 seeds).
A hypothetical long arm = p333's delay minus (a stored merge rule's centred paired difference + a true effect e).
K1 PASS needs, against EACH opponent, point >= 5 and the 97.5 % lower bound > 0. Opponents here: p333, os0_10_10 and a stand-in for Z16
(lr400_16_1 centred on p333: a rule that differs from p333 on every seed, median difference set to 0).
Also: the whole chain (pick the best of 4 on 60 seeds, verdict on 240 others), and the 6,000 noise level from the band rows."""
import pickle
import numpy as np
T = pickle.load(open("s.pkl", "rb"))
rng = np.random.default_rng(20261113)
seeds = sorted(T["p333"]); n0 = len(seeds)
col = lambda a: np.array([T[a][s]["d"] for s in seeds], float)
P = col("p333"); medP = np.median(P)
OS = col("os0_10_10")
Z = P - (lambda x: x - np.median(x))(P - col("lr400_16_1"))     # stand-in for Z16: equal to p333 in median
NOISE = ("r4a1", "z33133", "grid_r4a2", "grid_z31333")
C = {a: (lambda x: x - np.median(x))(100 * (P - col(a)) / medP) for a in NOISE}
B = 1000
def read(O, A, lev=97.5):
    """point, lower, upper of e = median(O - A) / median(O) x 100"""
    n = len(O); idx = rng.integers(0, n, (B, n)); x = O - A
    b = 100 * np.median(x[idx], axis=1) / np.median(O)
    a = (100 - lev) / 2
    return 100 * np.median(x) / np.median(O), np.percentile(b, a), np.percentile(b, 100 - a)
def verdict(i, A):
    r = [read(O[i], A[i]) for O in (P, OS, Z)]
    p1 = r[0][0] >= 5 and r[0][1] > 0
    p2 = p1 and r[1][0] >= 5 and r[1][1] > 0
    p3 = p2 and r[2][0] >= 5 and r[2][1] > 0
    return p1, p2, p3, r[0][2] < 5
ST = 1500
print("true effect against p333 | PASS against p333 alone / p333 and os0_10_10 / all three | BOUNDED (%), n = 240, 97.5 %")
for a in NOISE:
    print(f"noise {a}")
    for e in (0.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0):
        A = P - (C[a] + e) * medP / 100
        k = np.zeros(4)
        for _ in range(ST):
            k += verdict(rng.integers(0, n0, 240), A)
        k = 100 * k / ST
        print(f"   {e:+.0f}: {k[0]:5.1f} / {k[1]:5.1f} / {k[2]:5.1f} | {k[3]:5.1f}")
print("chain: 4 long arms, one with true effect e, three at 0; pick = highest median paired difference on 60 seeds; verdict on 240 other draws (all three opponents)")
for a in ("r4a1", "grid_z31333"):
    for e in (5.0, 6.0, 7.0):
        ok = pick = 0; S2 = 1000
        for _ in range(S2):
            m = [np.median(C[a][rng.integers(0, n0, 60)]) + (e if j == 0 else 0.0) for j in range(4)]
            if int(np.argmax(m)) == 0:
                pick += 1
                ok += verdict(rng.integers(0, n0, 240), P - (C[a] + e) * medP / 100)[2]
        print(f"   noise {a}, e {e:+.0f}: true arm picked {100 * pick / S2:.1f} %, screen PASS in the cell {100 * ok / S2:.1f} %")
print("6,000 veh/h, normal stand-in with the band rows' paired SD (8-11 % of p333's median; n = 240; one comparison):")
for sd in (8.0, 11.0):
    for e in (0.0, 3.0, 5.0, 6.0):
        k = np.zeros(2); S3 = 1500
        for _ in range(S3):
            x = rng.normal(e, sd, 240)
            b = np.median(x[rng.integers(0, 240, (B, 240))], axis=1)
            pt, lo, hi = np.median(x), np.percentile(b, 1.25), np.percentile(b, 98.75)
            k += (pt >= 5 and lo > 0, hi < 5)
        print(f"   SD {sd:.0f}, e {e:+.0f}: PASS {100 * k[0] / S3:5.1f} | BOUNDED {100 * k[1] / S3:5.1f}")
