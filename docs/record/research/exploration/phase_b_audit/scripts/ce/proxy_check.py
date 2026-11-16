import json, numpy as np, collections
f = "/home/catalin/work/phd/v5b1_runs/round2/test/rows_6c49e7e.jsonl"
REF = 100/3.6
rat = []; n = 0; names = collections.Counter()
by = collections.defaultdict(dict)
for l in open(f):
    r = json.loads(l); n += 1
    names[r["name"]] += 1
    if "all_delay" in r and "N" in r and "dist" in r:
        p = r["N"] - r["dist"]/REF
        rat.append(p / r["all_delay"])
        by[r["name"]][r["seed"]] = (p, r["all_delay"], r.get("delay"))
rat = np.array(rat)
print(n, "rows;", len(rat), "with keys; proxy/all_delay min, median, max:", rat.min().round(4), np.median(rat).round(4), rat.max().round(4))
print(list(names)[:20])
