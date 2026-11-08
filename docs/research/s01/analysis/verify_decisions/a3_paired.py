"""D3, D4, D6, D7: asked cadence; X1 minus X2 paired for policy and rule arms; ttc_net effects; Spearman across arms."""
import numpy as np, json
from base import *
ST = "/home/catalin/work/phd/v5b1_runs/measure_s01_remote/st/"
rows, T = load()
ncomp = 0
# D3 asked per ALKS over all cells, ignored for policies
for a in ["p333", "os1_15_10", "3e", "copy", "w0u250", "t0", "d0u500", "s0u500"]:
    rs = [r for (c, aa, q), tab in T.items() if aa == a for r in tab.values()]
    print(f"D3 {a:10s} asked/ALKS med all cells {np.median([derived(r)['asked_pv'] for r in rs]):.1f}  X1 {np.median([derived(r)['asked_pv'] for r in T[('X1',a,5300.0)].values()]):.1f}  max ignored {max(derived(r)['ignored'] for r in rs)}  applied X1 med {np.median([derived(r)['applied'] for r in T[('X1',a,5300.0)].values()]):.3f}")
dens_cache = {}
def dens(r):
    k = r["m_st_file"]
    if k not in dens_cache:
        z = np.load(ST + k); dens_cache[k] = float(z["n"].sum() / 1500.0 / (z["n"].shape[1] * 0.05))
    return dens_cache[k]
GROUPS = {**ARMS, "p333": ["p333"], "os1_15_10": ["os1_15_10"], "3e": ["3e"], "copy": ["copy"]}
KEYS = ["conf_med", "conf_lt05", "ent", "rev_share", "applied", "excess_pv", "chg_pv", "share3", "gap_on", "on_share", "s3_abs"]
res = {}
print("\nX1 minus X2, paired median [95% CI], arm value per seed = mean over learners")
for gname, names in GROUPS.items():
    line = []
    for k in KEYS + ["dens"]:
        f = (lambda r, k=k: derived(r)[k]) if k != "dens" else dens
        A = arm_series(T, "X1", names, 5300.0, f); B = arm_series(T, "X2", names, 5300.0, f)
        if any(np.isnan(list(A.values()))): continue
        (t, n) = paired_diff(A, B); ncomp += 1
        res[(gname, k)] = t
        line.append(f"{k} {fmt(t, 3 if k not in ('dens','s3_abs') else 1)}")
    print(f"  {gname}: n={n}; " + "; ".join(line))
# levels: X1 and X2 medians of share3
for gname in ["v3w", "tail", "sw", "bv3"]:
    A = arm_series(T, "X1", GROUPS[gname], 5300.0, lambda r: derived(r)["share3"]); B = arm_series(T, "X2", GROUPS[gname], 5300.0, lambda r: derived(r)["share3"])
    print(f"  share3 {gname}: X1 med {boot_median(list(A.values()))}, X2 med {boot_median(list(B.values()))}")
# D7 ttc_net effects
print("\nD7 ttc_net, round-2 effect (sign -1; negative = more close-following in P)")
ttc = lambda r: g(r, "ttc_net")
nc1 = {s: ttc(r) for s, r in T[("X1", "nc", 5300.0)].items()}; nc2 = {s: ttc(r) for s, r in T[("X2", "nc", 5300.0)].items()}
for gname in ["v3w", "tail", "sw", "bv3", "p333", "os1_15_10", "3e", "copy", "nc"]:
    names = GROUPS.get(gname, [gname])
    A = arm_series(T, "X1", names, 5300.0, ttc); B = arm_series(T, "X2", names, 5300.0, ttc)
    e12, n = effect(A, B); ncomp += 1
    s = f"  {gname:10s} X1 vs X2 {fmt(e12,1)} (med X1 {np.median(list(A.values())):.0f}, X2 {np.median(list(B.values())):.0f})"
    if gname != "nc":
        e1, _ = effect(A, nc1); e2, _ = effect(B, nc2); ncomp += 2
        s += f"; vs nc X1 {fmt(e1,1)}; X2 {fmt(e2,1)}"
    print(s)
# delay check
dl = lambda r: g(r, "all_delay")
A = arm_series(T, "X1", ARMS["v3w"], 5300.0, dl); print("  v3w X1 all_delay vs nc", fmt(effect(A, {s: dl(r) for s, r in T[("X1","nc",5300.0)].items()})[0], 3))
# Spearman across controlled arms (single arms: every non-nc arm name expanded? use groups of learners as one arm)
def rank(x):
    x = np.asarray(x); o = np.argsort(x); r = np.empty(len(x)); r[o] = np.arange(len(x))
    # ties average
    for v in np.unique(x):
        m = x == v; r[m] = r[m].mean()
    return r
for cell in ["X1", "X2"]:
    arms_single = sorted({a for (c, a, q) in T if c == cell and a != "nc"})
    pooled = {k: v for k, v in GROUPS.items() if k in ARMS}
    learner = {n for v in ARMS.values() for n in v}
    units = {**pooled, **{a: [a] for a in arms_single if a not in learner}}
    xs, ys, labs = [], [], []
    ncell = {s: ttc(r) for s, r in T[(cell, "nc", 5300.0)].items()}
    for u, names in units.items():
        A = arm_series(T, cell, names, 5300.0, ttc)
        e, _ = effect(A, ncell)
        s3 = np.median(list(arm_series(T, cell, names, 5300.0, lambda r: derived(r)["share3"]).values()))
        xs.append(s3); ys.append(e[0]); labs.append(u)
    rho = np.corrcoef(rank(xs), rank(ys))[0, 1]
    # permutation null for rho
    rng = np.random.default_rng(1); ry = rank(ys); rx = rank(xs)
    null = np.array([np.corrcoef(rx, rng.permutation(ry))[0, 1] for _ in range(20000)])
    print(f"  Spearman share3 vs ttc effect, {cell}: n_arms={len(xs)} rho={rho:+.2f}, two-sided permutation p={np.mean(np.abs(null) >= abs(rho)):.3f}")
    print("   ", ", ".join(f"{l}:{x:.2f}/{y:+.0f}" for l, x, y in sorted(zip(labs, xs, ys), key=lambda t: t[1])))
print("comparisons in this script:", ncomp)
