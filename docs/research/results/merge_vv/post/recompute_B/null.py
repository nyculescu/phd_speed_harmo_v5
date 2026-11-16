"""Recomputer B: swap null (sign flip per learner and seed on the per-seed edge, denominator fixed).

Usage: null.py KEY SWAPS RESAMPLES LEVEL RNG
LEVEL 97.5 reads the 1.25/98.75 percentiles, 98.75 the 0.625/99.375 percentiles.
The rate is the mean of the false rates of "lower bound above 0" and "upper bound below 0".
"""
import json
import sys
import time

import numpy as np

HERE = '/home/catalin/work/phd/v5b1_runs/vv_post/recompute_B/'
key, K, BP, level, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), int(sys.argv[5])
d = np.load(HERE + 'edges_B.npz')[key].astype(np.float64)
L, N = d.shape
tail = (100 - level) / 2
rng = np.random.default_rng(seed)
lo_hits = hi_hits = 0
t0 = time.time()
for k in range(K):
    ds = d * rng.choice(np.array([-1.0, 1.0]), size=(L, N))
    idx = rng.integers(0, N, size=(BP, N))
    eff = np.zeros(BP)
    for i in range(L):
        eff += np.median(ds[i][idx], axis=1)
    eff /= L
    lo, hi = np.percentile(eff, [tail, 100 - tail])
    lo_hits += lo > 0
    hi_hits += hi < 0
rate = (lo_hits / K + hi_hits / K) / 2 * 100
out = {'key': key, 'swaps': K, 'resamples': BP, 'level': level, 'rng': seed, 'false_lo': int(lo_hits),
       'false_hi': int(hi_hits), 'rate_pct': rate, 'se_pct': float(np.sqrt(rate / 100 * (1 - rate / 100) / (2 * K)) * 100),
       'seconds': time.time() - t0}
print(json.dumps(out))
with open(HERE + 'nulls_B.jsonl', 'a') as f:
    f.write(json.dumps(out) + '\n')
