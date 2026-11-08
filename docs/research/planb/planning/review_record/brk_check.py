"""Verify plan_b_v0 §5's stored robust braking excess per vehicle-km (v3w arm vs each rule, X1/X2 at 5,300), 95 % percentile bootstrap."""
import pickle, sys
import numpy as np
cells = pickle.load(open(sys.argv[1], "rb"))
rng = np.random.default_rng(20261108)
for cell, C in cells.items():
    A, rules = C["arms"], C["rules"]
    n = len(C["seeds"])
    J = rng.integers(0, n, (20000, n))
    out = []
    for o in rules:
        p, q = A["v3w"]["ev4_vkm"], A[o]["ev4_vkm"]
        d = p - q
        pt = -np.median(d) / np.median(q) * 100
        bs = -np.median(d[J], axis=1) / np.median(q) * 100
        out.append((pt, np.percentile(bs, 2.5), np.percentile(bs, 97.5), o))
    out.sort()
    print(cell, n, len(rules))
    for r in out[:4]:
        print("  %.1f [%.1f, %.1f] %s" % r)
