"""Own extraction of the confirmation rows (read only): scalars plus per-road, per-period maps."""
import json, pickle, sys
src, out = sys.argv[1], sys.argv[2]
SC = ["ttc_net", "E30", "out_E30", "passed", "arrived", "N", "vs", "dist_step", "end_stop", "end_stop2", "ttc_half", "ttc3", "ttc2", "ttc15", "sev3",
      "ttc3_s_lo", "ttc3_s_mid", "ttc3_s_hi", "ttc3_p_before", "ttc3_p_taper", "ttc3_p_hold", "ttc3_p_after", "ttc3_p_rest", "m_ttc3_all", "m_ttc3_lc",
      "b45_step", "all_delay", "m_pending_end", "m_stuck_n", "collisions", "teleports", "steps", "halt_3a_0", "ttc3_r_4a", "ttc3_r_ramp2", "ttc3_r_3", "ttc3_r_rest"]
recs, keysets = [], {}
for line in open(src):
    r = json.loads(line)
    d = {"name": r["name"], "seed": r["seed"], "pert": r.get("pert_log"), "commit": r.get("commit")}
    for k in SC:
        d[k] = float(r.get(k) or 0.0)
    for key in ("m_road_ttc3", "m_road_vs"):
        d[key] = r.get(key) or {}
        for road in d[key]:
            keysets.setdefault(key, set()).add(road)
    for k in r:
        if k.startswith(("ttc3_r_", "ttc3_p_", "ttc3_s_")):
            keysets.setdefault("flat", set()).add(k)
    recs.append(d)
pickle.dump(recs, open(out, "wb"))
print(len(recs), {k: sorted(v) for k, v in keysets.items()})
