"""EXPLORATORY planning, read-only: Screen M's K1 at 5,300 under two PASS forms, from stored S6 rows (cell S, 240 seeds).
Hypothetical long arm = p333's delay minus (a stored merge rule's centred paired difference + a true effect e against p333).
Opponents: p333, os0_10_10, and a stand-in for Z16 (lr400_16_1 re-centred on p333: differs on every seed, median difference 0).
Form A: point >= 5 and 97.5 % lower bound > 0 against EACH opponent.  Form B: point >= 5 against p333; lower bound > 0 against each.
BOUNDED: 97.5 % upper bound against p333 < 5.  One index matrix per study for every comparison (planb.md:424)."""
import pickle, sys
import numpy as np
T = pickle.load(open("mine.pkl", "rb"))
rng = np.random.default_rng(424242)
seeds = sorted(T["p333"]); n0 = len(seeds)
col = lambda a: np.array([T[a][s]["d"] for s in seeds], float)
P = col("p333"); medP = np.median(P); OS = col("os0_10_10")
cz = P - col("lr400_16_1"); Z = P - (cz - np.median(cz))
NOISE = ("r4a1", "z33133", "grid_r4a2", "grid_z31333")
C = {}
for a in NOISE:
    x = 100 * (P - col(a)) / medP; C[a] = x - np.median(x)
B = 1000
def reads(i, A):
    idx = rng.integers(0, len(i), (B, len(i)))
    out = []
    for O in (P, OS, Z):
        o = O[i]; x = o - A[i]
        b = 100 * np.median(x[idx], axis=1) / np.median(o)
        out.append((100 * np.median(x) / np.median(o), np.percentile(b, 1.25), np.percentile(b, 98.75)))
    return out
def verdict(i, A):
    r = reads(i, A)
    fa = all(pt >= 5 and lo > 0 for pt, lo, hi in r)
    fb = r[0][0] >= 5 and all(lo > 0 for pt, lo, hi in r)
    return fa, fb, r[0][2] < 5
ST = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
print("true effect | PASS form A (5 %% against each) / form B (5 %% against p333, lower bound > 0 against each) | BOUNDED | NOT SHOWN under B  (%%, n = 240, 97.5 %%, %d studies)" % ST)
for a in NOISE:
    print("noise", a)
    for e in (0.0, 2.0, 3.0, 5.0, 6.0, 7.0, 8.0):
        A = P - (C[a] + e) * medP / 100
        k = np.zeros(3)
        for _ in range(ST):
            k += verdict(rng.integers(0, n0, 240), A)
        k = 100 * k / ST
        print("   %+.0f: %5.1f / %5.1f | %5.1f | %5.1f" % (e, k[0], k[1], k[2], 100 - k[1] - k[2]))
print("chain, form B: 4 long arms (one at true effect e, three at 0); pick = highest median paired difference on 60 seeds; verdict on 240 other draws")
for a in ("r4a1", "grid_z31333"):
    for e in (0.0, 5.0, 6.0, 7.0, 8.0):
        S2 = 800; ok = okA = pick = bnd = 0
        for _ in range(S2):
            m = [np.median(C[a][rng.integers(0, n0, 60)]) + (e if j == 0 else 0.0) for j in range(4)]
            j = int(np.argmax(m)); pick += j == 0
            eff = e if j == 0 else 0.0
            fa, fb, bd = verdict(rng.integers(0, n0, 240), P - (C[a] + eff) * medP / 100)
            ok += fb; okA += fa; bnd += bd
        print("   noise %s, e %+.0f: true arm picked %5.1f %%; PASS B %5.1f %%, PASS A %5.1f %%; BOUNDED %5.1f %%" % (a, e, 100 * pick / S2, 100 * ok / S2, 100 * okA / S2, 100 * bnd / S2))
# half-widths at n = 240 and at n = 60 (97.5 %), from the centred stored differences
for a in NOISE:
    hw = []
    for nn in (240, 60):
        u = []
        for _ in range(300):
            x = C[a][rng.integers(0, n0, nn)]
            b = np.median(x[rng.integers(0, nn, (B, nn))], axis=1)
            u.append((np.percentile(b, 98.75) - np.median(x), np.median(x) - np.percentile(b, 1.25)))
        hw.append(np.median(np.array(u), axis=0))
    print("half-widths %s: n 240 upper %.1f lower %.1f; n 60 upper %.1f lower %.1f" % (a, hw[0][0], hw[0][1], hw[1][0], hw[1][1]))
