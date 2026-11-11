"""EXPLORATORY: stage-0 statements for screen M from stored S6 rows. Median of paired differences, percentile bootstrap, 10,000 resamples."""
import pickle
import numpy as np
T, cfg = pickle.load(open("parts.pkl", "rb"))
seeds = list(range(7480400, 7480640)); n = 240
IDX = np.random.default_rng(20261110).integers(0, n, (10_000, n))
def col(cell, arm, k): return np.array([T[(cell, arm)][s][k] for s in seeds], float)
def ci(x, lo=2.5, hi=97.5):
    b = np.median(x[IDX], axis=1); return np.median(x), np.percentile(b, lo), np.percentile(b, hi)
f = lambda t: "%+.2f [%+.2f, %+.2f]" % t
for cell in ("S", "TRUCK"):
    tot = col(cell, "p333", "all_delay")
    print(f"## {cell}: p333 median all_delay {np.median(tot):.0f}; end_stop2 median {np.median(col(cell,'p333','end_stop2')):.1f}, end_stop {np.median(col(cell,'p333','end_stop')):.1f}")
    e1, e2 = col(cell, "p333", "exc1"), col(cell, "p333", "exc2")
    print("  merge excess share of delay, %: both", f(ci(100 * (e1 + e2) / tot)), "| merge 1", f(ci(100 * e1 / tot)), "mean %.1f" % (100 * e1 / tot).mean(), "| merge 2", f(ci(100 * e2 / tot)), "mean %.1f" % (100 * e2 / tot).mean())
    print("  f2 (4a + ramp-2 road + ramp-2 queue) share %:", f(ci(100 * col(cell, "p333", "f2") / tot)), "| ramp-2 road+queue share", f(ci(100 * col(cell, "p333", "ramp2") / tot)))
    print("  corr(exc2, end_stop2) %.2f; corr(exc2, all_delay) %.2f" % (np.corrcoef(e2, col(cell, "p333", "end_stop2"))[0, 1], np.corrcoef(e2, tot)[0, 1]))
    print("  arm: delay edge over p333 % (positive = arm has less delay) | f2 change, points of p333 median delay (negative = less friction) | end_stop2 change | sd of paired delay diff %, 1.4826*MAD")
    rows = []
    for (c, arm) in T:
        if c != cell or arm == "p333": continue
        d = 100 * (tot - col(cell, arm, "all_delay")) / np.median(tot)
        rows.append((np.median(d), arm, d))
    for med, arm, d in sorted(rows, key=lambda r: -r[0]):
        g = 100 * (col(cell, arm, "f2") - col(cell, "p333", "f2")) / np.median(tot)
        es = col(cell, arm, "end_stop2") - col(cell, "p333", "end_stop2")
        print(f"   {arm:18s} {f(ci(d))} | {f(ci(g))} | {f(ci(es))} | sd {d.std(ddof=1):.2f}, rsd {1.4826*np.median(np.abs(d-np.median(d))):.2f}; f2 sd {g.std(ddof=1):.2f}")
for a in ("z33133", "r4a1", "grid_r4a2", "grid_z31333", "os0_10_10", "a4400_10_1", "grid_a41000_10_2", "copy", "3E-D_TRUCK", "lr1000_10_1"):
    print(a, cfg[a])
