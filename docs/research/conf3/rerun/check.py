"""Exact reproduction: every numeric key of each base rerun against the stored evaluation row; the added TTC total against ttc3."""
import json, sys
O = "/home/catalin/work/phd/v5b1_runs/conf3/"
S = {(r["name"], r["seed"]): r for r in map(json.loads, open(O + "eval_primary.jsonl")) if r["q"] == 5300.0}
bad, n, keys = [], 0, 0
for r in map(json.loads, open(sys.argv[1])):
    o = S[(r["name"], r["seed"])]
    n += 1
    for k, v in o.items():
        if isinstance(v, (int, float)) and k not in ("wall",):
            keys += 1
            if r.get(k) != v:
                bad.append((r["name"], r["seed"], k, v, r.get(k)))
    for k in ("flow_min", "v20_min", "pert_log", "lv"):
        if k in o and o[k] != r.get(k):
            bad.append((r["name"], r["seed"], k))
    if r["extra"].get("ttc_all", 0) + r["extra"].get("late_ttc_all", 0) != r["ttc3"]:
        bad.append((r["name"], r["seed"], "added TTC total", r["ttc3"], r["extra"].get("ttc_all")))
print("rows", n, "numeric keys compared", keys, "mismatches", len(bad), bad[:6])
