"""EXPLORATORY, read-only: small per-seed table from the stored S6 rows (cells S and TRUCK). Prints counts only."""
import json, pickle, sys
import numpy as np
ROWS = "/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"
REF = 100.0 / 3.6
T = {}
tot = lambda p: sum(p.values()) if isinstance(p, dict) else float(np.sum(p))
for line in open(ROWS):
    i = line.find('"name": "')
    if i < 0:
        continue
    name = line[i + 9:line.index('"', i + 9)]
    if not name.startswith(("S|", "TRUCK|")):
        continue
    r = json.loads(line)
    vs = {g: tot(p) for g, p in r["m_road_vs"].items()}
    ds = {g: tot(p) for g, p in r["m_road_dist"].items()}
    dl = {g: vs[g] - ds.get(g, 0.0) / REF for g in vs}
    rec = {"d": r["all_delay"], "dl": dl, "ds": ds, "col": r.get("collisions"), "passed": r.get("passed"), "afm": r.get("alks_full_moving"),
           "stuck": r.get("m_stuck_n"), "end2": r.get("end_stop2"), "fin": r.get("finished_pct")}
    if name in ("S|p333", "S|nc"):
        for ln in ("3_0", "4a_1", "3_1", "3_2"):
            rec["v_" + ln] = r["nv_" + ln] / max(r["n_" + ln], 1) * 3.6
            rec["n_" + ln] = r["n_" + ln]
        for x in ("1", "3", "4a", "r2", "rj2"):
            if r.get("lv_n_" + x):
                rec["lv_" + x] = r["lv_sum_" + x] / r["lv_n_" + x]
        rec["ctrl"] = json.dumps(r["cfg"].get("ctrl", {}))[:200]
    T.setdefault(name, {})[r["seed"]] = rec
pickle.dump(T, open(sys.argv[1], "wb"))
print(len(T), "arms;", sorted({len(v) for v in T.values()}), "rows per arm")
print(sorted(k for k in T if k.startswith("S|")))
