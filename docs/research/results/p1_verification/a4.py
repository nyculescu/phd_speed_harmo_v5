import pickle, sys, json, numpy as np
sys.path.insert(0, "/home/catalin/work/phd/p1_frozen_85f7d34")
from v5b.p1 import family as fam
R = pickle.load(open(sys.argv[1], "rb"))
res = json.load(open("/home/catalin/work/phd/v5b1_runs/p1/v99/result.json"))
ARMS = res["tune"]["arms"]
EV = list(range(7400500, 7400600))
def fk(g, inc, q, s): return f"{g}_{inc}_q{q}_s{s}"
def sk(N, a, inc, q, s):
    g, back = fam.parse_action(a); return f"{N}-{g}" + ("+back" if back else "") + f"_{inc}_q{q}_s{s}"
rng = np.random.default_rng(12345)
B = 20000
IDX = rng.integers(0, 100, size=(B, 100))
def rel(r, t, level=1 - 0.05 / 8):
    d = r - t
    m = np.median(d) / np.median(r)
    bd = np.median(d[IDX], axis=1)
    lo, hi = np.quantile(bd, [(1 - level) / 2, 1 - (1 - level) / 2])
    return round(100 * m, 1), round(float(lo), 1), round(float(hi), 1)
for q in (1600, 2000):
    a = ARMS[str(q)]; N = a["N"]
    D = {}
    for inc in ("slow", "block"):
        D[inc] = {x: np.array([R[fk(a[x], inc, q, s)]["delay_s"] for s in EV]) for x in ("N", "FX", "FB", "PI", "AD")}
        D[inc]["NC"] = np.array([R[fk("NC", inc, q, s)]["delay_s"] for s in EV])
        D[inc]["ID"] = np.array([R[sk(N, a["ID"], inc, q, s)]["delay_s"] for s in EV])
        D[inc]["IP"] = np.array([R[sk(N, a["IP"][inc], inc, q, s)]["delay_s"] for s in EV])
        D[inc]["A"] = {x: np.array([R[sk(N, x, inc, q, s)]["delay_s"] for s in EV]) for x in fam.A}
    pooled = {x: np.concatenate([D["slow"]["A"][x], D["block"]["A"][x]]) for x in fam.A}
    idh = min(fam.A, key=lambda x: (np.median(pooled[x]), fam.A.index(x)))
    for inc in ("slow", "block"):
        d = D[inc]
        iph = min(fam.A, key=lambda x: (np.median(d["A"][x]), fam.A.index(x)))
        print(f"== {inc}_q{q}: medians", {x: round(float(np.median(d[x])), 1) for x in ("NC", "N", "FX", "FB", "PI", "AD", "ID", "IP")})
        print("  ID vs L0 (rel %, CI of median diff at 1-.05/8):", {r: rel(d[r], d["ID"]) for r in ("N", "FX", "FB", "PI", "AD")})
        print("  IP vs ID:", rel(d["ID"], d["IP"]))
        print(f"  hindsight pooled ID on eval = {idh}: vs L0", {r: rel(d[r], d["A"][idh])[0] for r in ("N", "FX", "FB", "PI", "AD")},
              " IP vs it:", rel(d["A"][idh], d["IP"]))
        print(f"  hindsight per-cell best action on eval = {iph}: vs L0", {r: rel(d[r], d["A"][iph])[0] for r in ("N", "FX", "FB", "PI", "AD")})
        print("  IP vs L0 (95%):", {r: rel(d[r], d["IP"], 0.95) for r in ("FB", "PI")})
        print("  median(PI-IP) =", round(float(np.median(d["PI"] - d["IP"])), 2), " median(PI)-median(IP) =", round(float(np.median(d["PI"]) - np.median(d["IP"])), 2),
              " share IP<PI", np.mean(d["IP"] < d["PI"]))
