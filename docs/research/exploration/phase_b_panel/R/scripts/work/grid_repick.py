# EXPLORATORY: confirmatory 3's stored grid rows (7,440,160-179), re-ranked on delay with no close-following bound
import json, collections, numpy as np
f = "/home/catalin/work/phd/v5b1_runs/conf3/tune.jsonl"
T = collections.defaultdict(dict)
with open(f) as h:
    for line in h:
        r = json.loads(line)
        T[r["name"]][r["seed"]] = (float(r["all_delay"]), float(r.get("collisions") or 0), float(r.get("alks_full_events") or 0))
rng = np.random.default_rng(20261110)
for c in ("X1", "X2"):
    ref = T[f"{c}|p333"]; seeds = sorted(ref)
    refmed = np.median([ref[s][0] for s in seeds])
    out = []
    for nm, rows in T.items():
        if not nm.startswith(c + "|") or nm.endswith("|p333"): continue
        d = np.array([(ref[s][0] - rows[s][0]) / refmed * 100 for s in seeds])  # positive = rule has less delay than p333
        b = np.median(d[rng.integers(0, len(d), (10000, len(d)))], axis=1)
        lo, hi = np.percentile(b, [2.5, 97.5])
        out.append((float(np.median(d)), lo, hi, nm.split("|")[1], float(np.median([rows[s][0] for s in seeds])), float(np.mean([rows[s][1] for s in seeds]))))
    out.sort(reverse=True)
    print(f"## {c}: grid rules against p333 on delay, 20 tuning seeds; positive = rule has LESS delay than p333; p333 median {refmed:.0f}; rules {len(out)}")
    for e in out[:10]:
        print(f"  {e[3]:14s} {e[0]:+5.1f} [{e[1]:+5.1f}, {e[2]:+5.1f}]  median {e[4]:.0f}  mean collisions {e[5]:.2f}")
    print("  rules with point > 0:", sum(e[0] > 0 for e in out), "; with CI lower bound > 0:", sum(e[1] > 0 for e in out))
