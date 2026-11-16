"""Severity, speed band, period and lane-change shares; C-D5 statistic on each; end_stop2 vs merge-2 counts."""
import sys
sys.path.insert(0, sys.argv[1])
import numpy as np
from cd5 import T, V3W, edge, fmt
ARMS = ["lr400_16_1", "p333", "MPC-F", "3E-D_TRUCK", "grid_lr400_13_1", "3E-C_TRUCK"]
mild = lambda g: g.ttc3 - g.ttc2
F = {"ttc3 (all, = ttc_net)": "ttc3", "mild 2<=TTC<3": mild, "ttc2 (<2 s)": "ttc2", "ttc15 (<1.5 s)": "ttc15", "sev3 DRAC>=3": "sev3",
     "ttc3 speed lo <5 m/s": "ttc3_s_lo", "ttc3 speed mid 5-10": "ttc3_s_mid", "ttc3 speed hi >=10": "ttc3_s_hi",
     "ttc3 period before": "ttc3_p_before", "ttc3 taper+hold": lambda g: g.ttc3_p_taper + g.ttc3_p_hold, "ttc3 after (120 s)": "ttc3_p_after", "ttc3 rest": "ttc3_p_rest",
     "lane-change related (m_ttc3_lc)": "m_ttc3_lc", "not lc": lambda g: g.m_ttc3_all - g.m_ttc3_lc,
     "end_stop2 (+ = v3w fewer)": "end_stop2", "end_stop (merge1)": "end_stop", "ttc2 at 4a": "ttc2_r_4a", "ttc15 at 4a": "ttc15_r_4a", "sev3 at 4a": "sev3_r_4a"}
def med(a, f):
    x = f(T[a]) if callable(f) else T[a][f]
    return float(np.median(x))
print("medians".ljust(32), " ".join(a[:12].rjust(12) for a in ["v3w"] + ARMS))
for name, f in F.items():
    vals = [np.median([med(w, f) for w in V3W])] + [med(a, f) for a in ARMS]
    print(name.ljust(32), " ".join(f"{v:12.1f}" for v in vals))
print("\nC-D5 statistic (positive = v3w lower), 97.5 %")
print("measure".ljust(32), " ".join(a.rjust(26) for a in ARMS))
for name, f in F.items():
    print(name.ljust(32), " ".join(fmt(edge(a, f)).rjust(26) for a in ARMS), flush=True)
# within-arm relation between end-of-lane stops and merge-2 close-following
print("\nSpearman(end_stop2, merge2 TTC samples) per arm, and merge-2 TTC per end_stop2 tercile (median)")
from scipy.stats import spearmanr
m2 = lambda g: g.get("m_road_ttc3|4a", 0) + g.get("m_road_ttc3|ramp2", 0)
for a in V3W[:2] + tuple(ARMS):
    g = T[a]
    x, y = g.end_stop2.to_numpy(float), m2(g).to_numpy(float)
    q = np.quantile(x, [1/3, 2/3])
    t = [np.median(y[x <= q[0]]), np.median(y[(x > q[0]) & (x <= q[1])]), np.median(y[x > q[1]])]
    print(a.ljust(16), f"rho {spearmanr(x, y)[0]:+.2f}", " terciles", " ".join(f"{v:7.1f}" for v in t))
