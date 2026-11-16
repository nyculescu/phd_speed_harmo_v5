"""Independent re-derivation of P1 (page docs/research/protocols/p1_incident_information.md, V99 + Addendum).
Reads only the slim per-run records (recs.pkl, built from the run JSONs by load.py). Does not import v5b code.
Usage: rederive.py recs.pkl out.json BOOTMODE   (BOOTMODE: 'page' = rng(20261019).integers(0,n,(B,n)) as I12;
'own' = an independent rng seed, to see Monte Carlo sensitivity)."""
import json, pickle, sys
import numpy as np

recs = pickle.load(open(sys.argv[1], "rb"))
OUT, MODE = sys.argv[2], sys.argv[3]
B = 20_000
SEED = 20261019 if MODE == "page" else 987654321

# ------------------------------------------------------------- families (page §2, A5(a))
RATES = [400, 600, 800] + list(range(1000, 2601, 100))
CONST = [f"c{r}" for r in RATES]
FEEDBACK = [f"f{k}_{n}" for k in (10, 20, 40, 70, 120) for n in (6, 8, 10, 12, 14, 16)]
G = CONST + FEEDBACK
A = G + [g + "+back" for g in G]
PI = [f"p{kp}_{ki}_{n}_{e}" for e, ns in (("e4", (6, 8, 10, 12, 14, 16)), ("e5", (2, 4, 6, 8, 10, 12)))
      for kp in (20, 40, 70) for ki in (10, 20, 40, 70, 120) for n in ns]
ETA = ["0p5", "1", "2"]
assert len(G) == 50 and len(A) == 100 and len(PI) == 180
QS = (1600.0, 2000.0)
INC = ("slow", "block")
L0 = ("N", "FX", "FB", "PI", "AD")
TUNE = list(range(7400200, 7400240))
EVAL = list(range(7400500, 7400600))

# ------------------------------------------------------------- index by in-file spec
IX = {}
for r in recs:
    key = (r["pre"], r["post"], bool(r["back"]), r["incident"], float(r["q"]), int(r["seed"]), int(r["k"]),
           float(r["d"]), float(r["c"]), bool(r["fa"]))
    assert key not in IX, key
    IX[key] = r


def fixed(g, inc, q, s, k=0):
    return IX[(g, None, False, inc, q, s, k, 0.0, 0.0, False)]


def sw(N, a, inc, q, s, k=0, d=0.0, c=0.0):
    back = a.endswith("+back")
    g = a[:-5] if back else a
    return IX[(N, g, back, inc, q, s, k, float(d), float(c), False)]


def fa(N, g, q, s):
    return IX[(N, g, False, "none", q, s, 0, 0.0, 0.0, True)]


def has_fixed(g, inc, q, s):
    return (g, None, False, inc, q, s, 0, 0.0, 0.0, False) in IX


def med(x):
    return float(np.median(np.asarray(x, float)))


def best(cands, vals):
    """lowest median; ties to the earlier candidate"""
    return min(cands, key=lambda c: (med(vals[c]), cands.index(c)))


