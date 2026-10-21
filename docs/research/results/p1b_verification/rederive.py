"""Independent re-derivation of P1b (p1b_addendum.md, V108, on top of p1_incident_information.md, V99 + addenda).
Adapted from ../p1_verification/rederive.py (which matched P1 exactly). Reads only recs.pkl (load.py). Does not import
v5b. P1b changes: seeds; A(q) = (G u G_PI(q)) x {stay, back} with G_PI(q) = top-10 PI by pooled tuning median (R1),
order G stay, G back, G_PI stay, G_PI back; runner rows (R5); realism rows (B1, B4, R4, R6, R7) with the recomputed
spill indicator (V109: tail within 50 m of the entry OR mean depart delay > 5 s; descriptive, post-run).
Usage: rederive.py recs.pkl out.json BOOTMODE   (page = rng(20261019) draws as I12; own = independent seed)."""
import json, pickle, sys
import numpy as np

recs = pickle.load(open(sys.argv[1], "rb"))
OUT, MODE = sys.argv[2], sys.argv[3]
B = 20_000
SEED = 20261019 if MODE == "page" else 987654321

RATES = [400, 600, 800] + list(range(1000, 2601, 100))
CONST = [f"c{r}" for r in RATES]
FEEDBACK = [f"f{k}_{n}" for k in (10, 20, 40, 70, 120) for n in (6, 8, 10, 12, 14, 16)]
G = CONST + FEEDBACK
PI = [f"p{kp}_{ki}_{n}_{e}" for e, ns in (("e4", (6, 8, 10, 12, 14, 16)), ("e5", (2, 4, 6, 8, 10, 12)))
      for kp in (20, 40, 70) for ki in (10, 20, 40, 70, 120) for n in ns]
ETA = ["0p5", "1", "2"]
assert len(G) == 50 and len(PI) == 180
QS = (1600.0, 2000.0)
INC = ("slow", "block")
L0 = ("N", "FX", "FB", "PI", "AD")
RARMS = L0 + ("ID", "IP")
SHARES = (0.1, 0.3)
TUNE = list(range(7400300, 7400340))
EVAL = list(range(7400600, 7400700))
SPILL_OLD_M, SPILL_NEW_M, SPILL_DEP_S = 7.0, 50.0, 5.0

IX = {}
for r in recs:
    key = (r["pre"], r["post"], bool(r["back"]), r["incident"], float(r["q"]), int(r["seed"]), int(r["k"]),
           float(r["d"]), float(r["c"]), bool(r["fa"]), float(r["rs"] or 0.0))
    assert key not in IX, key
    IX[key] = r


def fixed(g, inc, q, s, k=0, rs=0.0):
    return IX[(g, None, False, inc, q, s, k, 0.0, 0.0, False, float(rs))]


def sw(N, a, inc, q, s, k=0, d=0.0, c=0.0, rs=0.0):
    back = a.endswith("+back")
    g = a[:-5] if back else a
    return IX[(N, g, back, inc, q, s, k, float(d), float(c), False, float(rs))]


def fa(N, g, q, s):
    return IX[(N, g, False, "none", q, s, 0, 0.0, 0.0, True, 0.0)]


def med(x):
    return float(np.median(np.asarray(x, float)))


def best(cands, vals):
    return min(cands, key=lambda c: (med(vals[c]), cands.index(c)))


