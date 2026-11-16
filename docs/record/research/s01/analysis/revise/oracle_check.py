"""Own check of the two oracle-gate definitions for X1/X2 ttc_net against no control."""
import json
import sys
import numpy as np

path = sys.argv[1]
ttc = {}
with open(path) as f:
    for line in f:
        r = json.loads(line)
        cell, a = r["name"].split("|")
        if cell not in ("X1", "X2"):
            continue
        ttc[(cell, a, int(r["seed"]))] = float(r["ttc_net"])

W = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
T = [f"t{i}" for i in range(5)]
S = [f"s{i}u500" for i in range(5)]


def stat(p, o):
    d = (o - p) / np.median(o) * 100  # positive = gate has less close-following than nc
    rng = np.random.default_rng(20261104)
    idx = rng.integers(0, len(d), (20000, len(d)))
    bs = np.median(d[idx], axis=1)
    return np.median(d), *np.percentile(bs, (2.5, 97.5))


for cell in ("X1", "X2"):
    seeds = sorted({s for (c, a, s) in ttc if c == cell and a == "nc"})
    nc = np.array([ttc[(cell, "nc", s)] for s in seeds])
    arm_gate, lrn_gate, v3w = [], [], []
    for s in seeds:
        m = [np.mean([ttc[(cell, n, s)] for n in g]) for g in (W, T, S)]
        arm_gate.append(min(m))
        v3w.append(m[0])
        lrn_gate.append(np.mean([min(ttc[(cell, g[i], s)] for g in (W, T, S)) for i in range(5)]))
    print(cell, "n", len(seeds))
    print(" v3w vs nc", np.round(stat(np.array(v3w), nc), 2))
    print(" arm-level gate vs nc", np.round(stat(np.array(arm_gate), nc), 2))
    print(" per-learner gate vs nc", np.round(stat(np.array(lrn_gate), nc), 2))