# ------------------------------------------------------------- tuning re-derivation (page §2)
arms = {}
for q in QS:
    none = {g: [fixed(g, "none", q, s)["delay_s"] for s in TUNE] for g in G}
    pooled = {g: [fixed(g, i, q, s)["delay_s"] for i in INC for s in TUNE] for g in G + PI}
    N = best(G, none)
    FX = best(CONST, pooled)
    FB = best(FEEDBACK, pooled)
    PIa = best(PI, pooled)
    ADc = [f"ad{e}_{FB}" for e in ETA]
    ADv = {a: [fixed(a, i, q, s)["delay_s"] for i in INC for s in TUNE] for a in ADc}
    AD = best(ADc, ADv)
    per = {i: {a: [sw(N, a, i, q, s)["delay_s"] for s in TUNE] for a in A} for i in INC}
    IP = {i: best(A, per[i]) for i in INC}
    ID = best(A, {a: per["slow"][a] + per["block"][a] for a in A})
    # prevalence re-tuning (page §6; D5(a): AD over eta with the main FB)
    fams = {"N": G, "FX": CONST, "FB": FEEDBACK, "PI": PI, "AD": ADc}
    prev = {}
    for pi in (0.1, 0.25, 0.5):
        prev[pi] = {}
        for arm, cand in fams.items():
            mix = {g: [pi * (fixed(g, "slow", q, s)["delay_s"] + fixed(g, "block", q, s)["delay_s"]) / 2
                       + (1 - pi) * fixed(g, "none", q, s)["delay_s"] for s in TUNE] for g in cand}
            prev[pi][arm] = best(list(cand), mix)
    arms[q] = {"N": N, "FX": FX, "FB": FB, "PI": PIa, "AD": AD, "ID": ID, "IP": IP, "prev": prev}

# ------------------------------------------------------------- statistics (page §5)
_idx = {}


def idx(n):
    if n not in _idx:
        _idx[n] = np.random.default_rng(SEED).integers(0, n, size=(B, n))
    return _idx[n]


def paired(r, t, level, mean=False):
    r, t = np.asarray(r, float), np.asarray(t, float)
    f = np.mean if mean else np.median
    d = r - t
    I = idx(len(r))
    bd, br = f(d[I], axis=1), f(r[I], axis=1)
    lo, hi = 50 * (1 - level), 50 * (1 + level)
    return {"n": len(r), "ref": float(f(r)), "treat": float(f(t)), "diff": float(f(d)), "rel": float(f(d) / f(r)),
            "diff_ci": [float(np.percentile(bd, lo)), float(np.percentile(bd, hi))],
            "rel_ci": [float(np.percentile(bd / br, lo)), float(np.percentile(bd / br, hi))]}


L_S1, L_S2, L95 = 1 - 0.05 / 8, 1 - 0.05 / 4, 0.95


def rule(st):
    return {"a": st["rel"] >= 0.10 and st["diff_ci"][0] > 0, "b": st["rel"] >= -0.05}


# ------------------------------------------------------------- break-even (page §4, I8)
def crossing(M, grid, kind):
    """M: (..., G). Returns value, flag (0 crossing, 1 never ahead, 2 > max)."""
    M = np.atleast_2d(M)
    g = np.asarray(grid, float)
    vals, flags = np.empty(M.shape[0]), np.empty(M.shape[0], int)
    for j in range(M.shape[0]):
        m = M[j]
        nz = np.nonzero(m <= 0)[0]
        if len(nz) == 0:
            vals[j], flags[j] = g[-1], 2
        elif nz[0] == 0:
            vals[j], flags[j] = g[0], 1
        else:
            i = nz[0]
            if kind == "first":
                vals[j] = g[i]
            else:
                vals[j] = g[i - 1] + (g[i] - g[i - 1]) * m[i - 1] / (m[i - 1] - m[i])
            flags[j] = 0
    return vals, flags


FL = {0: "crossing", 1: "IP never ahead", 2: "> max"}


def breakeven(X, grid, kind):
    """X = {arm: (n, G) per-seed L0 - IP(x)}"""
    per = {}
    for a in L0:
        v, f = crossing(np.median(X[a], axis=0), grid, kind)
        per[a] = (float(v[0]), FL[int(f[0])], [float(x) for x in np.median(X[a], axis=0)])
    bind = min(L0, key=lambda a: (per[a][0], L0.index(a)))
    n = X["N"].shape[0]
    I = idx(n)
    allv, allf = [], []
    for a in L0:
        Mb = np.concatenate([np.median(X[a][I[s:s + 500]], axis=1) for s in range(0, B, 500)])  # (B, G)
        v, f = crossing(Mb, grid, kind)
        allv.append(v)
        allf.append(f)
    allv, allf = np.array(allv), np.array(allf)
    k = np.argmin(allv, axis=0)
    vb, fb = allv[k, np.arange(B)], allf[k, np.arange(B)]
    return {"value": per[bind][0], "flag": per[bind][1], "binding": bind,
            "per_arm": {a: {"value": per[a][0], "flag": per[a][1], "M": per[a][2]} for a in L0},
            "ci": [float(np.percentile(vb, 2.5)), float(np.percentile(vb, 97.5))],
            "share_gt_max": float(np.mean(fb == 2)), "share_never": float(np.mean(fb == 1))}


