import json, sys, collections
f = "/home/catalin/work/phd/v5b1_runs/conf3/tune.jsonl"
n = 0; names = collections.Counter(); qs = collections.Counter(); seeds = set(); keys = None; conds = collections.Counter()
with open(f) as h:
    for line in h:
        r = json.loads(line); n += 1
        if keys is None:
            keys = sorted(k for k in r if not isinstance(r[k], (list, dict)))
            print("scalar keys:", keys[:80]); print("other keys:", sorted(k for k in r if isinstance(r[k], (list, dict)))[:40])
        nm = r.get("name"); names[nm] += 1; qs[r.get("q")] += 1; seeds.add(r.get("seed"))
        conds[str(nm).split("|")[0]] += 1
print("rows", n, "distinct names", len(names), "q", dict(qs), "seeds", min(seeds), max(seeds), len(seeds))
print("prefix counts", dict(conds))
print(list(names.items())[:12])
