"""Swap null (c1_confirm §1 as I read it): one sign per learner and seed on the per-seed edge; rate = mean of the false
rates of 'lower bound above 0' and 'upper bound below 0' at the reading's level."""
import json, sys, time
import numpy as np

E = np.load("edges_A.npz")
N = 480


def counts(K, rng):
    idx = rng.integers(0, N, size=(K, N))
    c = np.zeros((K, N), dtype=np.int16)
    for k in range(K):
        c[k] = np.bincount(idx[k], minlength=N)
    return c


def boot_stat(e, cnt):
    """Bootstrap medians from resample counts: the 240th and 241st order statistics of each weighted resample."""
    out = np.zeros(cnt.shape[0])
    for l in range(e.shape[0]):
        o = np.argsort(e[l], kind="stable"); v = e[l][o]
        cs = np.cumsum(cnt[:, o], axis=1)
        out += (v[(cs >= N // 2).argmax(1)] + v[(cs >= N // 2 + 1).argmax(1)]) / 2
    return out / e.shape[0]


def null(e, swaps, K, lo_p, hi_p, seed):
    rng = np.random.default_rng(seed)
    cnt = counts(K, rng)
    f_lo = f_hi = 0
    for i in range(swaps):
        s = rng.integers(0, 2, size=e.shape) * 2 - 1
        bs = boot_stat(e * s, cnt)
        lo, hi = np.percentile(bs, [lo_p, hi_p])
        f_lo += lo > 0
        f_hi += hi < 0
    return {"swaps": swaps, "resamples": K, "pct": [lo_p, hi_p], "seed": seed,
            "rate_lo_above0": f_lo / swaps, "rate_hi_below0": f_hi / swaps, "rate": (f_lo + f_hi) / (2 * swaps)}


out = {}
jobs = [("V3a_ttc_net_300|lr400_16_1", 1.9), ("V3a_ttc_net_300|grid_lr400_13_1", 1.9), ("V3a_main_300|lr400_16_1", 1.9),
        ("V3a_main_300|grid_lr400_13_1", 1.9), ("V3b_ttc_net_600|lr400_16_1", 1.9), ("V3b_ttc_net_600|grid_lr400_13_1", 1.9)]
for j, (key, bar) in enumerate(jobs):
    t = time.time()
    r = null(E[key], 2000, 2000, 1.25, 98.75, 9100 + j)
    if r["rate"] * 100 > bar:
        r["re_estimate"] = null(E[key], 20000, 2000, 1.25, 98.75, 9200 + j)
    r["sec"] = time.time() - t
    out[key + "|97.5"] = r
    print(key, r, flush=True)
    json.dump(out, open("nulls_A.json", "w"), indent=1)
t = time.time()
r = null(E["V3b_ttc_net_600|lr400_16_1"], 20000, 4000, 0.625, 99.375, 9300)
r["sec"] = time.time() - t
out["V3b_ttc_net_600|lr400_16_1|98.75"] = r
print("WORSE", r, flush=True)
json.dump(out, open("nulls_A.json", "w"), indent=1)
print("done")
