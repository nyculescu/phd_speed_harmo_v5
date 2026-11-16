"""Emergency-braking counts per arm from m_peak_* (PEAK_EDGES: index 6 = -7..-8, 7 = -8..-9, 8 = beyond -9 m/s2)."""
import json, numpy as np, collections
ROWS = "/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl"
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
T = collections.defaultdict(dict)
with open(ROWS) as f:
    for line in f:
        r = json.loads(line); n = r["name"].split("|", 1)[1]
        pk = {c: np.array(r[f"m_peak_{c}"]) for c in ("car", "alks", "truck")}
        T[n][r["seed"]] = (sum(p[6:].sum() for p in pk.values()), sum(p[8] for p in pk.values()), pk["alks"][8], pk["car"][8] + pk["truck"][8], r["collisions"])
seeds = sorted(T["w0u250"]); S = len(seeds)
A = {n: np.array([T[n][s] for s in seeds], float) for n in T}   # seed x 5
sc = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json")); comp = set(sc["competitors"])
L = np.stack([A[w] for w in V3W])  # 5 x seed x 5
rng = np.random.default_rng(20261108); idx = rng.integers(0, S, size=(20000, S))
print("per-run means: ge7, ge9 all, ge9 alks, ge9 car+truck, collisions")
print("v3w learners", [np.round(A[w].mean(0), 3).tolist() for w in V3W])
print("share of v3w runs with any ge9 ALKS event:", round(float((L[:, :, 2] > 0).mean()), 3))
out = []
for n in sorted(A):
    if n in V3W: continue
    R = A[n]
    for j, lab in ((0, "ge7"), (1, "ge9")):
        d = L[:, :, j].mean(0) - R[:, j]      # v3w (mean of learners) minus rule, per seed
        rel = -d.mean() / R[:, j].mean() * 100 if R[:, j].mean() else np.nan
        bs = d[idx].mean(1); lo, hi = np.percentile(bs, [2.5, 97.5])
        out.append((lab, n, n in comp, R[:, j].mean(), L[:, :, j].mean(), rel, lo, hi))
for lab in ("ge7", "ge9"):
    print(f"\n{lab}: arm C/T rule_mean v3w_mean  rel% (positive = v3w fewer)  mean diff v3w-rule 95% [lo, hi]")
    for o in sorted([o for o in out if o[0] == lab], key=lambda x: x[5]):
        print(f"  {o[1]:18s} {'C' if o[2] else 'T'} {o[3]:7.3f} {o[4]:7.3f} {o[5]:+7.1f}  [{o[6]:+.3f}, {o[7]:+.3f}]")
