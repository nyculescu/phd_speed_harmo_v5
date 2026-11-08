"""F9 per-learner effects and level shares; F10 stop_gap and gap25."""
import sys
import numpy as np
sys.path.insert(0, "/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/24a0150f-4eb7-443d-8a6d-3d8d8c91d56d/scratchpad/s01/verify_x1_exposure")
from vlib import effect, fmt, g, load, arms_for
T = load()
seeds = list(range(7440840, 7440880))
o = np.array([g(T["X1|nc"][s], "ttc_net") for s in seeds])
for n in arms_for("X1")["v3w"]:
    p = np.array([g(T[f"X1|{n}"][s], "ttc_net") for s in seeds])
    print("X1", n, "ttc_net", fmt(effect(p, o, -1)))
for a in ("p333", "os1_15_10", "3e", "3ex", "v3w"):
    vals = []
    for s in seeds:
        v = [T[f"X1|{n}"][s]["m_dec_level_s"] for n in arms_for("X1")[a]]
        vals.append(np.mean([x[-1] / sum(x) for x in v]))
    print("X1 level_share_on[-1] median", a, round(float(np.median(vals)), 3))
for cell in ("X1", "X2"):
    for a in ("nc", "v3w", "p333"):
        x = np.array([np.mean([g(T[f"{cell}|{n}"][s], "stop_gap") for n in arms_for(cell)[a]]) for s in seeds])
        mx = max(g(T[f"{cell}|{n}"][s], "stop_gap") for n in arms_for(cell)[a] for s in seeds)
        print(cell, a, "stop_gap mean", round(float(x.mean()), 1), "median", float(np.median(x)), "max single run", mx)
print("gap25 max over all rows", max(g(r, "gap25") for A in T.values() for r in A.values()))
