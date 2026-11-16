"""Rule medians of the period counts, to mark printed cells whose denominator is 0 (post hoc, printed items only)."""
import json
import sys
from collections import defaultdict

import numpy as np

vals = defaultdict(list)
with open(sys.argv[1]) as fh:
    for line in fh:
        r = json.loads(line)
        L, arm = r["name"].split("|")
        if arm not in ("lr400_16_1", "grid_lr400_13_1", "p333", "nc"):
            continue
        for p in ("before", "taper", "hold", "after", "rest"):
            vals[(L, arm, p)].append(float(r.get(f"ttc3_p_{p}", 0.0) or 0.0))
for k in sorted(vals):
    v = np.array(vals[k])
    print(*k, "n", len(v), "median", np.median(v), "mean", round(v.mean(), 2))
