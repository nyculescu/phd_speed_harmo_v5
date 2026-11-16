import json, sys
from collections import defaultdict
import numpy as np
T = defaultdict(lambda: defaultdict(list))
first = None
for line in open(sys.argv[1]):
    r = json.loads(line)
    if first is None:
        first = r
        print("m_ keys:", [k for k in r if k.startswith("m_")][:60])
        if "m_minute" in r:
            print("m_minute keys:", sorted(r["m_minute"]))
    nm = r["name"]
    if nm.split("|")[1] in ("p333", "nc", "os1_15_10"):
        k = (nm, r.get("q"))
        mm = r.get("m_minute") or {}
        for f in ("all_delay", "delay", "delay_ramp", "delay_ramp2", "end_stop", "end_stop2", "finished_pct", "m_pending_end"):
            if r.get(f) is not None:
                T[k][f].append(r[f])
        for f in ("ramp1_pending", "ramp2_pending"):
            if f in mm:
                T[k][f].append(float(np.sum(mm[f])))
        if "m_main_pending_min" in r:
            T[k]["main_pending"].append(float(np.sum(r["m_main_pending_min"])))
for k in sorted(T, key=lambda k: (k[0], k[1] or 0)):
    d = T[k]
    print(f"  {k[0]:12s} q {k[1]} n {len(d['all_delay'])}: " + "; ".join(f"{f} {np.median(v):.1f}" for f, v in d.items()))
