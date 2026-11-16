import json, sys, pickle
src = "/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl"
out = {}
keys = None
allkeys = set()
with open(src) as f:
    for line in f:
        r = json.loads(line)
        d = {k: v for k, v in r.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
        for k, v in r.items():
            if k.startswith("m_road") or k.startswith("m_") and isinstance(v, dict):
                d[k] = v
        allkeys |= set(r.keys())
        out[(r["name"], r["seed"])] = d
pickle.dump(out, open(sys.argv[1], "wb"))
print(len(out))
print(sorted(k for k in allkeys if "road" in k or "merge" in k or "stop" in k or "ttc" in k))
