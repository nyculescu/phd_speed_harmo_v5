"""EXPLORATORY: stored S6 rows, rules that lengthen headways at a merge against p333 (paired, 240 seeds)."""
import json, sys
from collections import defaultdict
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
ARMS = ("p333", "r4a1", "grid_r4a2", "a4400_10_1", "grid_a41000_10_2", "z33133", "grid_z31333", "os0_10_10", "nc")
REF = 100.0 / 3.6
T = defaultdict(dict)
cfgs = {}
for line in open(ROWS):
    r = json.loads(line)
    cond, nm = r["name"].split("|", 1)
    if nm not in ARMS:
        continue
    vs = {g: (sum(p.values()) if isinstance(p, dict) else float(np.sum(p))) for g, p in r["m_road_vs"].items()}
    ds = {g: (sum(p.values()) if isinstance(p, dict) else float(np.sum(p))) for g, p in r["m_road_dist"].items()}
    dl = lambda g: vs[g] - ds.get(g, 0.0) / REF
    rate = lambda g: dl(g) / max(ds[g] / 1000.0, 1e-9)
    exc = (dl("3a") - rate("2") * ds["3a"] / 1000.0) + (dl("4a") - rate("3") * ds["4a"] / 1000.0) + dl("pending_ramp") + dl("pending_ramp2")
    exc_wide = exc + dl("ramp1") + dl("ramp2") + (dl("4") - rate("5") * ds["4"] / 1000.0)
    T[(cond, nm)][r["seed"]] = (r["all_delay"], r["delay_ramp2"], r["end_stop2"], r["ttc_net"], dl("4a"), dl("ramp2") + dl("pending_ramp2"), dl("3"), 100 * exc / r["all_delay"], 100 * exc_wide / r["all_delay"], r["end_stop"])
    cfgs[nm] = r["cfg"].get("ctrl")
rng = np.random.default_rng(20261110)
def ci(x):
    x = np.asarray(x, float)
    m = np.median(x[rng.integers(0, len(x), (10000, len(x)))], axis=1)
    return np.median(x), np.percentile(m, 2.5), np.percentile(m, 97.5)
for nm in ARMS:
    print(nm, "ctrl:", json.dumps(cfgs[nm])[:160])
seeds = sorted(T[("S", "p333")])
for cond in ("S", "TRUCK"):
    base = np.array([T[(cond, "p333")][s] for s in seeds])
    print(f"\n{cond}: p333 medians all_delay {np.median(base[:,0]):.0f}, 4a delay {np.median(base[:,4]):.0f}, ramp2 road+queue {np.median(base[:,5]):.0f}, end_stop2 {np.median(base[:,2]):.1f}")
    print("   merge excess share narrow %.1f %% [%.1f, %.1f]" % ci(base[:, 7]), "| wide %.1f %% [%.1f, %.1f]" % ci(base[:, 8]))
    for nm in ARMS[1:]:
        a = np.array([T[(cond, nm)][s] for s in seeds])
        d = 100.0 * (base[:, 0] - a[:, 0]) / np.median(base[:, 0])
        m, lo, hi = ci(d)
        d4 = ci(a[:, 4] - base[:, 4]); dr = ci(a[:, 5] - base[:, 5]); es = ci(a[:, 2] - base[:, 2]); d3 = ci(a[:, 6] - base[:, 6])
        print(f"  {nm:17s} delay vs p333 {m:+6.2f} % [{lo:+6.2f}, {hi:+6.2f}] (positive = arm lower); 4a delay {d4[0]:+7.0f} [{d4[1]:+7.0f}, {d4[2]:+7.0f}]; edge 3 {d3[0]:+7.0f} [{d3[1]:+7.0f}, {d3[2]:+7.0f}]; ramp2 road+queue {dr[0]:+6.0f} [{dr[1]:+6.0f}, {dr[2]:+6.0f}]; end_stop2 {es[0]:+6.1f} [{es[1]:+6.1f}, {es[2]:+6.1f}]; merge excess {np.median(a[:,7]):.1f} %")
