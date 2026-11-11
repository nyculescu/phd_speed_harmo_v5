# EXPLORATORY: does a stored-row T0 record exist for r2m3? u0 (1.6 s) against p333 (0.8 s), confirmatory 3 tuning rows
import json, collections, numpy as np
f = "/home/catalin/work/phd/v5b1_runs/conf3/tune.jsonl"
T = collections.defaultdict(dict)
keys = ("tau_on_match", "tau_on_n", "passed", "mean_v", "all_delay", "end_stop2", "q")
with open(f) as h:
    for line in h:
        r = json.loads(line)
        if r["name"].split("|")[-1] in ("u0", "p333", "os0_10_10", "lr1000_10_1"):
            T[r["name"]][r["seed"]] = {k: r.get(k) for k in keys}
rng = np.random.default_rng(20261110)
def ci(d):
    b = np.median(d[rng.integers(0, len(d), (10000, len(d)))], axis=1)
    return np.median(d), *np.percentile(b, [2.5, 97.5])
print("names:", sorted(T))
for c in ("S", "X1", "X2"):
    a, b = T.get(f"{c}|u0"), T.get(f"{c}|p333")
    if not a or not b:
        print(c, "missing"); continue
    seeds = sorted(set(a) & set(b))
    print(c, "seeds", len(seeds), seeds[0], seeds[-1], "q", {a[s]["q"] for s in seeds})
    for n, R in (("u0", a), ("p333", b)):
        m = [R[s]["tau_on_match"] / R[s]["tau_on_n"] for s in seeds if R[s]["tau_on_n"]]
        print(f"  {n}: tau_on_match/tau_on_n median {np.median(m):.4f} min {min(m):.4f} (n rows {len(m)})")
    for k in ("passed", "mean_v", "all_delay"):
        d = np.array([a[s][k] - b[s][k] for s in seeds], float)
        ref = np.median([b[s][k] for s in seeds])
        p, lo, hi = ci(d / ref * 100)
        print(f"  u0 minus p333, {k}: {p:+.1f} % [{lo:+.1f}, {hi:+.1f}] (95 %)")
for c in ("X1",):
    for n in ("p333", "os0_10_10", "lr1000_10_1", "u0"):
        R = T.get(f"{c}|{n}")
        if R:
            print(f"  {c} {n}: end_stop2 median {np.median([R[s]['end_stop2'] for s in R]):.0f}")
