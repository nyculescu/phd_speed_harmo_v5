"""Read-only extraction of the fields the metric audit needs. EXPLORATORY."""
import json, pickle, sys
RUNS = "/home/catalin/work/phd/v5b1_runs/"
SC = ("all_delay", "N", "dist_step", "dist", "vs", "passed", "arrived", "m_planned_window", "m_pending_end", "finished_pct", "delay", "delay_ramp", "delay_ramp2",
      "delay_p95", "m_stuck_n", "m_dropped", "teleports", "collisions", "contact_steps", "steps", "q", "delay_s", "end_stop", "end_stop2", "halt_3a_0", "halt_3a_1",
      "m_n_alks", "m_n_car", "m_n_truck", "m_dist_m_alks", "m_dist_m_car", "m_dist_m_truck", "alks_full_events", "alks_full_creep", "alks_full_moving", "stop_gap", "mean_v")
LISTS = ("flow_min", "m_main_pending_min", "m_capped")
def ext(path, arms, out):
    T = {}
    with open(path) as h:
        for line in h:
            r = json.loads(line)
            cell, arm = r["name"].split("|", 1)
            if arm not in arms:
                continue
            d = {k: r.get(k) for k in SC}
            for k in LISTS:
                d[k] = r.get(k)
            d["road_vs"] = r.get("m_road_vs"); d["road_dist"] = r.get("m_road_dist"); d["minute"] = r.get("m_minute")
            d["pert"] = r.get("pert_log"); d["cell_spec"] = r.get("cell_spec")
            T.setdefault((cell, arm), {})[r["seed"]] = d
    for k, v in sorted(T.items()):
        print(k, len(v), min(v), max(v))
    pickle.dump(T, open(out, "wb"))
W2 = {"w0u250", "w1u500", "w2u250", "w3u500", "w4u500"}
which = sys.argv[1]
if which == "s6":
    ext(RUNS + "planb_s56_remote/s6/s6_rows.jsonl", {"nc", "p333", "os0_10_10", "3E-C_TRUCK", "3E-D_TRUCK", "lr1000_10_1"} | W2, "s6.pkl")
elif which == "r2t":
    ext(RUNS + "round2/test/rows_6c49e7e.jsonl", {"nc", "p333", "os0_10_10", "3ex1", "3ex2", "lr1000_10_1"} | W2, "r2t.pkl")
elif which == "s01":
    ext(RUNS + "measure_s01_remote/rows_test.jsonl", {"nc", "p333", "os0_10_10", "3ex1", "3ex2", "lr1000_10_1"} | W2, "s01.pkl")
elif which == "r2v":
    ext(RUNS + "round2/val/rows_6c49e7e.jsonl", {"nc", "p333", "os0_10_10", "3ex1", "3ex2", "lr1000_10_1", "w0u250", "w1u250", "w2u500", "w3u500", "w4u500"}, "r2v.pkl")
elif which == "r1":
    ext(RUNS + "round1_remote/out/test/test.jsonl", {"nc", "p333", "os0_10_10", "lr1000_10_1", "w0", "w1", "w2", "w3", "w4"}, "r1.pkl")
