"""EXPLORATORY: tail and mean readings of stored S6 delay rows (rows already read for a verdict)."""
import numpy as np
Z = np.load('/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseA/rows/s6_scalars.npz')
K = list(Z['keys']); n = 240
L = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
rng = np.random.default_rng(20261110); IDX = rng.integers(0, n, (10000, n))
def col(c, a, k="all_delay"): return Z[f"{c}|{a}"][:, K.index(k)]
def ci(fn):
    b = np.array([fn(i) for i in IDX]); return np.percentile(b, (2.5, 97.5))
def show(tag, fn):
    lo, hi = ci(fn); print("    %-34s %+.2f [%+.2f, %+.2f]" % (tag, fn(np.arange(n)), lo, hi))
for c in ("TRUCK", "S"):
    nc = col(c, "nc"); hard = nc >= np.quantile(nc, 0.8)
    print("#####", c, "(positive = v3w lower delay; per-learner statistics averaged over the 5 learners; seed bootstrap 95 %)")
    for o in ("p333", "os0_10_10", "3E-D_TRUCK", "os1_15_10", "lr1000_16_2", "3E-C_TRUCK"):
        O = col(c, o); P = np.array([col(c, l) for l in L])
        print("  vs", o)
        show("median paired diff, % of median", lambda i: np.mean([np.median(O[i] - p[i]) for p in P]) / np.median(O[i]) * 100)
        show("mean paired diff, % of mean", lambda i: (O[i].mean() - P[:, i].mean()) / O[i].mean() * 100)
        show("q90 across seeds, %", lambda i: (np.quantile(O[i], .9) - np.mean([np.quantile(p[i], .9) for p in P])) / np.quantile(O[i], .9) * 100)
        def cvar(x): return np.sort(x)[-max(1, len(x) // 10):].mean()
        show("mean of worst 10 % of seeds, %", lambda i: (cvar(O[i]) - np.mean([cvar(p[i]) for p in P])) / cvar(O[i]) * 100)
        h = np.where(hard)[0]; rh = np.random.default_rng(1).integers(0, len(h), (10000, len(h)))
        f = lambda j: np.mean([np.median(O[h][j] - p[h][j]) for p in P]) / np.median(O[h][j]) * 100
        b = np.array([f(j) for j in rh]); print("    %-34s %+.2f [%+.2f, %+.2f]  (n=%d)" % ("hard seeds (top 20 % nc delay), med", f(np.arange(len(h))), *np.percentile(b, (2.5, 97.5)), len(h)))
