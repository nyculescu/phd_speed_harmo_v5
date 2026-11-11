import json, glob, collections
c = collections.Counter(); names = collections.defaultdict(set); seeds = collections.defaultdict(set)
for p in glob.glob("/home/catalin/work/phd/v5b1_runs/planb_s34_remote/s3a/*.jsonl"):
    with open(p) as f:
        for line in f:
            r = json.loads(line)
            cell = r.get("cell") or str(r.get("name", "")).split("|")[0]
            c[cell] += 1; names[cell].add(r.get("arm") or r.get("name")); seeds[cell].add(r.get("seed"))
for k in c:
    print(k, c[k], "rows;", len(names[k]), "rules;", len(seeds[k]), "seeds", min(seeds[k]), max(seeds[k]))
