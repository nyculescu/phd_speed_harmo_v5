"""EXPLORATORY: side-constraint scalars from the stored S6 rows (read-only). Fields read as read6.derive does."""
import json
import numpy as np
ROWS = '/home/catalin/work/phd/v5b1_runs/planb_s56_remote/s6/s6_rows.jsonl'
ROBUST_BIN = {"car": 2, "alks": 2, "truck": 1}
KEYS = ["collisions", "alks_full_moving", "pending_end", "stuck_n", "all_delay", "ttc_net", "passed", "robust_rate"]
T = {}
for line in open(ROWS):
    r = json.loads(line)
    ev = sum(sum(r[f"m_peak_{c}"][b:]) for c, b in ROBUST_BIN.items())
    km = sum(r[f"m_dist_m_{c}"] for c in ROBUST_BIN) / 1000.0
    x = [float(r["collisions"]), float(r.get("alks_full_moving") or 0.0), float(r["m_pending_end"]), float(r["m_stuck_n"]),
         float(r["all_delay"]), float(r["ttc_net"]), float(r["passed"]), 1000.0 * ev / km if km > 0 else 0.0]
    T.setdefault(r["name"], {})[r["seed"]] = x
seeds = list(range(7480400, 7480640))
out = {}
for name, d in T.items():
    assert sorted(d) == seeds, (name, len(d))
    out[name] = np.array([d[s] for s in seeds], float)
np.savez("k4_scalars.npz", keys=np.array(KEYS), **out)
print(len(out), "arms")
