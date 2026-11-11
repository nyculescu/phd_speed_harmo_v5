"""Extract the scalar fields the exploratory analysis needs from the S6 rows into one npz (read-only on the rows)."""
import json, sys
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
KEYS = ("all_delay", "ttc_net", "passed", "N", "delay", "arrived", "m_planned_window", "collisions", "m_pending_end", "m_stuck_n", "q", "delay_ramp", "finished_pct")
T = {}
for line in open(ROWS):
    r = json.loads(line)
    cond, name = r["name"].split("|", 1)
    T.setdefault((cond, name), {})[r["seed"]] = [np.nan if r.get(k) is None else float(r[k]) for k in KEYS]
seeds = list(range(7480400, 7480640))
out = {}
for (cond, name), d in T.items():
    assert sorted(d) == seeds, (cond, name, len(d))
    out[f"{cond}|{name}"] = np.array([d[s] for s in seeds])
np.savez("s6_scalars.npz", keys=np.array(KEYS), seeds=np.array(seeds), **out)
print(len(out), "arms", out["TRUCK|nc"].shape)
