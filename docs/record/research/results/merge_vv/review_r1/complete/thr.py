# TTC threshold sensitivity on stored E30 rows (post hoc, C-D5 form as design/a3.py)
import pickle, numpy as np, sys
R = pickle.load(open(sys.argv[1], "rb"))
V3W = ["E30|w0u250", "E30|w1u500", "E30|w2u250", "E30|w3u500", "E30|w4u500"]
names = sorted({n for n, s in R}); seeds = sorted({s for n, s in R})
def col(k, a): return np.array([R[(a, s)].get(k, 0.0 if k in ("ttc15","ttc2","sev3") else np.nan) for s in seeds], float)
def boot(P, Rr, B=4000, seed=20261108):
    d = -(P - Rr) / max(np.median(Rr), 1e-9) * 100
    rng = np.random.default_rng(seed); idx = rng.integers(0, Rr.shape[0], (B, Rr.shape[0]))
    b = np.mean([np.median(x[idx], axis=1) for x in d], axis=0)
    return np.mean(np.median(d, axis=1)), np.percentile(b, (1.25, 98.75))
print("n seeds", len(seeds))
for opp in ("E30|lr400_16_1", "E30|grid_lr400_13_1", "E30|p333", "E30|nc"):
    for k in ("ttc_net", "ttc2", "ttc15", "sev3"):
        P = np.array([col(k, w) for w in V3W]); Q = col(k, opp)
        pt, q = boot(P, Q)
        print(f"{opp:22s} {k:8s} v3w med {np.median(P):7.1f} opp med {np.median(Q):7.1f} edge {pt:+6.2f} [{q[0]:+6.2f},{q[1]:+6.2f}]")
