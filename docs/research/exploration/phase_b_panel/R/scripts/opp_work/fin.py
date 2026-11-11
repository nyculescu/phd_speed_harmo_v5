"""EXPLORATORY: share of planned vehicles finished by 1,800 s in X1, round 2 test rows (already read)."""
import sys
import numpy as np
sys.path.insert(0, "/srv/shared/Workspace/phd/phd_speed_harmo_v5b1/docs/research/exploration/phase_b_round1/scripts/x1x2")
from lib import RUNS, load
T = load(RUNS + "round2/test/rows_6c49e7e.jsonl")
for c in ("X1", "X2"):
    for a in ("nc", "p333", "os0_10_10", "lr1000_10_1", "w0u250", "w3u500"):
        k = (f"{c}|{a}", 5300.0)
        if k not in T:
            print(c, a, "absent"); continue
        v = [r.get("finished_pct") for r in T[k].values() if r.get("finished_pct") is not None]
        fm = [np.mean(r["flow_min"][-10:]) for r in T[k].values() if r.get("flow_min")]
        print(c, a, "n", len(v), "finished % median", round(float(np.median(v)), 1), "last-10-min flow veh/min median", round(float(np.median(fm)), 1) if fm else None)
names = sorted({n for (n, q) in T if n.startswith("X1|")})
print(len(names), names[:30])