# ------------------------------------------------------------- evaluation
D_GRID, C_GRID = (0.0, 30.0, 60.0, 120.0, 240.0), (0.0, 60.0, 180.0)
P_GRID = [round(0.01 * i, 2) for i in range(101)]
LAST = 40.0 + 900.0 - 1.0
res = {"arms": {str(int(q)): {k: (v if k != "prev" else {str(p): x for p, x in v.items()}) for k, v in a.items()}
                for q, a in arms.items()}, "cells": {}, "checks": {}}
chk = res["checks"]
chk["n_invalid_eval"] = sum(1 for r in recs if 7400500 <= r["seed"] <= 7400599 and not r["valid"])
chk["n_teleport_eval"] = sum(1 for r in recs if 7400500 <= r["seed"] <= 7400599 and (r["teleports"] or 0) > 0)
chk["n_undrained_eval"] = sum(1 for r in recs if 7400500 <= r["seed"] <= 7400599 and not r["drained"])


def imperfect(N, a, inc, q, s, d=0.0, c=0.0):
    """Own canonicalisation from the incident ticks recorded in the plan's main run (page §4, I5)."""
    main = sw(N, a, inc, q, s)
    t_on, t_off = main["t_on"], main["t_off"]
    back = a.endswith("+back")
    g = a[:-5] if back else a
    if g == N:
        return sw(N, N, inc, q, s), "N-plan"
    t_sw = 40.0 + max(0, np.ceil(t_on + d - 40.0 - 1e-9))
    if t_sw >= t_off - 1e-9:
        return sw(N, N, inc, q, s), "noswitch"
    if not back:
        return (sw(N, g, inc, q, s, d=d) if d else main), "stay"
    t_bk = 40.0 + max(0, np.ceil(t_off + c - 40.0 - 1e-9))
    if t_bk > LAST + 1e-9:
        return (sw(N, g, inc, q, s, d=d) if d else sw(N, g, inc, q, s)), "back->stay"
    if not d and not c:
        return main, "back"
    return sw(N, a, inc, q, s, d=d, c=c), "back"


