"""EXPLORATORY, read-only: own per-seed table from the stored S6 rows, cell S. Writes a pickle in the scratchpad; prints counts only."""
import json, pickle
import numpy as np
ROWS = "/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl"
REF = 100.0 / 3.6
def tot(p):
    return float(sum(p.values())) if isinstance(p, dict) else float(np.sum(p))
T = {}
for line in open(ROWS):
    i = line.find('"name": "')
    name = line[i + 9:line.index('"', i + 9)]
    if not name.startswith("S|"):
        continue
    r = json.loads(line)
    vs = {g: tot(p) for g, p in r["m_road_vs"].items()}
    ds = {g: tot(p) for g, p in r["m_road_dist"].items()}
    rec = dict(d=r["all_delay"], vs=vs, ds=ds, N=r["N"], planned=r["m_planned_window"], passed=r["passed"], col=r["collisions"],
               stuck=r["m_stuck_n"], afm=r.get("alks_full_moving"), end2=r.get("end_stop2"), tm=r.get("tau_mismatch"))
    if name in ("S|p333", "S|nc"):
        m = r["m_minute"]
        for k in ("m2_up", "m2_acc", "m1_up", "m1_acc"):
            v, n = np.array(m[k + "_vs"], float), np.array(m[k + "_n"], float)
            sp = np.where(n > 0, 3.6 * v / np.maximum(n, 1e-9), np.nan)
            rec[k + "_slow"] = int(np.nansum(sp < 60.0)); rec[k + "_nmin"] = len(sp)
        rec["r2pend"] = float(np.sum(m["ramp2_pending"])); rec["r1pend"] = float(np.sum(m["ramp1_pending"]))
    T.setdefault(name[2:], {})[r["seed"]] = rec
pickle.dump(T, open("mine.pkl", "wb"))
print(len(T), "arms;", sorted({len(v) for v in T.values()}), "rows per arm;", sorted(T))
