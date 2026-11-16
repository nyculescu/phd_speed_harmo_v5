"""Share of ramp merges in the last 20 % of the acceleration lane (m_mergepos_* has 10 position bins), per arm; post hoc."""
import json, numpy as np, collections
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
T = collections.defaultdict(dict)
with open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl") as f:
    for line in f:
        r = json.loads(line); n = r["name"].split("|", 1)[1]
        a, b = np.array(r["m_mergepos_m1"], float), np.array(r["m_mergepos_m2"], float)
        T[n][r["seed"]] = (a[-2:].sum() / max(a.sum(), 1), b[-2:].sum() / max(b.sum(), 1), a.sum(), b.sum(), r["m_ttc3_lc"])
seeds = sorted(T["w0u250"]); S = len(seeds)
A = {n: np.array([T[n][s] for s in seeds]) for n in T}
L = np.stack([A[w] for w in V3W]).mean(0)
rng = np.random.default_rng(20261108); idx = rng.integers(0, S, size=(10000, S))
print("arm | late-merge share m1, m2 (mean) | v3w - rule late share m2, 95% | merges m1, m2 | ttc3_lc")
print(f"v3w (mean of 5)    | {L[:,0].mean():.3f} {L[:,1].mean():.3f} | | {L[:,2].mean():.0f} {L[:,3].mean():.0f} | {L[:,4].mean():.0f}")
for n in sorted(A, key=lambda n: A[n][:, 1].mean()):
    if n in V3W: continue
    R = A[n]; d = L[:, 1] - R[:, 1]; bs = d[idx].mean(1)
    print(f"{n:18s} | {R[:,0].mean():.3f} {R[:,1].mean():.3f} | {d.mean():+.3f} [{np.percentile(bs,2.5):+.3f}, {np.percentile(bs,97.5):+.3f}] | {R[:,2].mean():.0f} {R[:,3].mean():.0f} | {R[:,4].mean():.0f}")
