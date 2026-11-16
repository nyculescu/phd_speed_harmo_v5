"""EXPLORATORY: scalars for the screen F draft from the stored S6 rows (read-only)."""
import json
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
STRICT = ["all_delay", "ttc_net", "passed", "m_ttc3_all", "m_ttc3_lc", "fuel_km"]
OPT = ["ttc3", "ttc3_r_3", "ttc3_r_4a", "ttc3_r_ramp2", "ttc3_r_rest", "ttc3_s_lo", "ttc3_s_mid", "ttc3_s_hi", "tau_mismatch", "tau_on_n", "tau_on_match"]
ROADS = ("1", "2", "3a", "3", "4a", "4", "5", "ramp1", "ramp2", "junction")
KEYS = STRICT + OPT + [f"rt_{r}" for r in ROADS]
T, groups = {}, set()
for line in open(ROWS):
    r = json.loads(line)
    x = [float(r[k]) for k in STRICT] + [float(r.get(k, 0.0)) for k in OPT]
    rt = r["m_road_ttc3"]
    groups |= set(rt)
    x += [sum(rt.get(g, {}).values()) for g in ROADS]
    T.setdefault(r["name"], {})[r["seed"]] = x
seeds = list(range(7480400, 7480640))
out = {}
for name, d in T.items():
    assert sorted(d) == seeds, (name, len(d))
    out[name] = np.array([d[s] for s in seeds], float)
np.savez("f_scalars.npz", keys=np.array(KEYS), seeds=np.array(seeds), **out)
print(len(out), "arms; road groups seen:", sorted(groups))
