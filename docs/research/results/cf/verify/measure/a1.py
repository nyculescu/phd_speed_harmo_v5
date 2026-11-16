"""Exposure medians per arm and the C-D5 statistic on raw and normalised close-following."""
import sys
sys.path.insert(0, sys.argv[1])
import numpy as np
from cd5 import T, V3W, edge, fmt, df

ARMS = ["lr400_16_1", "p333", "MPC-F", "3E-D_TRUCK", "grid_lr400_13_1", "3E-C_TRUCK", "nc"]
# reproduce the reader first
print("repro E lr400_16_1", fmt(edge("lr400_16_1", "ttc_net")), " away", fmt(edge("lr400_16_1", lambda g: sum(g.get(f"m_road_ttc3|{r}", 0) for r in "12345"))))
keys = ["ttc_net", "E30", "out_E30", "passed", "arrived", "N", "vs", "dist_step", "end_stop", "end_stop2", "m_pending_end", "m_road_vs|pending_main", "m_road_vs|pending_ramp", "m_road_vs|pending_ramp2", "finished_pct", "m_stuck_n", "ttc_half", "teleports", "collisions", "mean_v"]
print("\nmedians (v3w = median of the 5 learners' medians)")
print("arm".ljust(16), " ".join(k[-14:].rjust(14) for k in keys))
def med(a, k):
    return float(np.median(T[a][k])) if k in T[a] else float("nan")
for a in ["v3w"] + ARMS:
    vals = [np.median([med(w, k) for w in V3W]) if a == "v3w" else med(a, k) for k in keys]
    print(a.ljust(16), " ".join(f"{v:14.1f}" for v in vals))
F = {
    "raw ttc_net": "ttc_net",
    "per on-net veh-s (vs)": lambda g: g.ttc_net / g.vs,
    "per N (incl pending)": lambda g: g.ttc_net / g.N,
    "per veh-km (dist_step)": lambda g: g.ttc_net / (g.dist_step / 1000.0),
    "per passed": lambda g: g.ttc_net / g.passed,
    "ttc_half (0.5-s offset sample)": "ttc_half",
    "on-net veh-s (vs)": "vs",
    "veh-km": "dist_step",
    "passed (+ = v3w fewer)": "passed",
}
print("\nC-D5 statistic, positive = v3w lower; 97.5 % percentile interval")
print("measure".ljust(32), " ".join(a.rjust(26) for a in ARMS))
for name, f in F.items():
    print(name.ljust(32), " ".join(fmt(edge(a, f)).rjust(26) for a in ARMS), flush=True)
