"""EXPLORATORY: scalar safety and smoothness fields of every S6 row into one npz. Reads the rows only."""
import json
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
CNT0 = ["ttc3", "ttc2", "ttc15", "sev3"] + [f"{m}_{s}" for m in ("ttc3", "ttc2", "ttc15", "sev3") for s in ("s_lo", "s_mid", "s_hi", "r_3", "r_4a", "r_ramp2", "r_rest", "p_before", "p_trucks", "p_rest")] + ["alks_full_events", "alks_full_moving", "alks_full_creep", "pass_lane_change", "end_stop2"]
STRICT = ["all_delay", "passed", "N", "vs", "ttc_net", "ttc_half", "E15", "E30", "out_E30", "brake_net", "brake3", "brake45", "out_b3", "b45_net", "b7_net", "b3_step", "b45_step", "b7_step", "alks_b3_step", "alks_b45_step", "alks_b7_step", "free_brake_alks", "free_brake_alks_step", "gap25", "stop_gap", "a2", "jerk", "jerk_step", "fuel_km", "undertakes", "pass_straight", "pass_merging", "pass_side_by_side", "end_stop", "halt_3a_0", "contact_steps", "collisions", "teleports", "m_stuck_n", "m_ttc3_all", "m_ttc3_lc", "m_cong_vs", "m_cong_vs_nc", "dist", "m_planned_window"]
CLS = ("car", "alks", "truck")
ROADS = ("1", "2", "3a", "3", "4a", "4", "5", "ramp1", "ramp2", "junction")
KEYS = STRICT + CNT0
for c in CLS:
    KEYS += [f"ev_{c}", f"ev45_{c}", f"ev7_{c}", f"casc_{c}", f"evs_{c}", f"a2_{c}", f"n_{c}", f"mild_{c}", f"fuel_{c}", f"dist_{c}", f"low7_{c}", f"dur2_{c}"]
KEYS += ["robust_raw"] + [f"rt_{r}" for r in ROADS] + [f"rb_{r}" for r in ROADS]
T = {}
absent = {k: 0 for k in CNT0}
for line in open(ROWS):
    r = json.loads(line)
    x = [float(r[k]) for k in STRICT]
    for k in CNT0:
        if k not in r:
            absent[k] += 1
        x.append(float(r.get(k, 0.0)))
    for c in CLS:
        pk, ah, vh, du = r[f"m_peak_{c}"], r[f"m_ah_{c}"], r[f"m_vh_{c}"], r[f"m_dur_{c}"]
        # mild: -3 <= a < -1.5 m/s² vehicle-steps (bins 14-16); low7: vehicle-steps below 25 km/h (bins 0-4); dur2: events of 2 s or longer
        x += [r[f"m_events_{c}"], sum(pk[3:]), sum(pk[6:]), r[f"m_cascade_{c}"], r[f"m_event_s_{c}"], r[f"m_a2_{c}"], r[f"m_n_{c}"], sum(ah[14:17]), r[f"m_fuel_mg_{c}"], r[f"m_dist_m_{c}"], sum(vh[:5]), sum(du[3:])]
    rr = r["m_robust_road"]
    x.append(sum(v for g in rr.values() for v in g.values()))
    x += [sum(r["m_road_ttc3"].get(g, {}).values()) for g in ROADS]
    x += [sum(rr.get(g, {}).values()) for g in ROADS]
    T.setdefault(r["name"], {})[r["seed"]] = x
seeds = list(range(7480400, 7480640))
out = {}
for name, d in T.items():
    assert sorted(d) == seeds, (name, len(d))
    out[name] = np.array([d[s] for s in seeds], float)
np.savez("s6_safety.npz", keys=np.array(KEYS), seeds=np.array(seeds), **out)
print(len(out), "arms", out["TRUCK|nc"].shape, "absent counts (read as 0):", {k: v for k, v in absent.items() if k in ("ttc3", "ttc2", "ttc15", "sev3", "alks_full_events", "alks_full_moving", "alks_full_creep", "end_stop2")})
