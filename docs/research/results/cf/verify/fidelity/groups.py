import json, sys
import numpy as np
want = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500", "lr400_16_1", "p333", "nc", "3ex2")
n = 480; pos = {s: i for i, s in enumerate(range(7489160, 7489640))}
G = {"merge2": ("4a", "ramp2"), "merge1": ("3a", "ramp1"), "away": ("1", "2", "3", "4", "5")}
X = {g: {a: np.zeros(n) for a in want} for g in list(G) + ["rest", "total"]}
roads = set()
for line in open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/s6_rows.jsonl"):
    head = line[:60]
    if not any(f'"E30|{a}"' in head for a in want): continue
    r = json.loads(line); a = r["arm"]; i = pos[r["seed"]]; t = r["m_road_ttc3"]; roads |= set(t)
    s = lambda ks: sum(sum(t[k].values()) if isinstance(t.get(k), dict) else float(t.get(k, 0)) for k in ks)
    for g, ks in G.items(): X[g][a][i] = s(ks)
    X["total"][a][i] = r["ttc_net"]; X["rest"][a][i] = r["ttc_net"] - sum(X[g][a][i] for g in G)
print("road keys seen", sorted(roads))
V3W = want[:5]; idx = np.random.default_rng(20261108).integers(0, n, (20000, n))
for opp in ("lr400_16_1", "p333", "nc", "3ex2"):
    for g in ("total", "merge2", "merge1", "away", "rest"):
        O = X[g][opp]; m = max(np.median(O), 1e-9); D = [-(X[g][w] - O) / m * 100 for w in V3W]
        b = np.mean([np.median(d[idx], axis=1) for d in D], axis=0); lo, hi = np.percentile(b, (1.25, 98.75))
        print(f"{opp:11s} {g:7s} median opp {np.median(O):7.1f} v3w(mean of learners) {np.median(np.mean([X[g][w] for w in V3W], axis=0)):7.1f}  edge {np.mean([np.median(d) for d in D]):+6.1f} [{lo:+6.1f}, {hi:+6.1f}]  learners {[round(float(np.median(d)), 1) for d in D]}")
