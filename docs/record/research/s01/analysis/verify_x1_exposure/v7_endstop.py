"""Is the 4a TTC excess tied to lane-end stops on the 4a acceleration lane (end_stop2)?"""
import sys
import numpy as np
sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_exposure")
from vlib import fmt, g, load, arms_for, mean_ci
T = load()
seeds = list(range(7440840, 7440880))
def sp(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])
def av(cell, arm, k):
    return np.array([np.mean([g(T[f"{cell}|{n}"][s], k) for n in arms_for(cell)[arm]]) for s in seeds])
for cell in ("X1", "X2"):
    o_t, o_e = av(cell, "nc", "ttc3_r_4a"), av(cell, "nc", "end_stop2")
    o_lo = av(cell, "nc", "ttc3_s_lo")
    print(cell, f"within nc rho(ttc3_r_4a, end_stop2) {sp(o_t, o_e):+.2f}; rho(ttc3_s_lo, end_stop2) {sp(o_lo, o_e):+.2f}")
    # pooled over all 70 arm-cell runs per seed: across arms, arm-level medians
    names = sorted({k.split('|')[1] for k in T if k.startswith(cell + '|')})
    mt = [np.median([g(T[f"{cell}|{n}"][s], "ttc3_r_4a") for s in seeds]) for n in names]
    me = [np.median([g(T[f"{cell}|{n}"][s], "end_stop2") for s in seeds]) for n in names]
    print(cell, f"across {len(names)} arms (medians) rho(ttc3_r_4a, end_stop2) {sp(np.array(mt), np.array(me)):+.2f}")
    for arm in ("v3w", "tail", "sw", "inc", "3e", "p333", "os1_15_10"):
        p_t, p_e = av(cell, arm, "ttc3_r_4a"), av(cell, arm, "end_stop2")
        d_t, d_e = p_t - o_t, p_e - o_e
        rho = sp(d_t, d_e)
        rng = np.random.default_rng(7)
        null = [sp(p_t - o_t[pi], p_e - o_e[pi]) for pi in (rng.permutation(40) for _ in range(3000))]
        # ratio: extra 4a TTC-s per extra lane-end stopped veh-s, against nc's own ratio
        print(f"  {arm}: d end_stop2 {fmt(mean_ci(d_e), 0)} (nc med {np.median(o_e):.0f}); d ttc3_r_4a {fmt(mean_ci(d_t), 0)}; rho(d,d) {rho:+.2f} null med {np.median(null):+.2f} [{np.percentile(null, 2.5):+.2f}, {np.percentile(null, 97.5):+.2f}]; within-arm rho {sp(p_t, p_e):+.2f}")
