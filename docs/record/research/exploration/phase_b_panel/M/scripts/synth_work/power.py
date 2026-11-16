"""EXPLORATORY planning, read-only: null and power of Screen M's verdict rule from stored paired differences (S6, cell S, against p333).
Rule: PASS = point >= 5 and 97.5 % lower bound > 0; BOUNDED = 97.5 % upper bound < 5; else not shown. One comparison."""
import pickle, sys
import numpy as np
T = pickle.load(open(sys.argv[1], "rb"))
rng = np.random.default_rng(20261111)
seeds = sorted(T["S|p333"])
P = np.array([T["S|p333"][s]["d"] for s in seeds], float); med = np.median(P)
NOISE = ("r4a1", "z33133", "grid_r4a2", "grid_z31333")
D = {a: 100 * (P - np.array([T["S|" + a][s]["d"] for s in seeds], float)) / med for a in NOISE}
def study(d0, n, STUD=2000, B=1000, thr=5.0, lev=97.5):
    a = (100 - lev) / 2
    out = np.zeros(3); hw = []
    for _ in range(STUD):
        x = d0[rng.integers(0, len(d0), n)]
        b = np.median(x[rng.integers(0, n, (B, n))], axis=1)
        lo, hi, pt = np.percentile(b, a), np.percentile(b, 100 - a), np.median(x)
        out[0 if (pt >= thr and lo > 0) else 1 if hi < thr else 2] += 1
        hw.append(hi - pt)
    return 100 * out / STUD, float(np.median(hw))
print("columns: true effect | PASS / BOUNDED / not shown (%) | median upper half-width (points)")
for n in (240,):
    for a in NOISE:
        d = D[a] - np.median(D[a])
        print(f"noise {a}, n {n}, paired SD {D[a].std(ddof=1):.1f}")
        for e in (0.0, 2.0, 3.0, 5.0, 6.0, 6.1, 7.0):
            p, hw = study(d + e, n)
            print(f"   {e:+.1f}: {p[0]:5.1f} / {p[1]:5.1f} / {p[2]:5.1f} | {hw:.2f}")
# sign-flip null of "lower bound > 0" (symmetric no-effect null), n = 240
print("sign-flip null, share of studies with the 97.5 % lower bound above 0 (nominal 1.25 %):")
for a in NOISE:
    d = D[a] - np.median(D[a]); k = 0; S = 2000
    for _ in range(S):
        x = d[rng.integers(0, len(d), 240)] * rng.choice((-1.0, 1.0), 240)
        b = np.median(x[rng.integers(0, 240, (1000, 240))], axis=1)
        k += np.percentile(b, 1.25) > 0
    print(f"   {a}: {100 * k / S:.2f}")
# selection on 60 seeds among 4 long arms
print("selection, 60 seeds, 4 arms: P(best null arm reads >= 5 %); P(a true 6 % arm is picked over 3 null arms)")
for a in NOISE:
    d = D[a] - np.median(D[a]); S = 4000; k0 = k1 = 0
    for _ in range(S):
        m = [np.median(d[rng.integers(0, len(d), 60)]) for _ in range(4)]
        k0 += max(m) >= 5.0
        k1 += (m[0] + 6.0) > max(m[1:])
    print(f"   {a}: {100 * k0 / S:.1f} | {100 * k1 / S:.1f}")
