import json, numpy as np
p = "/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"
out = {"S|p333": [], "S|nc": []}
with open(p) as f:
    for line in f:
        if '"name": "S|p333"' not in line and '"name": "S|nc"' not in line:
            continue
        r = json.loads(line)
        if r["name"] not in out:
            continue
        alks = sum(v for k, v in r.items() if k.startswith("lv_n_"))
        row = {"gate_on": r.get("tau_on_n", float("nan")) / alks if alks else float("nan"),
               "on_match": r.get("tau_on_match", float("nan")) / max(r.get("tau_on_n", 0), 1),
               "mismatch": r.get("tau_mismatch", float("nan")),
               "v_3_0": r["nv_3_0"] / max(r["n_3_0"], 1) * 3.6, "v_4a_1": r["nv_4a_1"] / max(r["n_4a_1"], 1) * 3.6,
               "share_3_0": r["n_3_0"] * (r["nv_3_0"] / max(r["n_3_0"], 1)) / sum(r["nv_3_%d" % i] for i in range(3)),
               "lvl_3": r.get("lv_sum_3", float("nan")) / max(r.get("lv_n_3", 1), 1), "end_stop2": r.get("end_stop2"), "finished": r.get("finished_pct")}
        out[r["name"]].append(row)
for a, rows in out.items():
    print(a, len(rows), {k: round(float(np.nanmedian([x[k] for x in rows])), 3) for k in rows[0]})
