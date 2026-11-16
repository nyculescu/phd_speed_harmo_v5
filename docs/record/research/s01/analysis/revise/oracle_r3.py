"""Round-3 re-check of the oracle gates and the 3E-T reference row (ttc_net vs no control, positive = fewer)."""
import json
import numpy as np

ROWS = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_test.jsonl"
W = ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"]
T = [f"t{i}" for i in range(5)]
S = [f"s{i}u500" for i in range(5)]

ttc = {}
with open(ROWS) as f:
    for line in f:
        r = json.loads(line)
        cell, arm = r["name"].split("|")
        ttc[(cell, arm, r["seed"])] = float(r["ttc_net"])
arms = sorted({a for _, a, _ in ttc})
print("arms:", arms)


def ci(p, o):
    ref = np.median(o)
    d = -(p - o) / ref * 100
    idx = np.random.default_rng(20261104).integers(0, len(d), (20000, len(d)))
    lo, hi = np.percentile(np.median(d[idx], axis=1), (2.5, 97.5))
    return round(float(np.median(d)), 1), round(float(lo), 1), round(float(hi), 1), len(d)


for cell in ("X1", "X2"):
    seeds = sorted(s for c, a, s in ttc if c == cell and a == "nc")
    o = np.array([ttc[(cell, "nc", s)] for s in seeds])
    g = lambda names: np.array([[ttc[(cell, n, s)] for n in names] for s in seeds])
    w, t, s_ = g(W), g(T), g(S)
    v3w = w.mean(1)
    arm_gate = np.minimum.reduce([v3w, t.mean(1), s_.mean(1)])
    learner_gate = np.minimum.reduce([w, t, s_]).mean(1)
    e3 = np.array([ttc[(cell, "3e", s)] for s in seeds])
    print(cell, "v3w", ci(v3w, o))
    print(cell, "arm-level gate", ci(arm_gate, o))
    print(cell, "per-learner gate", ci(learner_gate, o))
    print(cell, "3E-T", ci(e3, o))
