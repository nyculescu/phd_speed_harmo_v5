import json, numpy as np, collections
D = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/2d269ac5-95be-4f04-801b-ec9cc9873355/scratchpad/cfv/complete/"
res = json.load(open(D + "jams_all.json"))
sc = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json"))
comp = set(sc.get("competitors", []))
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
T = collections.defaultdict(dict)
for n, s, j, *_ in res: T[n.split("|", 1)[1]][s] = j
seeds = sorted(T["w0u250"]); S = len(seeds)
A = {n: np.array([T[n][s] for s in seeds], float) for n in T}
rng = np.random.default_rng(20261108); idx = rng.integers(0, S, size=(20000, S))
print("competitors in screen.json:", len(comp))
out = []
for n in sorted(A):
    if n in V3W: continue
    R = A[n]; den = np.median(R)
    per = np.stack([-(A[w] - R) / den * 100 for w in V3W])  # learner x seed
    pt = np.mean(np.median(per, 1))
    bs = np.mean(np.median(per[:, idx], 2), 0)
    lo, hi = np.percentile(bs, [1.25, 98.75]); hi95 = np.percentile(bs, 97.5)
    # mean-based percent variant
    mp_ = -(np.stack([A[w] for w in V3W]).mean(0) - R).mean() / R.mean() * 100
    bsm = np.array([-(np.stack([A[w] for w in V3W]).mean(0)[i] - R[i]).mean() / R[i].mean() * 100 for i in idx[:4000]])
    out.append((n, n in comp, pt, lo, hi, hi95, (bs == 0).mean(), mp_, *np.percentile(bsm, [1.25, 98.75, 97.5])))
print("arm comp | C-D5 pt [97.5%] hi95 share_bs==0 | mean-based % [97.5%] hi95  (positive = v3w fewer jams)")
for r in sorted(out, key=lambda x: x[7]):
    print(f"{r[0]:18s} {'C' if r[1] else 'T'} | {r[2]:+6.2f} [{r[3]:+6.2f}, {r[4]:+6.2f}] hi95 {r[5]:+6.2f} z{r[6]:.2f} | {r[7]:+6.2f} [{r[8]:+6.2f}, {r[9]:+6.2f}] hi95 {r[10]:+6.2f}")
