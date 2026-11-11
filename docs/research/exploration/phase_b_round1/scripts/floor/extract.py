"""Extract delay components from the S6 rows (read-only). EXPLORATORY."""
import json, pickle
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
ARMS = {"nc", "p333", "w0u250", "w1u500", "w2u250", "w3u500", "w4u500", "os0_10_10", "grid_os1_10_10", "lr1000_10_1", "3E-D_TRUCK"}
SC = ("all_delay", "N", "dist_step", "dist", "vs", "passed", "arrived", "m_planned_window", "m_pending_end", "finished_pct", "delay", "delay_ramp", "delay_ramp2",
      "delay_p95", "m_stuck_n", "m_dropped", "teleports", "collisions", "steps", "q", "delay_s", "m_cong_vs", "end_stop", "end_stop2",
      "m_n_alks", "m_n_car", "m_n_truck", "m_dist_m_alks", "m_dist_m_car", "m_dist_m_truck")
LISTS = ("flow_min", "v20_min", "m_main_pending_min", "m_vh_alks", "m_vh_car", "m_vh_truck")
T = {}
periods = set()
for line in open(ROWS):
    r = json.loads(line)
    cell, arm = r["name"].split("|", 1)
    if arm not in ARMS:
        continue
    d = {k: r.get(k) for k in SC}
    for k in LISTS:
        d[k] = r.get(k)
    d["road_vs"] = r["m_road_vs"]; d["road_dist"] = r["m_road_dist"]
    d["minute"] = r["m_minute"]
    d["offsets"] = r["m_offsets"]
    d["pert"] = r.get("pert_log")
    d["cfg"] = r.get("cfg")
    for g in r["m_road_vs"].values():
        periods |= set(g)
    T.setdefault((cell, arm), {})[r["seed"]] = d
for k, v in T.items():
    assert len(v) == 240, (k, len(v))
print(sorted(T), periods)
pickle.dump(T, open("comp.pkl", "wb"))
