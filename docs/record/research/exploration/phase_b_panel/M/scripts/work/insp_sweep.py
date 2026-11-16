import json, collections
F = '/home/catalin/work/phd/v5b1_runs/round1_sweep/out/sweep1.jsonl'
c = collections.Counter()
first = None
for line in open(F):
    r = json.loads(line)
    if first is None:
        first = r
    c[(r.get("name"), r.get("q"))] += 1
print(len(c))
ks = sorted(k for k in first if not isinstance(first[k], (list, dict)))
print(ks[:60])
print({k: first[k] for k in ("name", "q", "seed") if k in first})
names = sorted({str(k[0]) for k in c}); qs = sorted({k[1] for k in c})
print(names); print(qs)
print(sorted(set(c.values())))
