"""Size of plan_b_v0 §3.3's stopping threshold delta = max(1, 2 SE) from round 2's 3E-X final runs (40 seeds per candidate):
bootstrap SE of the paired difference in 3E-C-type loss (pooled close-following change vs p333 % + 10 per % delay above +1 %)
between pairs of shortlisted candidates. Planning only."""
import json, itertools
from collections import defaultdict
import numpy as np

for cell in ("x1", "x2"):
    R = defaultdict(dict)
    for line in open(f"/home/catalin/work/phd/v5b1_runs/round2/cma3e_{cell}/final_runs.jsonl"):
        r = json.loads(line)
        R[r["name"]][r["seed"]] = r
    seeds = sorted(R["ref"])
    get = lambda n, k: np.array([R[n][s][k] for s in seeds])
    rt, rd = get("ref", "ttc_net"), get("ref", "all_delay")

    def loss(n, idx):
        t = get(n, "ttc_net")[idx].sum() / rt[idx].sum() * 100 - 100
        d = get(n, "all_delay")[idx].sum() / rd[idx].sum() * 100 - 100
        return t + 10 * max(0.0, d - 1.0)

    rng = np.random.default_rng(1)
    J = rng.integers(0, 40, (4000, 40))
    names = [n for n in R if n != "ref"]
    full = {n: loss(n, np.arange(40)) for n in names}
    print(cell, {n: round(v, 1) for n, v in full.items()})
    ses = []
    for a, b in itertools.combinations(names, 2):
        diffs = np.array([loss(a, j) - loss(b, j) for j in J[:1000]])
        ses.append(diffs.std())
        print(f"  {a} - {b}: diff {full[a]-full[b]:+.1f}, SE {diffs.std():.2f}, delta {max(1, 2*diffs.std()):.1f}")
    print("  median SE", round(float(np.median(ses)), 2), "median delta", round(max(1, 2 * float(np.median(ses))), 1))

# 3E-D-type loss: pooled delay change vs p333 (%), no kink
print("3E-D type (pooled delay change %):")
for cell in ("x1", "x2"):
    R = defaultdict(dict)
    for line in open(f"/home/catalin/work/phd/v5b1_runs/round2/cma3e_{cell}/final_runs.jsonl"):
        r = json.loads(line)
        R[r["name"]][r["seed"]] = r
    seeds = sorted(R["ref"])
    get = lambda n, k: np.array([R[n][s][k] for s in seeds])
    rd = get("ref", "all_delay")
    J = np.random.default_rng(2).integers(0, 40, (2000, 40))
    names = [n for n in R if n != "ref"]
    ses = []
    for a, b in itertools.combinations(names, 2):
        da, db = get(a, "all_delay"), get(b, "all_delay")
        dd = [(da[j].sum() - db[j].sum()) / rd[j].sum() * 100 for j in J]
        ses.append(np.std(dd))
    print(" ", cell, "SE range", round(min(ses), 2), "-", round(max(ses), 2), "median", round(float(np.median(ses)), 2), "-> delta", round(max(1, 2 * float(np.median(ses))), 2))
