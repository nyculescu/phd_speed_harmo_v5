"""EXPLORATORY: per-road delay split of stored S6 rows, cell S (read-only on the rows)."""
import json, pickle, sys
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
WANT = ("S|nc", "S|p333", "S|os0_10_10", "S|grid_os1_10_10", "TRUCK|p333", "TRUCK|nc")
names, out = {}, {}
with open(ROWS) as f:
    for line in f:
        r = json.loads(line)
        n = r["name"]
        names[n] = names.get(n, 0) + 1
        if n in WANT or n.startswith("S|v3w") or n.startswith("S|w"):
            out.setdefault(n, {})[r["seed"]] = {k: r.get(k) for k in ("q", "all_delay", "delay", "delay_ramp", "delay_ramp2", "end_stop", "end_stop2", "m_road_vs", "m_road_dist", "m_planned_window", "N", "dist_step", "passed", "arrived", "halt_3a_0", "m_pending_end", "m_minute", "m_mergepos_m1", "m_mergepos_m2", "n_3_0", "n_3_1", "n_3_2", "nv_3_0", "nv_3_1", "nv_3_2", "ttc_net", "m_road_ttc3")}
pickle.dump(out, open(sys.argv[1], "wb"))
print(sorted(names.items()))
