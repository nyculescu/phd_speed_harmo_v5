"""Post hoc, descriptive: where the 'rest' samples (edges 2 and 3) sit in the V1 traces, by period and distance to the edge end."""
import json
import sys
from collections import Counter

import numpy as np

L = {"2": 498.3, "3": 1194.3}


def per(t, o, d):
    return "before" if t < o else "taper" if t < o + 20 else "hold" if t < o + d else "after" if t < o + d + 120 else "rest"


for line in open(sys.argv[1]):
    r = json.loads(line)
    if not r["name"].endswith("~trace"):
        continue
    o, d = r["pert_log"][0][1], r["pert_log"][0][2]
    out = {}
    for e in ("2", "3"):
        s = [x for x in r["vv_trace"] if x[5] == e]
        if s:
            dist = [L[e] - x[7] for x in s]
            out[e] = {"n": len(s), "period": dict(Counter(per(x[0], o, d) for x in s)), "dist_to_end_q25_50_75": [round(float(q)) for q in np.percentile(dist, (25, 50, 75))],
                      "share_within_150m_of_end": round(float(np.mean(np.array(dist) < 150)), 2), "follower_speed_med_kmh": round(float(np.median([x[15] for x in s])) * 3.6, 1)}
    print(r["name"].replace("~trace", ""), r["seed"], out)
