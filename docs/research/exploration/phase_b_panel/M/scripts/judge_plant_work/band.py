import json, collections
p = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/rows_band.jsonl"
c = collections.Counter()
with open(p) as f:
    for line in f:
        r = json.loads(line)
        cfg = r.get("cfg", {})
        pert = cfg.get("perturb") or cfg.get("ctrl", {}).get("env", {}).get("perturb")
        if r.get("q") in (5250.0, 6000.0) and str(r.get("name", "")).endswith("p333"):
            c[(r.get("q"), r.get("name"), json.dumps(pert)[:80])] += 1
for k, v in sorted(c.items(), key=str):
    print(k, v)
