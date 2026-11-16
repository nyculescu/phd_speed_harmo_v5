"""EXPLORATORY: where on acceleration lane 4a vehicles leave lane 0, and lane-end stops, by arm. S6 rows, read-only."""
import json
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
ARMS = {"nc", "p333", "grid_r4a2", "r4a1", "os0_10_10", "w0u250", "w1u500", "w2u250", "w3u500", "w4u500"}
T = {}
for line in open(ROWS):
    r = json.loads(line)
    cell, arm = r["name"].split("|", 1)
    if arm in ARMS and cell in ("S",):
        T.setdefault(arm, {})[r["seed"]] = (np.array(r["m_mergepos_m2"], float), float(r["end_stop2"]), np.array(r["m_mergepos_m1"], float), float(r["all_delay"]))
seeds = sorted(T["p333"])
assert len(seeds) == 240
IDX = np.random.default_rng(20261110).integers(0, 240, (10_000, 240))
def ci(d):
    b = np.median(d[IDX], axis=1); return "%+.2f [%+.2f, %+.2f]" % (np.median(d), *np.percentile(b, (2.5, 97.5)))
def late(arm, k=2, j=0):
    return np.array([100 * T[arm][s][j][-k:].sum() / max(T[arm][s][j].sum(), 1) for s in seeds])
print("bins", len(T["p333"][seeds[0]][0]), "merges per run at m2, p333 median", np.median([T["p333"][s][0].sum() for s in seeds]))
ref = late("p333")
print("p333: share of merge-2 lane changes in the last 2 of 10 bins, median %.2f %%; last bin %.2f %%; merge 1 last 2 bins %.2f %%" % (np.median(ref), np.median(late("p333", 1)), np.median(late("p333", 2, 2))))
for a in ("nc", "grid_r4a2", "r4a1", "os0_10_10"):
    print(a, "last-2-bin share median %.2f %%; arm minus p333, points:" % np.median(late(a)), ci(late(a) - ref), "| last bin:", ci(late(a, 1) - late("p333", 1)))
v = np.mean([late(a) for a in ARMS if a.startswith("w")], axis=0)
print("v3w (mean of 5) last-2-bin share median %.2f %%; minus p333:" % np.median(v), ci(v - ref))
e = lambda a: np.array([T[a][s][1] for s in seeds])
print("end_stop2 medians:", {a: float(np.median(e(a))) for a in ("nc", "p333", "grid_r4a2", "r4a1", "os0_10_10")}, "v3w", float(np.median(np.mean([e(a) for a in ARMS if a.startswith('w')], axis=0))))