# ------------------------------------------------------------- tuning (page §2 + R1)
arms, AQ = {}, {}
for q in QS:
    none = {g: [fixed(g, "none", q, s)["delay_s"] for s in TUNE] for g in G}
    pooled = {g: [fixed(g, i, q, s)["delay_s"] for i in INC for s in TUNE] for g in G + PI}
    N = best(G, none)
    FX = best(CONST, pooled)
    FB = best(FEEDBACK, pooled)
    PIa = best(PI, pooled)
    GPI = sorted(PI, key=lambda c: (med(pooled[c]), PI.index(c)))[:10]
    A = G + [g + "+back" for g in G] + GPI + [g + "+back" for g in GPI]
    assert len(A) == 120
    AQ[q] = A
    ADc = [f"ad{e}_{FB}" for e in ETA]
    ADv = {a: [fixed(a, i, q, s)["delay_s"] for i in INC for s in TUNE] for a in ADc}
    AD = best(ADc, ADv)
    per = {i: {a: [sw(N, a, i, q, s)["delay_s"] for s in TUNE] for a in A} for i in INC}
    IP = {i: best(A, per[i]) for i in INC}
    ID = best(A, {a: per["slow"][a] + per["block"][a] for a in A})
    fams = {"N": G, "FX": CONST, "FB": FEEDBACK, "PI": PI, "AD": ADc}
    prev = {}
    for pi in (0.1, 0.25, 0.5):
        prev[pi] = {}
        for arm, cand in fams.items():
            mix = {g: [pi * (fixed(g, "slow", q, s)["delay_s"] + fixed(g, "block", q, s)["delay_s"]) / 2
                       + (1 - pi) * fixed(g, "none", q, s)["delay_s"] for s in TUNE] for g in cand}
            prev[pi][arm] = best(list(cand), mix)
    # runner-up of the IP choice (descriptive; how close the tuning choice was)
    ip_top3 = {i: sorted(A, key=lambda a: (med(per[i][a]), A.index(a)))[:3] for i in INC}
    ip_top3 = {i: [(a, med(per[i][a])) for a in v] for i, v in ip_top3.items()}
    arms[q] = {"N": N, "FX": FX, "FB": FB, "PI": PIa, "AD": AD, "ID": ID, "IP": IP, "G_PI": GPI, "prev": prev,
               "IP_top3_tuning": ip_top3}

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


def crossing(M, grid, kind):
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
            vals[j] = g[i] if kind == "first" else g[i - 1] + (g[i] - g[i - 1]) * m[i - 1] / (m[i - 1] - m[i])
            flags[j] = 0
    return vals, flags


FL = {0: "crossing", 1: "IP never ahead", 2: "> max"}


def breakeven(X, grid, kind):
    per = {}
    for a in L0:
        v, f = crossing(np.median(X[a], axis=0), grid, kind)
        per[a] = (float(v[0]), FL[int(f[0])], [float(x) for x in np.median(X[a], axis=0)])
    bind = min(L0, key=lambda a: (per[a][0], L0.index(a)))
    n = X["N"].shape[0]
    I = idx(n)
    allv, allf = [], []
    for a in L0:
        Mb = np.concatenate([np.median(X[a][I[s:s + 500]], axis=1) for s in range(0, B, 500)])
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


# ------------------------------------------------------------- realism rows (B1, B4, R4, R6, R7, V109)
def spill_new(r):
    return r["max_queue_m"] >= r["avail_m"] - SPILL_NEW_M or r["depart_delay_s"] > SPILL_DEP_S


def realism(rr):
    ap = [r["approach_red_mps"] for r in rr]
    mq = np.array([r["max_queue_m"] for r in rr], float)
    dep = np.array([r["depart_delay_s"] for r in rr], float)
    av = rr[0]["avail_m"]
    return {"n": len(rr), "emergency_meter_total": int(sum(r["emergency_meter"] or 0 for r in rr)),
            "emergency_stops_total": int(sum(r["emergency_stops"] for r in rr)),
            "collisions_total": int(sum(r["collisions"] for r in rr)),
            "approach_red_med": med([a["median"] for a in ap if a["median"] is not None]) if any(
                a["median"] is not None for a in ap) else None,
            "approach_red_max": max((a["max"] for a in ap if a["max"] is not None), default=None),
            "approach_red_n_ge_10": int(sum(a["n_ge_10"] for a in ap)),
            "red_cross_share_med": med([r["red_cross_share"] for r in rr]),
            "red_cross_share_mean": float(np.mean([r["red_cross_share"] for r in rr])),
            "runner_red_cross_share_med": (med([r["runner_red_cross_share"] for r in rr if r["runner_red_cross_share"]
                                                is not None]) if any(r["runner_red_cross_share"] is not None for r in rr)
                                           else None),
            "commanded_med": (med([r["commanded_mean_vph"] for r in rr if r["commanded_mean_vph"] is not None])
                              if any(r["commanded_mean_vph"] is not None for r in rr) else None),
            "discharge_med": {x: med([r["discharge_vph"][x] for r in rr]) for x in ("G", "y", "r")},
            "served_med": med([r["served_ctrl_vph"] for r in rr]),
            "max_queue_veh_med": med([r["max_queue"] for r in rr]),
            "max_queue_m_med": float(np.median(mq)), "max_queue_m_max": float(mq.max()), "avail_m": av,
            "depart_delay_med": float(np.median(dep)), "depart_delay_max": float(dep.max()),
            "spill_old7": float(np.mean(mq >= av - SPILL_OLD_M)),
            "spill_tail50": float(np.mean(mq >= av - SPILL_NEW_M)),
            "spill_dep5": float(np.mean(dep > SPILL_DEP_S)),
            "spill_new": float(np.mean([spill_new(r) for r in rr]))}


