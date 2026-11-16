"""EXPLORATORY. Lengthening rules against p333 under three delay definitions, S6 rows. Positive = arm better than p333."""
import pickle, numpy as np
T = pickle.load(open("s6x.pkl", "rb"))
rng = np.random.default_rng(20261110)
seeds = list(range(7480400, 7480640))
IDX = rng.integers(0, len(seeds), size=(10000, len(seeds)))
def col(cell, arm, k): return np.array([float(T[(cell, arm)][s][k]) for s in seeds])
def eff(a, o, sign=-1):
    d = a - o
    pt = sign * np.median(d) / np.median(o) * 100
    bs = sign * np.median(d[IDX], axis=1) / np.median(o[IDX], axis=1) * 100
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return f"{pt:+.2f} [{lo:+.2f}, {hi:+.2f}]"
ARMS = ["grid_z31333", "z33133", "grid_r4a2", "r4a1", "os0_10_10", "3E-D_TRUCK", "3E-C_TRUCK", "lr1000_16_2", "MPC-F", "copy", "3e", "nc"]
for cell in ("S", "TRUCK"):
    print("==", cell, "| arm vs p333, % of p333 median, positive = arm better")
    print("arm | all_delay | finishers' delay (key delay) | TTT (N) | passed (positive = more) | finished_pct diff (points, median)")
    for a in ARMS:
        out = [eff(col(cell, a, k), col(cell, "p333", k)) for k in ("all_delay", "delay", "N")]
        out.append(eff(col(cell, a, "passed"), col(cell, "p333", "passed"), sign=1))
        fp = np.median(col(cell, a, "finished_pct") - col(cell, "p333", "finished_pct"))
        print(a, "|", " | ".join(out), "|", f"{fp:+.2f}")
    # v3w arm (per-seed mean of 5) and stacked single learners
    W = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
    for k in ("all_delay", "delay"):
        arm = np.mean([col(cell, w, k) for w in W], axis=0)
        print("v3w arm", k, eff(arm, col(cell, "p333", k)))
        o = col(cell, "p333", k)
        D = np.array([col(cell, w, k) - o for w in W])  # 5 x n
        pt = -np.median(D) / np.median(o) * 100
        bs = -np.median(D[:, IDX].transpose(1, 0, 2).reshape(10000, -1), axis=1) / np.median(o[IDX], axis=1) * 100
        lo, hi = np.percentile(bs, [2.5, 97.5])
        print("v3w stacked", k, f"{pt:+.2f} [{lo:+.2f}, {hi:+.2f}]")
    print("medians: p333 all_delay", np.median(col(cell, "p333", "all_delay")), "delay", np.median(col(cell, "p333", "delay")), "finished_pct", np.median(col(cell, "p333", "finished_pct")))
