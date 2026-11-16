"""Same null as null_v.py over v3w against p333, 3E-T, os1_15_10 and nc (the analyst's set: 168 + 48 comparisons)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from lib import ARMS, SETTINGS, SIGN, arm, load  # noqa: E402

T = {k: load(k) for k in ("s1", "band", "test")}
rng = np.random.default_rng(11)
rates = {20: [], 40: []}
for kind, cell, q, lab in SETTINGS:
    for key in SIGN:
        P = arm(T[kind], cell, q, ARMS["v3w"], key)
        for o in ("p333", "3e", "os1", "nc"):
            O = arm(T[kind], cell, q, ARMS[o], key)
            ss = sorted(set(P) & set(O))
            a = np.abs(np.array([P[s] - O[s] for s in ss]))
            n = len(a)
            idx = rng.integers(0, n, (4000, n))
            hits = 0
            for _ in range(300):
                d = a * rng.choice((-1.0, 1.0), n)
                lo, hi = np.percentile(np.median(d[idx], axis=1), (2.5, 97.5))
                hits += lo > 0 or hi < 0
            rates[n].append(hits / 300)
for n, r in rates.items():
    print(f"n={n}: {len(r)} comparisons, false-exclusion rate mean {100 * np.mean(r):.1f} % (range {100 * min(r):.1f}-{100 * max(r):.1f} %)")