# ------------------------------------------------------------- evaluation
D_GRID, C_GRID = (0.0, 30.0, 60.0, 120.0, 240.0), (0.0, 60.0, 180.0)
P_GRID = [round(0.01 * i, 2) for i in range(101)]
LAST = 40.0 + 900.0 - 1.0
res = {"arms": {str(int(q)): {k: (v if k != "prev" else {str(p): x for p, x in v.items()}) for k, v in a.items()}
                for q, a in arms.items()}, "cells": {}, "checks": {}, "runner_rows": {}, "clean_realism": {}}
chk = res["checks"]
ev = [r for r in recs if 7400600 <= r["seed"] <= 7400699]
chk["n_eval_runs"] = len(ev)
chk["n_tune_runs"] = len(recs) - len(ev)
chk["n_invalid_eval"] = sum(1 for r in ev if not r["valid"])
chk["n_teleport_eval"] = sum(1 for r in ev if (r["teleports"] or 0) > 0)
chk["n_undrained_eval"] = sum(1 for r in ev if not r["drained"])
chk["n_collision_runs_eval"] = sum(1 for r in ev if (r["collisions"] or 0) > 0)
chk["signals"] = sorted({r["signal"] for r in recs if r["pre"] != "NC"} | set())
chk["commits"] = sorted({r["code_commit"] for r in recs})


def imperfect(N, a, inc, q, s, d=0.0, c=0.0):
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


