"""Alternative: relocation of ramp-2 conflicts onto the 4a acceleration lane (ramp queue, lane-end stops, merge position)."""
import json, sys
import numpy as np
sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_exposure")
from vlib import D, effect, fmt, g, load, arms_for, mean_ci
T = load()
SUM = json.load(open(f"{D}/summary_rows_test.json"))
seeds = list(range(7440840, 7440880))
def av(cell, arm, fn):
    return np.array([np.mean([fn(T[f"{cell}|{n}"][s], SUM[f"{cell}|{n}|5300"][str(s)]) for n in arms_for(cell)[arm]]) for s in seeds])
F = {
 "ramp2_queue_mean": lambda r, sm: sm["ramp2_queue_mean"],
 "ramp2_pending_mean": lambda r, sm: sm["ramp2_pending_mean"],
 "end_stop2": lambda r, sm: g(r, "end_stop2"),
 "m2_ramp_in": lambda r, sm: sum(r["m_minute"]["m2_ramp_in"]),
 "m2_mergepos_mean_decile": lambda r, sm: float(np.dot(np.arange(10) + 0.5, r["m_mergepos_m2"]) / max(sum(r["m_mergepos_m2"]), 1)),
 "m2_acc_vs": lambda r, sm: sum(r["m_minute"]["m2_acc_n"]),
 "pass_merging": lambda r, sm: g(r, "pass_merging"),
}
for cell in ("X1", "X2"):
    for k, fn in F.items():
        p, o = av(cell, "v3w", fn), av(cell, "nc", fn)
        print(cell, k, "nc median", round(float(np.median(o)), 2), "v3w-nc mean", fmt(mean_ci(p - o), 2))
