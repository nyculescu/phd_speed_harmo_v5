"""EXPLORATORY planning: as power.py, at the level for m comparisons (two-sided 1 - 0.05/m), steady traffic at 5,300 only."""
import pickle, sys
import numpy as np
T = pickle.load(open(sys.argv[1], "rb"))
M = int(sys.argv[2])
rng = np.random.default_rng(20261110)
seeds = sorted(T["S|p333"])
A = 100 * 0.05 / M / 2
STUD, B = 300, 2000
base = np.array([T["S|p333"][s]["d"] for s in seeds]); med = np.median(base)
print(f"m = {M}: two-sided level {100 - 2 * A:.3f} %")
for a in ("z33133", "os1_10_0", "r4a1"):
    d0 = 100 * (base - np.array([T[f"S|{a}"][s]["d"] for s in seeds])) / med
    for n in (240, 360):
        line = f"  {a} n {n}:"
        for e in (-4, 0, 3, 5, 7):
            d = d0 - np.median(d0) + e
            out = np.zeros(3); hw = []
            for _ in range(STUD):
                x = d[rng.integers(0, len(d), n)]
                m = np.median(x[rng.integers(0, n, (B, n))], axis=1)
                lo, hi, pt = np.percentile(m, A), np.percentile(m, 100 - A), np.median(x)
                hw.append((hi - lo) / 2)
                out[0 if (pt >= 3 and lo > 0) else 1 if hi < 3 else 2] += 1
            p, k, u = 100 * out / STUD
            line += f" e={e:+}: P {p:.0f} K {k:.0f} U {u:.0f};"
        print(line + f" half-width {np.median(hw):.2f}", flush=True)
