import json, sys, hashlib, pickle
from collections import Counter, defaultdict
rows_path, out = sys.argv[1], sys.argv[2]
keep = ("seed","passed","arrived","N","E30","out_E30","ttc_net","all_delay","b45_step","collisions","teleports","m_stuck_n","m_dropped",
        "tau_on_n","tau_on_match","tau_mismatch","wall_s","q","steps","commit","ctrl_sha256","cell","arm","learner","m_ttc3_all","delay_s","m_pending_end","finished_pct","vs")
R = []
nkeys = Counter()
for line in open(rows_path):
    r = json.loads(line)
    d = {k: r.get(k) for k in keep}
    d["name"] = r["name"]
    d["cfg_sha"] = hashlib.sha256(json.dumps(r["cfg"], sort_keys=True).encode()).hexdigest()
    d["cell_spec"] = json.dumps(r.get("cell_spec"), sort_keys=True)
    d["pert_log"] = r.get("pert_log")
    d["alks_sha"] = (r.get("c1_t0") or {}).get("alks_sha")
    d["veh_n"] = (r.get("c1_t0") or {}).get("veh_n")
    d["road_ttc3_sum"] = sum(sum(x.values()) if isinstance(x, dict) else x for x in r.get("m_road_ttc3", {}).values())
    d["away"] = sum(sum(x.values()) if isinstance(x, dict) else x for k, x in r.get("m_road_ttc3", {}).items() if k in ("1","2","3","4","5"))
    d["ge45"] = sum(sum(r[f"m_peak_{c}"][3:]) for c in ("car","alks","truck"))
    d["lv"] = {rd: (r.get(f"lv_sum_{rd}"), r.get(f"lv_n_{rd}")) for rd in ("2","3","4","5")}
    m = r["m_minute"]
    d["q"] = {k: sum(m[k][i]/60.0 for i in range(20,25))/5 for k in ("ramp1_queue","ramp2_queue")}
    d["q"]["backlog"] = sum((m["ramp1_pending"][i]+m["ramp2_pending"][i]+r["m_main_pending_min"][i])/60.0 for i in range(20,25))/5
    d["files"] = json.dumps(r.get("files"), sort_keys=True)
    d["nkeys"] = len(r)
    d["m_capped"] = len(r.get("m_capped") or [])
    R.append(d)
pickle.dump(R, open(out, "wb"))
print(len(R))
