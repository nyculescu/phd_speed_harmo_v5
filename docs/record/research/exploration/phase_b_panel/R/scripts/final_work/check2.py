# EXPLORATORY: how often the "PR-28-bound" label fires on stored rows (round 2 test seeds, 40, X1), old and revised reading.
import pickle, numpy as np
res = pickle.load(open("/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/x1x2/b1.pkl", "rb"))
C = res["X1"]
W = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
ARMS = ["p333", "lr1000_10_1", "os0_10_10"]
seeds = sorted(C["p333"])
PER = sorted({k[1] for k in C["p333"][seeds[0]] if k[0] == "main"})


def parts(a):
    out = []
    for s in seeds:
        c = C[a][s]
        seg = lambda n: sum(c[("main", p, n)] for p in PER)
        out.append([seg("m2 4a") + sum(c[("pend_r2", p, "")] for p in PER), seg("down 4-5") + c[("resid", "", "")], c[("total", "", "")], c[("end_stop2", "", "")]])
    return np.array(out)


v = np.mean([parts(w) for w in W], axis=0)
P = {a: parts(a) for a in ARMS}
lo = np.stack([P[a][:, 0] - v[:, 0] for a in ARMS], axis=1)
hi = lo + np.stack([P[a][:, 1] - v[:, 1] for a in ARMS], axis=1)
tot = np.stack([P[a][:, 2] - v[:, 2] for a in ARMS], axis=1)
ref = np.stack([P[a][:, 2] for a in ARMS], axis=1)
es = np.stack([P[a][:, 3] - v[:, 3] for a in ARMS], axis=1)
print("points, 40 seeds:", {a: round(100 * float(np.median(tot[:, j]) / np.median(ref[:, j])), 2) for j, a in enumerate(ARMS)})
print("share low / high:", {a: (round(float(np.median(lo[:, j]) / np.median(tot[:, j])), 2), round(float(np.median(hi[:, j]) / np.median(tot[:, j])), 2)) for j, a in enumerate(ARMS)})
print("end_stop2 medians: v3w", float(np.median(v[:, 3])), {a: float(np.median(P[a][:, 3])) for a in ARMS})
rng = np.random.default_rng(31)
import sys
n, R = int(sys.argv[1]) if len(sys.argv) > 1 else 160, 20000
ii = rng.integers(0, len(seeds), (R, n))
pt = 100 * np.median(tot[ii], axis=1) / np.median(ref[ii], axis=1)
den = np.median(tot[ii], axis=1)
for name, num in (("low", lo), ("high", hi)):
    sh = np.median(num[ii], axis=1) / np.where(den > 0, den, np.nan)
    fire = sh > 0.5
    cl = pt.argmin(axis=1)
    old = fire[np.arange(R), cl]
    for w in (1.0, 1.5, 2.0):
        near = pt <= pt.min(axis=1, keepdims=True) + w
        print(f"  share {name}: closest arm only fires {old.mean():.2f}; any arm within {w} points fires {(fire & near).any(axis=1).mean():.2f}; arms read: mean {near.sum(axis=1).mean():.2f}")
    print(f"  share {name}: against p333 alone {fire[:, 0].mean():.2f}; against any of the three {fire.any(axis=1).mean():.2f}")
print("closest:", {a: round(float((pt.argmin(axis=1) == j).mean()), 2) for j, a in enumerate(ARMS)})
# end_stop2 clause: the arm's lane-end stops shown higher than v3w's (95 % lower bound of the median paired difference above 0)
g = np.random.default_rng(32)
hit = np.zeros(3)
for _ in range(300):
    s = g.integers(0, len(seeds), n)
    b = np.median(es[s][g.integers(0, n, (1000, n))], axis=1)
    hit += np.percentile(b, 2.5, axis=0) > 0
print("end_stop2 shown higher than v3w's (95 %), n = 160:", dict(zip(ARMS, (hit / 300).round(2))))
