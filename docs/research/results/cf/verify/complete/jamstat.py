import json, numpy as np, collections
D = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/2d269ac5-95be-4f04-801b-ec9cc9873355/scratchpad/cfv/complete/"
res = json.load(open(D + "jams_all.json"))
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
T = collections.defaultdict(dict); H = collections.defaultdict(lambda: collections.Counter())
for n, s, j, heads, vs, e in res:
    n = n.split("|", 1)[1]; T[n][s] = j
    for k, v in heads.items(): H[n][k] += v
seeds = sorted(T["w0u250"]); S = len(seeds)
A = {n: np.array([T[n][s] for s in seeds], float) for n in T}
L = np.stack([A[w] for w in V3W])
print("seeds", S)
print("v3w learners: mean jams", [round(A[w].mean(), 2) for w in V3W], "median", [np.median(A[w]) for w in V3W], "share>0", [round((A[w] > 0).mean(), 3) for w in V3W])
rng = np.random.default_rng(20261108); idx = rng.integers(0, S, size=(20000, S))
rows = []
for n in sorted(T):
    if n in V3W: continue
    R = A[n]
    d = L - R  # learner minus rule, per seed; positive = v3w more jams
    md = d.mean(0)  # mean over learners
    pt = md.mean(); bs = md[idx].mean(1)
    lo, hi = np.percentile(bs, [1.25, 98.75]); lo95, hi95 = np.percentile(bs, [2.5, 97.5])
    rows.append((n, R.mean(), np.median(R), (R > 0).mean(), pt, lo, hi, hi95, lo95))
print("arm  mean  median  share>0  | mean over learners of mean paired diff (v3w - rule), 97.5% [lo, hi], 95% lo; positive = v3w MORE jams")
for r in sorted(rows, key=lambda x: x[4]):
    print(f"{r[0]:18s} {r[1]:6.2f} {r[2]:4.1f} {r[3]:5.3f} | {r[4]:+6.2f} [{r[5]:+6.2f}, {r[6]:+6.2f}] lo95 {r[8]:+6.2f}")
print("v3w jam heads", {w: dict(H[w]) for w in V3W[:2]}); print("lr400_16_1 heads", dict(H["lr400_16_1"])); print("p333 heads", dict(H["p333"]))
