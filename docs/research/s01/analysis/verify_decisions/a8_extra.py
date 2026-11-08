"""Missed checks: Spearman among rules only; dilution of whole-run confidence (share of decisions on roads 4-5); rule reversal
shares; traced example; S1 7,000 residual under a linear band fit; v3w reversal share without low-V2V ALKS."""
import numpy as np
from base import *
ST = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st/"
rows, T = load()
def rank(x):
    x = np.asarray(x, float); r = np.empty(len(x)); r[np.argsort(x)] = np.arange(len(x))
    for v in np.unique(x):
        m = x == v; r[m] = r[m].mean()
    return r
learner = {n for v in ARMS.values() for n in v}
ttc = lambda r: g(r, "ttc_net")
for cell in ["X1", "X2"]:
    nc = {s: ttc(r) for s, r in T[(cell, "nc", 5300.0)].items()}
    rules = sorted({a for (c, a, q) in T if c == cell and a != "nc" and a not in learner})
    xs, ys = [], []
    for a in rules:
        e, _ = effect({s: ttc(r) for s, r in T[(cell, a, 5300.0)].items()}, nc)
        xs.append(np.median([derived(r)["share3"] for r in T[(cell, a, 5300.0)].values()])); ys.append(e[0])
    rho = np.corrcoef(rank(xs), rank(ys))[0, 1]
    rng = np.random.default_rng(2); null = np.array([np.corrcoef(rank(xs), rng.permutation(rank(ys)))[0, 1] for _ in range(20000)])
    xs2 = [x for x, a in zip(xs, rules) if a != "copy"]; ys2 = [y for y, a in zip(ys, rules) if a != "copy"]
    rho2 = np.corrcoef(rank(xs2), rank(ys2))[0, 1]
    print(f"{cell}: rules only n={len(rules)} Spearman rho={rho:+.2f} (perm p={np.mean(np.abs(null)>=abs(rho)):.4f}); without copy n={len(xs2)} rho={rho2:+.2f}")
# dilution: share of v3w decisions asked on roads 4-5 ('down') and on 4a ('m2'), X1
for a in ["w0u250", "os1_15_10"]:
    fr = [r["m_dec_place"]["down"][0] / r["m_dec_totals"]["asked"] for r in T[("X1", a, 5300.0)].values()]
    fm = [r["m_dec_place"]["m2"][0] / r["m_dec_totals"]["asked"] for r in T[("X1", a, 5300.0)].values()]
    print(f"{a}: share of asked decisions on roads 4-5 med {np.median(fr):.3f}, on 4a {np.median(fm):.3f}")
# rule reversal shares X1
for a in ["os1_15_10", "3e", "copy", "r4a1", "os0_10_10"]:
    print(a, "rev_share X1 med", round(float(np.median([derived(r)["rev_share"] for r in T[("X1", a, 5300.0)].values()])), 3))
print("v3w rev_share X1 med", round(float(np.median(list(arm_series(T, "X1", ARMS["v3w"], 5300.0, lambda r: derived(r)["rev_share"]).values()))), 3))
# v3w reversal share excluding low-V2V ALKS
vals = []
for s in T[("X1", "nc", 5300.0)]:
    per = []
    for n in ARMS["v3w"]:
        z = np.load(ST + T[("X1", n, 5300.0)][s]["m_st_file"]); D = z["dec"]; L = z["dec_level_s"]
        tot = L.sum(1); hi = ~((L[:, :4].sum(1) < 0.2 * tot) & (tot > 0))
        per.append(D[hi, 4].sum() / D[hi, 1].sum())
    vals.append(np.mean(per))
print("v3w X1 reversal share among ALKS with V2V on >= 20 %:", round(float(np.median(vals)), 3))
# traced example
z = np.load(ST + T[("X2", "w0u250", 5300.0)][7440840]["m_st_file"]); i = list(z["dec_ids"]).index("main.1235")
print("main.1235 dec", z["dec"][i].tolist(), "level_s", z["dec_level_s"][i].tolist())
# S1 7000: linear band fit and fit on the top three band levels
dc = {}
def dens(r):
    k = r["m_st_file"]
    if k not in dc:
        zz = np.load(ST + k); dc[k] = float(zz["n"].sum() / 1500.0 / (zz["n"].shape[1] * 0.05))
    return dc[k]
for k in ["conf_med", "rev_share"]:
    xb, yb, lv = [], [], []
    for q in [4500.0, 5000.0, 5250.0, 5500.0, 6000.0]:
        y = arm_series(T, "B", ARMS["v3w"], q, lambda r: derived(r)[k]); x = arm_series(T, "B", ARMS["v3w"], q, dens)
        for s in y: xb.append(x[s]); yb.append(y[s]); lv.append(q)
    xb, yb, lv = map(np.array, (xb, yb, lv))
    y7 = arm_series(T, "B", ARMS["v3w"], 7000.0, lambda r: derived(r)[k]); x7 = arm_series(T, "B", ARMS["v3w"], 7000.0, dens)
    for lab, m, deg in [("quadratic all", lv > 0, 2), ("linear all", lv > 0, 1), ("linear 5250-6000", lv >= 5250, 1)]:
        c = np.polyfit(xb[m], yb[m], deg)
        print(f"S1 7000 {k} {lab}: residual {fmt(boot_median([y7[s] - np.polyval(c, x7[s]) for s in y7]))}")
