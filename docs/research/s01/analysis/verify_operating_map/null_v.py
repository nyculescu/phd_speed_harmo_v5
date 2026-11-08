"""Null of the CI statistic: how often a 95 % percentile bootstrap of the paired median excludes 0 when the true median is 0.
Sign-flip replicates of each comparison's own |differences| (v3w vs p333, the six metrics, every setting)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from lib import ARMS, SETTINGS, SIGN, arm, load  # noqa: E402

T = {k: load(k) for k in ("s1", "band", "test")}
rng = np.random.default_rng(7)
rates = {20: [], 40: []}
for kind, cell, q, lab in SETTINGS:
    for key in SIGN:
        P = arm(T[kind], cell, q, ARMS["v3w"], key)
        O = arm(T[kind], cell, q, ARMS["p333"], key)
        ss = sorted(set(P) & set(O))
        a = np.abs(np.array([P[s] - O[s] for s in ss]))
        n = len(a)
        idx = rng.integers(0, n, (4000, n))
        hits = 0
        R = 300
        for _ in range(R):
            d = a * rng.choice((-1.0, 1.0), n)
            lo, hi = np.percentile(np.median(d[idx], axis=1), (2.5, 97.5))
            hits += lo > 0 or hi < 0
        rates[n].append(hits / R)
for n, r in rates.items():
    print(f"n={n}: {len(r)} comparisons, false-exclusion rate mean {100 * np.mean(r):.1f} % (range {100 * min(r):.1f}-{100 * max(r):.1f} %)")
