"""EXPLORATORY, read-only: in power.py's stand-in, what effect against os0_10_10 and the Z16 stand-in goes with a true effect e against p333 (full 240 stored seeds)?
Also: os0_10_10 against p333 on the seeds where they differ; rules with a median paired difference above 0 against p333."""
import pickle
import numpy as np
T = pickle.load(open("s.pkl", "rb"))
seeds = sorted(T["p333"])
col = lambda a: np.array([T[a][s]["d"] for s in seeds], float)
P = col("p333"); medP = np.median(P); OS = col("os0_10_10")
Z = P - (lambda x: x - np.median(x))(P - col("lr400_16_1"))
for a in ("r4a1", "z33133", "grid_r4a2", "grid_z31333"):
    c = 100 * (P - col(a)) / medP; c = c - np.median(c)
    out = []
    for e in (5.0, 6.0):
        A = P - (c + e) * medP / 100
        out.append("e %+.0f -> against os0_10_10 %+.2f, against the Z16 stand-in %+.2f" % (e, 100 * np.median(OS - A) / np.median(OS), 100 * np.median(Z - A) / np.median(Z)))
    print(a, "; ".join(out), "| corr of its paired difference with (os0 - p333): %.2f" % np.corrcoef(c, OS - P)[0, 1])
x = 100 * (P - OS) / medP
print("os0_10_10 against p333: identical seeds %d; where they differ: os0 lower on %d, higher on %d; mean %+.2f %%, median %+.2f %% (positive = os0 has less delay)" % ((x == 0).sum(), (x > 0).sum(), (x < 0).sum(), x.mean(), np.median(x)))
LEARN = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
pos = [(a, float(np.median(P - col(a)))) for a in sorted(T) if a not in LEARN + ("p333", "nc")]
print("rules:", len(pos), "; with median paired difference above 0 veh-s:", [(a, round(m, 1)) for a, m in pos if m > 0])
