"""EXPLORATORY. S6 delay: v3w against each of the 23 opponents, arm-level (the record's form) and stacked single learners; share of seeds identical to p333."""
import pickle, numpy as np
T = pickle.load(open("s6all.pkl", "rb"))
seeds = list(range(7480400, 7480640)); n = len(seeds)
rng = np.random.default_rng(20261110)
IDX = rng.integers(0, n, size=(10000, n))
W = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
def col(cell, arm): return np.array([T[(cell, arm)][s] for s in seeds])
for cell in ("TRUCK", "S"):
    opp = sorted(a for (c, a) in T if c == cell and a not in W and a != "nc")
    wl = np.array([col(cell, w) for w in W]); arm = wl.mean(axis=0)
    p = col(cell, "p333")
    rows = []
    for o in opp:
        x = col(cell, o)
        d = x - arm  # positive = v3w lower
        pt = np.median(d) / np.median(x) * 100
        bs = np.median(d[IDX], axis=1) / np.median(x[IDX], axis=1) * 100
        lo, hi = np.percentile(bs, [1.25, 98.75])
        D = x[None, :] - wl
        pts = np.median(D) / np.median(x) * 100
        bss = np.median(D[:, IDX].transpose(1, 0, 2).reshape(10000, -1), axis=1) / np.median(x[IDX], axis=1) * 100
        los, his = np.percentile(bss, [1.25, 98.75])
        same = int(np.sum(np.abs(x - p) < 1e-9))
        nl = sum(1 for k in range(5) if np.median(x - wl[k]) > 0)
        rows.append((pt, o, lo, hi, pts, los, his, same, nl))
    rows.sort()
    print("==", cell, "| opponent | arm-level 97.5 % | stacked 97.5 % | seeds identical to p333 of 240 | learners with positive point")
    for pt, o, lo, hi, pts, los, his, same, nl in rows:
        print(f"{o:18s} | {pt:+.2f} [{lo:+.2f}, {hi:+.2f}] | {pts:+.2f} [{los:+.2f}, {his:+.2f}] | {same} | {nl}")
    print("blockers arm-level:", sum(1 for r in rows if r[2] <= 0), "| blockers stacked:", sum(1 for r in rows if r[5] <= 0), "| stacked shown worse (upper<0):", sum(1 for r in rows if r[6] < 0), "| arm shown worse:", sum(1 for r in rows if r[3] < 0))
