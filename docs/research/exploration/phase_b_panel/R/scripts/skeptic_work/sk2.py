# EXPLORATORY: stability of the "PR-28-bound" label's location share on stored round 2 test rows (40 seeds, X1), from the first round's cached road split.
import pickle, numpy as np
P = "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/x1x2/b1.pkl"
res = pickle.load(open(P, "rb"))
W = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
C = res["X1"]
seeds = sorted(C["p333"])
PER = sorted({k[1] for k in C["p333"][seeds[0]] if k[0] == "main"})


def parts(a):
    out = []
    for s in seeds:
        c = C[a][s]
        seg = lambda n: sum(c[("main", p, n)] for p in PER)
        pend2 = sum(c[("pend_r2", p, "")] for p in PER)
        out.append([seg("m2 4a"), seg("down 4-5"), seg("between 3"), pend2, c[("resid", "", "")], c[("total", "", "")]])
    return np.array(out)


v3w = np.mean([parts(w) for w in W], axis=0)
rng = np.random.default_rng(20261110)
for rule in ("p333", "lr1000_10_1", "os0_10_10", "3ex1"):
    d = parts(rule) - v3w     # rule minus v3w, per seed
    lo_num = d[:, 0] + d[:, 3]     # road 4a and the ramp-2 insertion queue
    hi_num = lo_num + d[:, 1] + d[:, 4]     # plus roads 4-5 and every off-mainline part (upper bound of planb.md:143's set)
    den = d[:, 5]
    def share(i, num):
        de = np.median(den[i], axis=-1)
        return np.where(de > 0, np.median(num[i], axis=-1) / np.where(de > 0, de, 1), np.nan)
    all_ = np.arange(len(seeds))
    line = f"{rule}: point share low {float(share(all_, lo_num)):.2f}, high {float(share(all_, hi_num)):.2f}; "
    for n in (40, 160):
        idx = rng.integers(0, len(seeds), (20000, n))
        sl, sh = share(idx, lo_num), share(idx, hi_num)
        line += f"n={n}: P(share>0.5) low {np.nanmean(sl > 0.5):.2f}, high {np.nanmean(sh > 0.5):.2f}, 'not read' {np.isnan(sl).mean():.3f}; "
    print(line)
