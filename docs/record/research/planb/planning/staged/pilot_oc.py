"""Operating characteristic of candidate pilot futility rules (planning only, stored S0 rows as proxy).
Per simulated pilot: n seeds drawn with replacement from a cell's 40 stored seeds; v3w arm vs each of the cell's 14 rules;
effect = sign * median(P - O) / median(O) * 100 (round 2's point estimate). GO if every delay point >= d_min and every
close-following point >= t_min. Scenarios scale v3w's delay and close-following effects by f (as read_power/power.py)."""
import sys
import json
import numpy as np
sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/planb/read_power")
from load_arms import load, METRICS

C = load()
REPS = 4000
out = {}
for cell in ("X1@5300", "X2@5300"):
    A, rules = C[cell]["arms"], C[cell]["rules"]
    for f in (1.0, 0.75, 0.5, 0.25, 0.0):
        P = {}
        for o in rules:
            for k in ("all_delay", "ttc_net"):
                s = METRICS[k]
                ref = float(np.median(A[o][k]))
                d = s * (A["v3w"][k] - A[o][k]) / ref * 100
                P[(o, k)] = d - (1 - f) * float(np.median(d))
        for n in (20, 30):
            rng = np.random.default_rng(20261108 + n)
            idx = rng.integers(0, 40, (REPS, n))
            pd = np.stack([np.median(P[(o, "all_delay")][idx], axis=1) for o in rules], 1)
            pt = np.stack([np.median(P[(o, "ttc_net")][idx], axis=1) for o in rules], 1)
            for dmin in (0.0, 1.0, 2.0):
                for tmin in (0.0, 5.0):
                    go = ((pd >= dmin).all(1) & (pt >= tmin).all(1)).mean()
                    out[f"{cell}|f{f}|n{n}|d{dmin}|t{tmin}"] = round(100 * float(go), 1)
json.dump(out, open("pilot_oc.json", "w"), indent=0)
for cell in ("X1@5300", "X2@5300"):
    for n in (20, 30):
        for dmin in (0.0, 1.0, 2.0):
            for tmin in (0.0, 5.0):
                print(cell, n, dmin, tmin, [out[f"{cell}|f{f}|n{n}|d{dmin}|t{tmin}"] for f in (1.0, 0.75, 0.5, 0.25, 0.0)])
