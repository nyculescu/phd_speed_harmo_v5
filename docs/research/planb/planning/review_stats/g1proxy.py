"""G1a proxy (plan_b_v0 §7.3) on confirmatory 3's paired S/H1 rows at 5,300 (H1 = truck cap 50 km/h every 300 s, a weaker
relative of TRUCK rung 1). Paired effect (cell - S) / median(S), 95 % percentile bootstrap, 20,000 resamples."""
import json
from collections import defaultdict
import numpy as np

T = defaultdict(dict)
for f in ("eval_map.jsonl", "eval_primary.jsonl"):
    for line in open("/home/catalin/work/phd/v5b1_runs/conf3/" + f):
        r = json.loads(line)
        if r.get("q") == 5300.0:
            c, a = r["name"].split("|")
            T[(c, a)][r["seed"]] = float(r["all_delay"])
seeds = sorted(T[("S", "p333")])
rng = np.random.default_rng(20261108)
for cell in ("H1", "X1", "X2"):
    for a in ("nc", "p333"):
        c = np.array([T[(cell, a)][s] for s in seeds]); s0 = np.array([T[("S", a)][s] for s in seeds])
        d = (c - s0) / np.median(s0) * 100
        J = rng.integers(0, len(d), (20000, len(d)))
        lo, hi = np.percentile(np.median(d[J], axis=1), [2.5, 97.5])
        print(f"{cell} {a:5s} G1a effect {np.median(d):+6.1f} % [{lo:+.1f}, {hi:+.1f}]  pass(>=10, lo>0): {np.median(d) >= 10 and lo > 0}")
