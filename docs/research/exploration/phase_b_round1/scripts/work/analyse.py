"""EXPLORATORY: where delay sits by road in cell S (stored S6 rows, 240 paired seeds)."""
import pickle, sys
import numpy as np
D = pickle.load(open(sys.argv[1], "rb"))
REF = 100.0 / 3.6
seeds = sorted(D["S|p333"])
rng = np.random.default_rng(20261110)

def ci(x, lo=2.5, hi=97.5):
    x = np.asarray(x, float)
    idx = rng.integers(0, len(x), (10000, len(x)))
    m = np.median(x[idx], axis=1)
    return np.median(x), np.percentile(m, lo), np.percentile(m, hi)

def groups(r):
    vs = {g: sum(p.values()) if isinstance(p, dict) else float(np.sum(p)) for g, p in r["m_road_vs"].items()}
    ds = {g: sum(p.values()) if isinstance(p, dict) else float(np.sum(p)) for g, p in r["m_road_dist"].items()}
    return vs, ds

r0 = D["S|p333"][seeds[0]]
vs, ds = groups(r0)
print("q", {D["S|p333"][s]["q"] for s in seeds}, "groups vs", sorted(vs), "dist", sorted(ds))
print("check seed0: sum vs", round(sum(vs.values())), "N", round(r0["N"]), "sum delay", round(sum(vs.values()) - sum(ds.values()) / REF), "all_delay", round(r0["all_delay"]))

def table(arm):
    rows = D[arm]
    G = {}
    tot, share = [], {}
    for s in seeds:
        vs, ds = groups(rows[s])
        t = sum(vs.values()) - sum(ds.values()) / REF
        tot.append(t)
        for g in vs:
            d = vs[g] - ds.get(g, 0.0) / REF
            G.setdefault(g, []).append(d)
            share.setdefault(g, []).append(100.0 * d / t)
            if g in ds:
                G.setdefault("rate_" + g, []).append(d / max(ds[g] / 1000.0, 1e-9))
    return tot, G, share

for arm in ("S|nc", "S|p333", "S|os0_10_10"):
    tot, G, share = table(arm)
    print(f"\n{arm}: road-sum delay median {np.median(tot):.0f}; all_delay median {np.median([D[arm][s]['all_delay'] for s in seeds]):.0f}")
    for g in sorted(share):
        m, lo, hi = ci(share[g])
        rate = f"; s per veh-km {np.median(G['rate_' + g]):.2f}" if "rate_" + g in G else ""
        print(f"  {g:16s} delay median {np.median(G[g]):9.0f} veh-s; share {m:5.1f} % [{lo:5.1f}, {hi:5.1f}]{rate}")
    merge = [sum(share[g][i] for g in share if g in ("3a", "4a", "ramp1", "ramp2", "pending_ramp", "pending_ramp2")) for i in range(len(seeds))]
    print("  merge roads + ramps + ramp insertion queues: share %.1f %% [%.1f, %.1f]" % ci(merge))
    for k in ("delay", "delay_ramp", "delay_ramp2", "end_stop", "end_stop2", "halt_3a_0", "m_pending_end", "passed", "m_planned_window"):
        x = [D[arm][s][k] for s in seeds if D[arm][s][k] is not None]
        print(f"  {k}: median {np.median(x):.2f}, mean {np.mean(x):.2f}, p90 {np.percentile(x, 90):.2f}, n {len(x)}")

# paired: where p333's gain over no control sits
tn, Gn, _ = table("S|nc")
tp, Gp, _ = table("S|p333")
print("\np333 - nc paired delay difference by road (veh-s; negative = p333 lower):")
for g in sorted(k for k in Gp if not k.startswith("rate_")):
    d = np.array(Gp[g]) - np.array(Gn[g])
    print(f"  {g:16s} %9.0f [%9.0f, %9.0f]" % ci(d))
print("  total            %9.0f [%9.0f, %9.0f]" % ci(np.array(tp) - np.array(tn)))
