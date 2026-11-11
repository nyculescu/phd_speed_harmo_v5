"""EXPLORATORY: headway readback, flow, occupancy and lane-change fields of the S6 rows into one npz. Reads the rows only."""
import json
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
KEYS = ["tau_mismatch", "tau_on_match", "tau_on_n", "passed", "N", "all_delay", "ttc_net", "m_ttc3_all", "m_ttc3_lc", "mean_v", "steps", "end_stop", "end_stop2", "collisions", "alks_full_moving", "fuel_km"]
ROADS = ("1", "2", "3", "3a", "4", "4a", "5", "r", "r2", "rj", "rj2")
T = {}
for line in open(ROWS):
    r = json.loads(line)
    x = [float(r.get(k, np.nan)) for k in KEYS]
    x += [float(sum(r.get(f"lv_sum_{g}", 0.0) for g in ROADS)), float(sum(r.get(f"lv_n_{g}", 0.0) for g in ROADS))]
    T.setdefault(r["name"], {})[r["seed"]] = x
seeds = list(range(7480400, 7480640))
out = {name: np.array([d[s] for s in seeds], float) for name, d in T.items()}
np.savez("/tmp/claude-1000/-srv-shared-Workspace-phd-phd-speed-harmo-v5b1/89ba3663-8e1a-45c3-9415-9e2a743fb16b/scratchpad/phaseB/panel/F/opp_t0.npz", keys=np.array(KEYS + ["lv_sum", "lv_n"]), seeds=np.array(seeds), **out)
print(len(out), "arms", out["TRUCK|nc"].shape)