window_mismatch = 0
rep_seed_bad = 0
nn_hash_mismatch = 0
switch_time_bad = 0
for inc in INC:
    for q in QS:
        a = arms[q]
        N = a["N"]
        name = f"{inc}_q{int(q)}"
        D = {"NC": [fixed("NC", inc, q, s)["delay_s"] for s in EVAL]}
        for x in L0:
            D[x] = [fixed(a[x], inc, q, s)["delay_s"] for s in EVAL]
        D["ID"] = [sw(N, a["ID"], inc, q, s)["delay_s"] for s in EVAL]
        D["IP"] = [sw(N, a["IP"][inc], inc, q, s)["delay_s"] for s in EVAL]
        main = np.array([[sw(N, x, inc, q, s)["delay_s"] for x in A] for s in EVAL])     # (100, 100)
        reps = np.array([[[sw(N, x, inc, q, s, k=k)["delay_s"] for x in A] for k in (1, 2, 3, 4)] for s in EVAL])
        # checks: same incident window for every run of a seed; replicate seeds
        for si, s in enumerate(EVAL):
            w = {(r["t_on"], r["t_off"]) for r in [fixed(g, inc, q, s) for g in ["NC"] + [a[x] for x in L0]]
                 + [sw(N, x, inc, q, s, k=k) for x in A for k in range(5)]}
            window_mismatch += len(w) != 1
            for k in (1, 2, 3, 4):
                r = sw(N, A[0], inc, q, s, k=k)
                rep_seed_bad += not (r["sumo_seed"] == s + k * 10_000_000 and r["demand_seed"] == s + k * 10_000_000)
            nn_hash_mismatch += fixed(N, inc, q, s)["hash"] != sw(N, N, inc, q, s)["hash"]
        D["OR_in"] = main.min(axis=1)
        orx = {}
        for R in (1, 2, 4):
            m = reps[:, :R, :].mean(axis=1)
            j = np.argmin(m, axis=1)          # first minimal = A order
            orx[R] = main[np.arange(100), j]
            D[f"ORX_{R}"] = orx[R]
        D = {k: np.asarray(v, float) for k, v in D.items()}
        cell = {"median": {k: med(v) for k, v in D.items()}}
        # S1
        cell["ID_vs"] = {r: paired(D[r], D["ID"], L_S1) for r in L0}
        cell["IP_vs_ID"] = paired(D["ID"], D["IP"], L_S1)
        cell["IP_vs_L0_S1level"] = {r: paired(D[r], D["IP"], L_S1) for r in L0}
        cell["IP_vs_L0_95"] = {r: paired(D[r], D["IP"], L95) for r in L0}
        # S2
        s2 = {"OR_in_med": paired(D["IP"], D["OR_in"], L_S2), "OR_in_mean": paired(D["IP"], D["OR_in"], L_S2, True)}
        for R in (1, 2, 4):
            s2[f"ORX{R}_med"] = paired(D["IP"], orx[R], L_S2)
            s2[f"ORX{R}_mean"] = paired(D["IP"], orx[R], L_S2, True)
        s2["plateau"] = paired(orx[2], orx[4], L95, True)
        s2["x"] = s2["OR_in_med"]["rel_ci"][1]
        s2["y"] = s2["ORX4_mean"]["rel_ci"][0]
        s2["y_hat"] = s2["ORX4_mean"]["rel"]
        s2["plateau_holds"] = -0.01 <= s2["plateau"]["rel_ci"][0] and s2["plateau"]["rel_ci"][1] <= 0.01
        s2["or_in_le_every_main"] = bool(np.all(D["OR_in"][:, None] <= main + 1e-12))
        cell["S2"] = s2
        # TP
        ipi = A.index(a["IP"][inc])
        ipreps = reps[:, :, ipi]
        cell["TP"] = paired(D["IP"], np.minimum(D["IP"], ipreps.min(axis=1)), L95)
        # S3
        ip, ot = a["IP"][inc], a["IP"][[i for i in INC if i != inc][0]]
        Dd, kinds = [], {}
        for d in D_GRID:
            col = []
            for s in EVAL:
                r, kd = imperfect(N, ip, inc, q, s, d=d)
                kinds[(d, kd)] = kinds.get((d, kd), 0) + 1
                if kd != "noswitch" and kd != "N-plan" and d and r["t_switch"] != r["t_on"] + d:
                    switch_time_bad += 1
                col.append(r["delay_s"])
            Dd.append(col)
        Dd = np.array(Dd).T
        Dc = np.array([[imperfect(N, ip, inc, q, s, c=c)[0]["delay_s"] for s in EVAL] for c in C_GRID]).T
        Dot = np.array([sw(N, ot, inc, q, s)["delay_s"] for s in EVAL])
        Dp = np.stack([(1 - p) * D["IP"] + p * Dot for p in P_GRID], axis=1)
        s3 = {}
        for lab, Mx, grid, kind in (("d", Dd, D_GRID, "linear"), ("c", Dc, C_GRID, "linear"), ("p", Dp, P_GRID, "first")):
            s3[lab] = breakeven({r: D[r][:, None] - Mx for r in L0}, grid, kind)
        s3["d_kinds"] = {f"{k[0]:g}:{k[1]}": v for k, v in kinds.items()}
        cb_ip = np.array([imperfect(N, ip, inc, q, s, d=60, c=60)[0]["delay_s"] for s in EVAL])
        cb_ot = np.array([imperfect(N, ot, inc, q, s, d=60, c=60)[0]["delay_s"] for s in EVAL])
        comb = 0.8 * cb_ip + 0.2 * cb_ot
        s3["combined_median"] = med(comb)
        s3["combined_vs_IP"] = paired(D["IP"], comb, L95)
        s3["combined_vs_L0"] = {r: paired(D[r], comb, L95) for r in L0}
        cell["S3"] = s3
        res["cells"][name] = cell

