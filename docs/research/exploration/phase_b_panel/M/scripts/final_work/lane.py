"""EXPLORATORY, read-only: lane speeds near merge 2 under p333 (stored S6 rows, cell S) and level use; summaries only."""
import json
import numpy as np
ROWS = "/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"
sp = {k: [] for k in ("3_0", "3_1", "3_2", "4a_1", "4a_3")}; dens = []; on_share = []; lvm = {}
for line in open(ROWS):
    if '"name": "S|p333"' not in line:
        continue
    r = json.loads(line)
    for k in sp:
        if r.get("n_" + k, 0) > 0:
            sp[k].append(3.6 * r["nv_" + k] / r["n_" + k])
    dens.append(r["n_3_0"] / (r["n_3_0"] + r["n_3_1"] + r["n_3_2"]))
    on_share.append(sum(r["m_dec_level_s"]) / max(sum(r["m_dec_level_s"]) + r["m_dec_off_s"], 1))
    for road in ("1", "3", "4a", "r2"):
        lvm.setdefault(road, []).append(r["lv_sum_" + road] / max(r["lv_n_" + road], 1))
print("rows", len(dens))
for k in sp:
    print("lane %s mean speed: median over seeds %.1f km/h (p10 %.1f, p90 %.1f)" % (k, np.median(sp[k]), np.percentile(sp[k], 10), np.percentile(sp[k], 90)))
print("lane 3_0 share of vehicle-seconds on edge 3: %.1f %%" % (100 * np.median(dens)))
print("share of ALKS-seconds with the V2V gate on: median %.1f %%" % (100 * np.median(on_share)))
print("mean level index by road:", {k: round(float(np.median(v)), 2) for k, v in lvm.items()})
