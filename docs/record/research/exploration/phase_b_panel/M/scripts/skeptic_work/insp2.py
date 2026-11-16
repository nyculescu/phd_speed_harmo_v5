"""EXPLORATORY, read-only: band rows at 6,000 veh/h: arm names, where the perturbation spec sits, which seeds have no slowdown. Names and counts only."""
import json, collections
p = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_band.jsonl"
names = collections.Counter(); spec = collections.Counter(); logs = {}
first = None
for line in open(p):
    r = json.loads(line)
    if r.get("q") != 6000.0:
        continue
    names[r["name"]] += 1
    c = r["cfg"]
    first = first or {k: (v if not isinstance(v, (dict, list)) else "...") for k, v in c.items()}
    e = c.get("ctrl", {}).get("env", {})
    spec[json.dumps({k: e[k] for k in e if "pert" in k})[:200]] += 1
    pl = r.get("pert_log")
    if r["name"].endswith("p333"):
        logs[r["seed"]] = (len(pl) if isinstance(pl, list) else pl, json.dumps(pl)[:160])
print("arms:", sorted(names), len(names))
print("cfg top:", first)
print("env pert spec:", dict(spec))
for s in sorted(logs):
    print(s, logs[s])