# S1 verdicts
cells = list(res["cells"])
ra = {r: {c: rule(res["cells"][c]["ID_vs"][r]) for c in cells} for r in L0}
common = [c for c in cells if all(ra[r][c]["a"] for r in L0)]
s1a = bool(common) and all(all(ra[r][c]["b"] for c in cells) for r in L0)
rb = {c: rule(res["cells"][c]["IP_vs_ID"]) for c in cells}
s1b_cells = [c for c in cells if rb[c]["a"]]
s1b = bool(s1b_cells) and all(rb[c]["b"] for c in cells)
res["S1"] = {"S1a_pass": s1a, "S1a_common_a_cells": common,
             "S1a_a_cells_per_arm": {r: [c for c in cells if ra[r][c]["a"]] for r in L0},
             "S1a_b_fail": {r: [c for c in cells if not ra[r][c]["b"]] for r in L0},
             "S1b_pass": s1b, "S1b_a_cells": s1b_cells, "S1b_b_fail": [c for c in cells if not rb[c]["b"]]}

# clean day, false alarm, f*(pi)
res["per_q"] = {}
for q in QS:
    a = arms[q]
    N = a["N"]
    clean = {x: np.array([fixed(a[x], "none", q, s)["delay_s"] for s in EVAL]) for x in L0}
    clean["NC"] = np.array([fixed("NC", "none", q, s)["delay_s"] for s in EVAL])
    Dfa = np.mean([[fa(N, a["IP"][i].replace("+back", ""), q, s)["delay_s"] if a["IP"][i].replace("+back", "") != N
                    else fixed(N, "none", q, s)["delay_s"] for s in EVAL] for i in INC], axis=0)
    cost = paired(Dfa, clean["N"], L95)
    ipd = {i: np.array([sw(N, a["IP"][i], i, q, s)["delay_s"] for s in EVAL]) for i in INC}
    fst = {}
    for pi, p in a["prev"].items():
        L = {r: np.array([pi * (fixed(g, "slow", q, s)["delay_s"] + fixed(g, "block", q, s)["delay_s"]) / 2
                          + (1 - pi) * fixed(g, "none", q, s)["delay_s"] for s in EVAL]) for r, g in p.items()}
        X = {r: np.stack([L[r] - (pi * (ipd["slow"] + ipd["block"]) / 2 + (1 - pi) * ((1 - f) * clean["N"] + f * Dfa))
                          for f in P_GRID], axis=1) for r in L0}
        fst[str(pi)] = breakeven(X, P_GRID, "first")
    res["per_q"][str(int(q))] = {"clean_median": {k: med(v) for k, v in clean.items()}, "fa_cost": cost, "f_star": fst}

chk.update({"window_mismatch_seed_cells": window_mismatch, "replicate_seed_bad": rep_seed_bad,
            "N_fixed_vs_NN_hash_mismatch": nn_hash_mismatch, "delayed_switch_time_bad": switch_time_bad})
json.dump(res, open(OUT, "w"), indent=1, default=float)
print("done", MODE)
