"""EXPLORATORY. V382 T0 rows (10 seeds 7,440,065-074): arms against p333, two delay keys. Positive = arm better."""
import json, numpy as np, collections
F = '/home/catalin/work/phd/v5b1_runs/conf3/t0/prerun.jsonl'
T = collections.defaultdict(dict); has = collections.Counter()
for line in open(F):
    r = json.loads(line)
    T[r["name"]][r["seed"]] = (r.get("all_delay"), r.get("delay"), r.get("passed"), r.get("q"))
    has['all_delay' in r] += 1
print("rows with all_delay key:", dict(has))
names = sorted(T)
print(len(names), "names; seeds per name", sorted(set(len(v) for v in T.values())), "seed range", min(min(v) for v in T.values()), max(max(v) for v in T.values()))
rng = np.random.default_rng(20261110)
def eff(a, o):
    d = a - o; n = len(d)
    idx = rng.integers(0, n, size=(10000, n))
    pt = -np.median(d) / np.median(o) * 100
    bs = -np.median(d[idx], axis=1) / np.median(o[idx], axis=1) * 100
    return f"{pt:+.1f} [{np.percentile(bs,2.5):+.1f}, {np.percentile(bs,97.5):+.1f}]"
conds = sorted(set(n.split("|")[0] for n in names))
for c in conds:
    ref = T.get(f"{c}|p333")
    if not ref: print(c, "no p333", [n for n in names if n.startswith(c)][:12]); continue
    seeds = sorted(ref)
    print("==", c, "n", len(seeds), "q", set(ref[s][3] for s in seeds))
    for n in names:
        if not n.startswith(c + "|") or n.endswith("|p333"): continue
        if sorted(T[n]) != seeds: print("  ", n, "seed mismatch"); continue
        out = []
        for j in (0, 1):
            a = np.array([T[n][s][j] for s in seeds], float); o = np.array([ref[s][j] for s in seeds], float)
            out.append(eff(a, o))
        print("  ", n.split("|", 1)[1], "| all_delay", out[0], "| finishers' delay", out[1])
