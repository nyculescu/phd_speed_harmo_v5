"""Paired per-seed: does v3w's merge-2 TTC reduction track its reduction of lane-end stops on 4a_0? (descriptive)"""
import sys
sys.path.insert(0, sys.argv[1])
import numpy as np
from scipy.stats import spearmanr
from cd5 import T, V3W
m2 = lambda g: (g.get("m_road_ttc3|4a", 0) + g.get("m_road_ttc3|ramp2", 0)).to_numpy(float)
m1 = lambda g: (g.get("m_road_ttc3|3a", 0) + g.get("m_road_ttc3|ramp1", 0)).to_numpy(float)
for a in ("p333", "lr400_16_1", "MPC-F", "3E-D_TRUCK"):
    o = T[a]
    r2 = [spearmanr(o.end_stop2.to_numpy(float) - T[w].end_stop2.to_numpy(float), m2(o) - m2(T[w]))[0] for w in V3W]
    r1 = [spearmanr(o.end_stop.to_numpy(float) - T[w].end_stop.to_numpy(float), m1(o) - m1(T[w]))[0] for w in V3W]
    # seeds where the lane-end stop difference is small (|d end_stop2| <= 25 vehicle-s): residual merge-2 difference
    res = []
    for w in V3W:
        d = o.end_stop2.to_numpy(float) - T[w].end_stop2.to_numpy(float)
        k = np.abs(d) <= 25
        res.append((k.sum(), float(np.median((m2(o) - m2(T[w]))[k])), float(np.median(m2(o) - m2(T[w])))))
    print(a.ljust(12), "rho(d end_stop2, d merge2 TTC) per learner", " ".join(f"{x:+.2f}" for x in r2),
          "| rho merge1", " ".join(f"{x:+.2f}" for x in r1))
    print(" " * 12, "seeds with |d end_stop2|<=25: n, median d merge2 there, median d merge2 all:", res)