window_mismatch = rep_seed_bad = nn_hash_mismatch = switch_time_bad = 0
for inc in INC:
    for q in QS:
        a, A = arms[q], AQ[q]
        N = a["N"]
        name = f"{inc}_q{int(q)}"
        RK = {"NC": [fixed("NC", inc, q, s) for s in EVAL]}
        for x in L0:
            RK[x] = [fixed(a[x], inc, q, s) for s in EVAL]
        RK["ID"] = [sw(N, a["ID"], inc, q, s) for s in EVAL]
        RK["IP"] = [sw(N, a["IP"][inc], inc, q, s) for s in EVAL]
        mainR = [[sw(N, x, inc, q, s) for x in A] for s in EVAL]
        main = np.array([[r["delay_s"] for r in row] for row in mainR])                       # (100, 120)
        reps = np.array([[[sw(N, x, inc, q, s, k=k)["delay_s"] for x in A] for k in (1, 2, 3, 4)] for s in EVAL])
        for si, s in enumerate(EVAL):
            w = {(r["t_on"], r["t_off"]) for r in [fixed(g, inc, q, s) for g in ["NC"] + [a[x] for x in L0]]
                 + [sw(N, x, inc, q, s, k=k) for x in A for k in range(5)]}
            window_mismatch += len(w) != 1
            for k in (1, 2, 3, 4):
                r = sw(N, A[0], inc, q, s, k=k)
                rep_seed_bad += not (r["sumo_seed"] == s + k * 10_000_000 and r["demand_seed"] == s + k * 10_000_000)
            nn_hash_mismatch += fixed(N, inc, q, s)["hash"] != sw(N, N, inc, q, s)["hash"]
        D = {k: np.array([r["delay_s"] for r in v], float) for k, v in RK.items()}
        jin = main.argmin(axis=1)
        D["OR_in"] = main[np.arange(100), jin]
        RK["OR_in"] = [mainR[i][j] for i, j in enumerate(jin)]
        orx = {}
        for R in (1, 2, 4):
            j = np.argmin(reps[:, :R, :].mean(axis=1), axis=1)
            orx[R] = main[np.arange(100), j]
            D[f"ORX_{R}"] = orx[R]
            RK[f"ORX_{R}"] = [mainR[i][jj] for i, jj in enumerate(j)]
        cell = {"median": {k: med(v) for k, v in D.items()}}
        cell["realism"] = {k: realism(v) for k, v in RK.items()}
        cell["ID_vs"] = {r: paired(D[r], D["ID"], L_S1) for r in L0}
        cell["IP_vs_ID"] = paired(D["ID"], D["IP"], L_S1)
        cell["IP_vs_L0_S1level"] = {r: paired(D[r], D["IP"], L_S1) for r in L0}
        cell["IP_vs_L0_95"] = {r: paired(D[r], D["IP"], L95) for r in L0}
        cell["IP_vs_ID_95"] = paired(D["ID"], D["IP"], L95)
        cell["ID_vs_95"] = {r: paired(D[r], D["ID"], L95) for r in L0}
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
        s2["or_in_pick_is_pi_plan"] = float(np.mean([A[j].startswith("p") for j in jin]))
        cell["S2"] = s2
        ipi = A.index(a["IP"][inc])
        cell["TP"] = paired(D["IP"], np.minimum(D["IP"], reps[:, :, ipi].min(axis=1)), L95)
        ip, ot = a["IP"][inc], a["IP"][[i for i in INC if i != inc][0]]
        Dd, kinds = [], {}
        for d in D_GRID:
            col = []
            for s in EVAL:
                r, kd = imperfect(N, ip, inc, q, s, d=d)
                kinds[(d, kd)] = kinds.get((d, kd), 0) + 1
                if kd not in ("noswitch", "N-plan") and d and r["t_switch"] != r["t_on"] + d:
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
        s3["IP_median_by_d"] = [med(Dd[:, j]) for j in range(len(D_GRID))]
        cb_ip = np.array([imperfect(N, ip, inc, q, s, d=60, c=60)[0]["delay_s"] for s in EVAL])
        cb_ot = np.array([imperfect(N, ot, inc, q, s, d=60, c=60)[0]["delay_s"] for s in EVAL])
        comb = 0.8 * cb_ip + 0.2 * cb_ot
        s3["combined_median"] = med(comb)
        s3["combined_vs_IP"] = paired(D["IP"], comb, L95)
        s3["combined_vs_L0"] = {r: paired(D[r], comb, L95) for r in L0}
        cell["S3"] = s3
        res["cells"][name] = cell

        # runner rows (R5): every L0 arm, ID and IP at s, vs themselves at s = 0; 95 %; descriptive
        def rk(x, s, rs):
            if x == "ID":
                return sw(N, a["ID"], inc, q, s, rs=rs)
            if x == "IP":
                return sw(N, a["IP"][inc], inc, q, s, rs=rs)
            return fixed(a[x], inc, q, s, rs=rs)
        for rs in SHARES:
            K = {x: [rk(x, s, rs) for s in EVAL] for x in RARMS}
            K0 = {x: [rk(x, s, 0.0) for s in EVAL] for x in RARMS}
            Ds = {x: np.array([r["delay_s"] for r in v], float) for x, v in K.items()}
            D0 = {x: np.array([r["delay_s"] for r in v], float) for x, v in K0.items()}
            # same runner vehicles in every arm (R4): one runner hash per seed across the 7 arms
            hash_bad = sum(len({K[x][i]["runner_hash"] for x in RARMS}) != 1 for i in range(len(EVAL)))
            share = [K["N"][i]["n_runners"] / K["N"][i]["n_trips"] for i in range(len(EVAL))]
            res["runner_rows"][f"s{rs:g}_{name}"] = {
                "ID_vs": {r: paired(Ds[r], Ds["ID"], L95) for r in L0},
                "IP_vs_ID": paired(Ds["ID"], Ds["IP"], L95),
                "IP_vs": {r: paired(Ds[r], Ds["IP"], L95) for r in L0},
                "vs_self_s0": {x: paired(D0[x], Ds[x], L95) for x in RARMS},
                "median": {x: med(Ds[x]) for x in RARMS}, "median_s0": {x: med(D0[x]) for x in RARMS},
                "realism": {x: realism(K[x]) for x in RARMS},
                "runner_hash_mismatch_seeds": int(hash_bad),
                "runner_share_of_trips_med": med(share)}

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

res["per_q"] = {}
for q in QS:
    a = arms[q]
    N = a["N"]
    cleanR = {x: [fixed(a[x], "none", q, s) for s in EVAL] for x in L0}
    cleanR["NC"] = [fixed("NC", "none", q, s) for s in EVAL]
    clean = {x: np.array([r["delay_s"] for r in v]) for x, v in cleanR.items()}
    res["clean_realism"][str(int(q))] = {x: realism(v) for x, v in cleanR.items()}
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
