"""Skeptic re-derivation (read only) of the measure reviewer's numbers from my own extraction."""
import json, pickle, sys
import numpy as np
recs = pickle.load(open("rows.pkl", "rb"))
S = json.load(open("/home/catalin/work/phd/v5b1_runs/cf_remote/cf_screen/screen.json"))
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")
T = {}
for r in recs:
    c, a = r["name"].split("|", 1)
    assert c == "E30"
    T.setdefault(a, {})[r["seed"]] = r
seeds = sorted(T["p333"])
assert all(sorted(T[a]) == seeds for a in T), "seed sets differ"
n = len(seeds); print("arms", len(T), "seeds", n, seeds[0], seeds[-1])
IDX = np.random.default_rng(20261108).integers(0, n, (20000, n))
def rsum(r, key, roads, pers=None):
    out = 0.0
    for g in roads:
        x = r[key].get(g, {})
        out += sum(v for p, v in x.items() if pers is None or p in pers) if isinstance(x, dict) else float(x)
    return out
def col(a, f):
    return np.array([float(f(T[a][s]) if callable(f) else T[a][s][f]) for s in seeds])
def edge(opp, f):
    O = col(opp, f); m = max(float(np.median(O)), 1e-9)
    D = [-(col(w, f) - O) / m * 100.0 for w in V3W]
    pt = float(np.mean([np.median(d) for d in D]))
    b = np.mean([np.median(d[IDX], axis=1) for d in D], axis=0)
    lo, hi = np.percentile(b, (1.25, 98.75))
    return pt, float(lo), float(hi)
fm = lambda x: f"{x[0]:+6.1f} [{x[1]:+6.1f},{x[2]:+6.1f}]"
ALLR = ("1", "2", "3", "3a", "4a", "junction", "ramp1", "ramp2", "4", "5")
away = lambda r: rsum(r, "m_road_ttc3", ("1", "2", "3", "4", "5"))
m1 = lambda r: rsum(r, "m_road_ttc3", ("3a", "ramp1"))
m2 = lambda r: rsum(r, "m_road_ttc3", ("4a", "ramp2"))
ev = lambda r: rsum(r, "m_road_ttc3", ("1", "2"))
btw = lambda r: rsum(r, "m_road_ttc3", ("3",))
jn = lambda r: rsum(r, "m_road_ttc3", ("junction",))
# consistency
bad = sum(1 for r in recs if not (r["ttc3"] == r["ttc_net"] == r["m_ttc3_all"] == rsum(r, "m_road_ttc3", ALLR) == r["E30"] + r["out_E30"]))
badp = sum(1 for r in recs if r["ttc3"] != sum(r[f"ttc3_p_{p}"] for p in ("before", "taper", "hold", "after", "rest")))
bads = sum(1 for r in recs if r["ttc3"] != r["ttc3_s_lo"] + r["ttc3_s_mid"] + r["ttc3_s_hi"])
print("rows inconsistent total/period/speed:", bad, badp, bads, " steps set", {r["steps"] for r in recs}, "commits", {r["commit"] for r in recs})
print("\n1. reader reproduction and location (97.5 %)")
for a in ("lr400_16_1", "grid_lr400_13_1", "p333", "MPC-F"):
    R = S["readings"][a]
    print(a.ljust(16), "E", fm(edge(a, "ttc_net")), "| stored", f"{R['E']['pt']:+.1f} [{R['E']['lo']:+.1f},{R['E']['hi']:+.1f}]",
          "| away", fm(edge(a, away)), "| stored", f"{R['away']['pt']:+.1f} [{R['away']['lo']:+.1f},{R['away']['hi']:+.1f}]", flush=True)
print("\nstored 'away' reading for all competitors (screen.json), and trade points")
for a in S["competitors"] + S["trade_points"]:
    R = S["readings"][a]["away"]; print(" ", a.ljust(18), f"{R['pt']:+6.1f} [{R['lo']:+6.1f},{R['hi']:+6.1f}]", "competitor" if a in S["competitors"] else "trade")
print("\n2. medians by group")
G = {"merge1": m1, "merge2": m2, "between": btw, "event": ev, "junction": jn, "total": "ttc_net"}
med = lambda a, f: float(np.median(col(a, f)))
for a in ("v3w", "lr400_16_1", "grid_lr400_13_1", "p333", "MPC-F", "nc"):
    print(a.ljust(16), " ".join(f"{k} {(np.median([med(w, f) for w in V3W]) if a == 'v3w' else med(a, f)):7.1f}" for k, f in G.items()))
print("\n3. additive mean-difference shares (opp - v3w), all 14 competitors: merge1 merge2 between event | m1+m2")
md = lambda a, f: float(np.mean([np.mean(col(a, f) - col(w, f)) for w in V3W]))
sh = {}
for a in S["competitors"]:
    tot = md(a, "ttc_net"); p = [md(a, f) / tot * 100 for f in (m1, m2, btw, ev)]
    sh[a] = p
    print(" ", a.ljust(16), " ".join(f"{x:6.0f}%" for x in p), f"| {p[0]+p[1]:5.0f}%  total {tot:7.1f}")
print("  range merge2", f"{min(p[1] for p in sh.values()):.0f}-{max(p[1] for p in sh.values()):.0f}", "m1+m2", f"{min(p[0]+p[1] for p in sh.values()):.0f}-{max(p[0]+p[1] for p in sh.values()):.0f}")
print("\n4. E without merge 2, without both merges; group statistics for the two weakest")
exm2 = lambda r: r["ttc_net"] - m2(r)
exm12 = lambda r: r["ttc_net"] - m2(r) - m1(r)
lo2 = []
for a in S["competitors"]:
    e2 = edge(a, exm2); lo2.append(e2[1])
    extra = (" | ex both " + fm(edge(a, exm12)) + " | event " + fm(edge(a, ev)) + " | m1 " + fm(edge(a, m1)) + " | m2 " + fm(edge(a, m2)) + " | between " + fm(edge(a, btw))) if a in ("lr400_16_1", "grid_lr400_13_1", "MPC-F", "p333") else ""
    print(" ", a.ljust(16), "ex m2", fm(e2), extra, flush=True)
print("  smallest lower bound without merge 2:", f"{min(lo2):+.1f}")
