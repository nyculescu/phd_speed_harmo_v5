# EXPLORATORY: v3w's close-following (ttc_net) against each stored rule and no control in X1, pooled 120 seeds, 95 %.
import numpy as np
from load import arrays, RULES
L, O, NC, _ = arrays("ttc_net")
a = L.mean(axis=1)
rng = np.random.default_rng(20261110)
ii = rng.integers(0, len(a), (20000, len(a)))
for name, o in [("nc", NC)] + [(r, O[:, j]) for j, r in enumerate(RULES)]:
    d = o - a
    m = np.median(o)
    b = 100 * np.median(d[ii], axis=1) / m
    lo, hi = np.percentile(b, [2.5, 97.5])
    p = 100 * np.median(d) / m
    print(f"{name}: {p:+.1f} [{lo:+.1f}, {hi:+.1f}]{'  HARM' if p < -10 and hi < 0 else ''}")
