"""EXPLORATORY: stored S6 rows, every arm, a few fields (read-only)."""
import json, pickle, sys
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
REF = 100.0 / 3.6
out = {}
for line in open(ROWS):
    r = json.loads(line)
    vs = {g: (sum(p.values()) if isinstance(p, dict) else float(np.sum(p))) for g, p in r["m_road_vs"].items()}
    ds = {g: (sum(p.values()) if isinstance(p, dict) else float(np.sum(p))) for g, p in r["m_road_dist"].items()}
    dl = {g: vs[g] - ds.get(g, 0.0) / REF for g in vs}
    out.setdefault(r["name"], {})[r["seed"]] = dict(d=r["all_delay"], passed=r["passed"], es2=r["end_stop2"], es1=r["end_stop"], ttc=r["ttc_net"], col=r.get("collisions"), dl=dl, ds=ds, stuck=r.get("m_stuck_n"))
pickle.dump(out, open(sys.argv[1], "wb"))
print(len(out), sorted(out)[:80])
