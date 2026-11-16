"""EXPLORATORY: where the extra emergency braking sits in the M2 pick rows (means per run, 60 seeds)."""
import json, collections
import numpy as np
R = collections.defaultdict(list)
for line in open('/home/catalin/work/phd/v5b1_runs/v505_remote/m2_pick/s6_rows.jsonl'):
    r = json.loads(line); R[r["name"]].append(r)
names = sorted(R); print("arms:", names)
r0 = R[names[0]][0]
ks = [k for k in r0 if any(s in k for s in ("full", "end_stop", "b45", "b7", "ttc_net", "all_delay", "passed", "m_road_b", "m_events", "alks_past"))]
print("keys:", ks[:40])
def mean(name, k):
    v = [x.get(k) for x in R[name]]
    v = [np.sum(y) if isinstance(y, list) else y for y in v if y is not None]
    return float(np.mean(v)) if v else float("nan")
show = [k for k in ks if isinstance(r0[k], (int, float))][:16]
for n in names:
    print(n, {k: round(mean(n, k), 2) for k in show})
for k in ks:
    if isinstance(r0[k], dict):
        print("dict key", k, list(r0[k].keys())[:12])
