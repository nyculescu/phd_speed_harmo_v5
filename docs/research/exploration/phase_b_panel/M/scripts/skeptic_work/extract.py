"""EXPLORATORY, read-only: per-seed table from the stored S6 rows, cell S. Writes a pickle in the scratchpad; prints counts only."""
import json, pickle
import numpy as np
ROWS = "/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"
REF = 100.0 / 3.6
tot = lambda p: sum(p.values()) if isinstance(p, dict) else float(np.sum(p))
T = {}
for line in open(ROWS):
    i = line.find('"name": "')
    name = line[i + 9:line.index('"', i + 9)]
    if not name.startswith("S|"):
        continue
    r = json.loads(line)
    vs = {g: tot(p) for g, p in r["m_road_vs"].items()}
    ds = {g: tot(p) for g, p in r["m_road_dist"].items()}
    rec = {"d": r["all_delay"], "dl": {g: vs[g] - ds.get(g, 0.0) / REF for g in vs}, "ds": ds, "N": r["N"], "planned": r["m_planned_window"],
           "passed": r["passed"], "col": r["collisions"], "stuck": r["m_stuck_n"], "afm": r.get("alks_full_moving")}
    if name == "S|p333":
        m = r["m_minute"]
        for k in ("m2_up", "m2_acc", "m1_up", "m1_acc"):
            sp = np.array([3.6 * v / n if n > 0 else np.nan for v, n in zip(m[k + "_vs"], m[k + "_n"])])
            rec[k + "_slow"] = int(np.nansum(sp < 60.0)); rec[k + "_nmin"] = len(sp)
    T.setdefault(name[2:], {})[r["seed"]] = rec
pickle.dump(T, open("s.pkl", "wb"))
print(len(T), "arms;", sorted({len(v) for v in T.values()}), "rows per arm")
