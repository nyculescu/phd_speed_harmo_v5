"""EXPLORATORY: stored S6 arms that lengthen headways near a merge, against p333. Paired, median of paired differences, 95 % bootstrap CI (10,000, rng 20261110)."""
import json
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
ARMS = ["p333", "grid_z31333", "z33133", "r4a1", "grid_r4a2", "a4400_10_1", "grid_a41000_10_2", "copy", "os0_10_10", "os1_15_10", "os1_10_0"]
REF = 100 / 3.6
T = {}; cfgs = {}
for line in open(ROWS):
    r = json.loads(line)
    cell, arm = r["name"].split("|", 1)
    if arm in ARMS:
        d = {"all_delay": r["all_delay"], "ttc": r["ttc_net"], "passed": r["passed"]}
        for g in ("3a", "3", "4a", "4", "5", "1", "2", "ramp1", "ramp2"):
            d[g] = sum(r["m_road_vs"].get(g, {}).values()) - sum(r["m_road_dist"].get(g, {}).values()) / REF
        T.setdefault((cell, arm), {})[r["seed"]] = d
        cfgs[arm] = r["cfg"]["ctrl"]
seeds = list(range(7480400, 7480640)); n = 240
IDX = np.random.default_rng(20261110).integers(0, n, (10_000, n))
def col(cell, arm, k): return np.array([T[(cell, arm)][s][k] for s in seeds])
def pct(a, b):     # positive = arm has MORE than p333, % of p333's median
    d = (a - b) / np.median(b) * 100; bs = np.median(d[IDX], axis=1); lo, hi = np.percentile(bs, (2.5, 97.5)); return "%+.2f [%+.2f, %+.2f]" % (np.median(d), lo, hi)
for a in ARMS: print(a, json.dumps({k: v for k, v in cfgs[a].items() if k != "env"}))
for cell in ("S", "TRUCK"):
    print("#####", cell, "arm minus p333, % of p333's median; positive = the arm has more")
    for a in ARMS[1:]:
        print(f" {a}: all_delay {pct(col(cell,a,'all_delay'), col(cell,'p333','all_delay'))} %; close-following {pct(col(cell,a,'ttc'), col(cell,'p333','ttc'))} %; delay on 3 {pct(col(cell,a,'3'), col(cell,'p333','3'))}, on 4a {pct(col(cell,a,'4a'), col(cell,'p333','4a'))}, on 3a {pct(col(cell,a,'3a'), col(cell,'p333','3a'))}, ramp2 {pct(col(cell,a,'ramp2'), col(cell,'p333','ramp2'))}; medians all_delay {np.median(col(cell,a,'all_delay')):.0f} vs {np.median(col(cell,'p333','all_delay')):.0f}")
