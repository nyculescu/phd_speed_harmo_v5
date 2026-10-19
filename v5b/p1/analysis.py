"""P1 arms, spec lists and statements on stored run dicts (page §2-§6; pure, no SUMO).

Run dicts are keyed by v5b/p1/episode.run_key. Delays: the D2 primary metric 'delay_s' (lower is better).
Arm runs per seed in an incident cell (inc, q):
- NC, and every L0 arm (N, FX, FB, PI, AD): its controller from t = 0, no switching (fixed runs);
- ID, IP: 'N before onset, the chosen action of A after onset' (switch runs);
- OR_in: per seed the lowest main-run delay over A (in-sample);
- ORX_R: per seed the action with the lowest mean delay over replicates k = 1..R (ties: A order), scored on its main run.
On clean days ID and IP run N (page §6).
"""
from __future__ import annotations

from collections import Counter

import numpy as np

from v5b.d2.incidents import INCIDENTS, NONE, incident_window
from v5b.p1 import family as fam
from v5b.p1 import stats as st
from v5b.p1.episode import make_spec
from v5b.p1.meters import switch_schedule

QS = (1600.0, 2000.0)
CONDITIONS = (NONE,) + INCIDENTS
L0 = ("N", "FX", "FB", "PI", "AD")
R_SET = (1, 2, 4)                       # A7(a)
RMAX = R_SET[-1]
D_GRID = (0.0, 30.0, 60.0, 120.0, 240.0)
C_GRID = (0.0, 60.0, 180.0)
P_GRID = tuple(round(0.01 * i, 2) for i in range(101))
F_GRID = P_GRID
PIS = (0.1, 0.25, 0.5)
COMBINED = {"d": 60.0, "c": 60.0, "p": 0.2}
VSL_B = (0.8, 0.6, 0.4)
TV_B0 = 0.4
T_CTRL0, CONTROL_S = 40.0, 900.0


def qk(q) -> str:
    return str(int(q))


def cell_name(inc: str, q) -> str:
    return f"{inc}_q{qk(q)}"


def other(inc: str) -> str:
    return INCIDENTS[1 - INCIDENTS.index(inc)]


# ---------------------------------------------------------------- spec builders
def fixed(g, inc, q, s, k=0, vsl=None) -> dict:
    return make_spec(g, None, False, inc, q, s, k=k, vsl_b=vsl)


def sw(N, a, inc, q, s, k=0, d=0.0, c=0.0, vsl=None) -> dict:
    g, back = fam.parse_action(a)
    return make_spec(N, g, back, inc, q, s, k=k, d=d, c=c, vsl_b=vsl)


def canon_sw(N, a, inc, q, s, d=0.0, c=0.0) -> dict:
    """The run that realises plan a with detection delay d and clearance delay c (page §4), canonicalised to an
    identical existing run where the delays cannot act: no switch before clearance -> the N run (IP = N); a switch to
    N itself -> the N run; a stay plan ignores c; a back plan whose return falls after control -> the stay plan."""
    g, back = fam.parse_action(a)
    if g == N:
        return sw(N, N, inc, q, s)
    onset, dur = incident_window(s, T_CTRL0, CONTROL_S)
    t_sw, t_bk = switch_schedule(onset, dur, d, c, back, T_CTRL0, CONTROL_S)
    if t_sw is None:
        return sw(N, N, inc, q, s)
    if back and t_bk is None:
        return sw(N, g, inc, q, s, d=d)
    return sw(N, a, inc, q, s, d=d, c=c if back else 0.0)


def fa_spec(N, a, q, s) -> dict:
    """False alarm on a clean day (page §4): N, then at the alarm tick the plan's controller for 240 s, then N.
    A plan whose controller is N itself is the N run."""
    g = fam.parse_action(a)[0]
    if g == N:
        return fixed(N, NONE, q, s)
    return make_spec(N, g, False, NONE, q, s, fa=True)


def uniq(specs) -> list:
    seen, out = set(), []
    for s in specs:
        if s["key"] not in seen:
            seen.add(s["key"])
            out.append(s)
    return out


def _d(res, key, m="delay_s"):
    return res[key][m]


def _v(res, key) -> bool:
    return bool(res[key]["valid"])


# ---------------------------------------------------------------- selections (page §2)
def fit_fixed(res, seeds, G_, PI_, q) -> dict:
    """N (no-incident runs), FX, FB (pooled slow + block runs, constants / feedback meters of G), PI (pooled)."""
    none = {g: [_d(res, k) for s in seeds if (k := fixed(g, NONE, q, s)["key"]) in res] for g in G_}
    pooled = {g: [_d(res, k) for inc in INCIDENTS for s in seeds if (k := fixed(g, inc, q, s)["key"]) in res]
              for g in tuple(G_) + tuple(PI_)}
    out = {"N": fam.best_by_median(none, G_),
           "FX": fam.best_by_median(pooled, [g for g in G_ if g in fam.CONST]),
           "FB": fam.best_by_median(pooled, [g for g in G_ if g in fam.FEEDBACK])}
    if PI_:
        out["PI"] = fam.best_by_median(pooled, PI_)
    out["median_none"] = {g: float(np.median(v)) for g, v in none.items() if v}
    out["median_incident_pooled"] = {g: float(np.median(v)) for g, v in pooled.items() if v}
    return out


def fit_switch(res, seeds, A_, q, N) -> dict:
    """IP per (type, q) and ID per q (pooled slow + block) over A, from the runs 'N before onset, a after'."""
    per = {inc: {a: [_d(res, k) for s in seeds if (k := sw(N, a, inc, q, s)["key"]) in res] for a in A_}
           for inc in INCIDENTS}
    ip = {inc: fam.best_by_median(per[inc], A_) for inc in INCIDENTS}
    pooled = {a: per["slow"][a] + per["block"][a] for a in A_}
    return {"IP": ip, "ID": fam.best_by_median(pooled, A_),
            "median_switch": {inc: {a: float(np.median(v)) for a, v in per[inc].items() if v} for inc in INCIDENTS},
            "median_switch_pooled": {a: float(np.median(v)) for a, v in pooled.items() if v}}


def ad_candidates(FB: str) -> tuple:
    return tuple(fam.ad_id(e, FB) for e in fam.ETA_GRID)


def fit_ad(res, seeds, q, FB) -> dict:
    cand = ad_candidates(FB)
    pooled = {a: [_d(res, k) for inc in INCIDENTS for s in seeds if (k := fixed(a, inc, q, s)["key"]) in res]
              for a in cand}
    return {"AD": fam.best_by_median(pooled, cand),
            "median_incident_pooled": {a: float(np.median(v)) for a, v in pooled.items() if v}}


def fit_vsl_b(res, seeds, q, N, IP) -> dict:
    """If VSL entered (page §3 TV 3): b per cell, by median delay of IP + VSL(b) on the tuning seeds (ties: VSL_B order)."""
    out = {}
    for inc in INCIDENTS:
        per = {b: [_d(res, k) for s in seeds if (k := sw(N, IP[inc], inc, q, s, vsl=b)["key"]) in res] for b in VSL_B}
        out[inc] = float(fam.best_by_median({str(b): v for b, v in per.items()}, [str(b) for b in VSL_B]))
    return out


def prevalence_families(arms_q: dict, G_, PI_) -> dict:
    return {"N": tuple(G_), "FX": tuple(g for g in G_ if g in fam.CONST), "FB": tuple(g for g in G_ if g in fam.FEEDBACK),
            "PI": tuple(PI_), "AD": ad_candidates(arms_q["FB"])}


def fit_prevalence(res, seeds, q, families: dict) -> dict:
    """Page §6 prevalence line: each L0 arm re-tuned per pi on the per-seed mixture
    pi (D_slow + D_block) / 2 + (1 - pi) D_clean of its own tuning runs (lowest median; ties: family order)."""
    out = {}
    for pi in PIS:
        out[str(pi)] = {}
        for arm, cand in families.items():
            per = {}
            for g in cand:
                ks = [[fixed(g, c, q, s)["key"] for c in ("slow", "block", NONE)] for s in seeds]
                ks = [k for k in ks if all(x in res for x in k)]
                if ks:
                    per[g] = st.prevalence_mix([_d(res, k[0]) for k in ks], [_d(res, k[1]) for k in ks],
                                               [_d(res, k[2]) for k in ks], pi)
            out[str(pi)][arm] = fam.best_by_median(per, cand)
    return out


# ---------------------------------------------------------------- run lists
def fixed_specs(ctrls, conds, seeds, qs=QS) -> list:
    return [fixed(g, c, q, s) for q in qs for s in seeds for c in conds for g in ctrls]


def switch_specs(N: dict, A_, seeds, k=0, qs=QS) -> list:
    return [sw(N[qk(q)], a, inc, q, s, k=k) for q in qs for s in seeds for inc in INCIDENTS for a in A_]


def eval_specs(arms: dict, A_, seeds, rmax: int = RMAX, vsl: bool = False) -> list:
    """Every evaluation run (page §2, §4, §6, §7), main and derived runs first, replicates last."""
    N = {k: v["N"] for k, v in arms.items()}
    sp = switch_specs(N, A_, seeds)
    for q in QS:
        a = arms[qk(q)]
        l0 = [a[x] for x in L0] + [fam.NC]
        prev = [g for p in a["prev"].values() for g in p.values()]
        sp += fixed_specs(l0 + prev, CONDITIONS, seeds, (q,))
        for s in seeds:
            for inc in INCIDENTS:
                ip, ot = a["IP"][inc], a["IP"][other(inc)]
                sp += [canon_sw(a["N"], ip, inc, q, s, d=d) for d in D_GRID[1:]]
                sp += [canon_sw(a["N"], ip, inc, q, s, c=c) for c in C_GRID[1:]]
                sp += [canon_sw(a["N"], x, inc, q, s, d=COMBINED["d"], c=COMBINED["c"]) for x in (ip, ot)]
                sp.append(fa_spec(a["N"], ip, q, s))
                if vsl and a.get("VSL_b"):
                    sp.append(sw(a["N"], ip, inc, q, s, vsl=a["VSL_b"][inc]))
    for k in range(1, rmax + 1):
        sp += switch_specs(N, A_, seeds, k=k)
    return uniq(sp)


# ---------------------------------------------------------------- per-seed arm runs in a cell
def cell_runs(res, seeds, A_, q, inc, a: dict, rmax: int = RMAX, need_reps: bool = True) -> tuple:
    """(ok seeds, {arm: [key per seed]}, {'OR_in': [[keys]], 'reps': [[[keys]]]}) for an incident cell. A seed enters
    only if every run it needs exists (failed runs are reported by the runner)."""
    N = a["N"]
    ok, keys, sets = [], {x: [] for x in ("NC",) + L0 + ("ID", "IP")}, {"main": [], "reps": []}
    for s in seeds:
        k = {"NC": fixed(fam.NC, inc, q, s)["key"], **{x: fixed(a[x], inc, q, s)["key"] for x in L0},
             "ID": sw(N, a["ID"], inc, q, s)["key"], "IP": sw(N, a["IP"][inc], inc, q, s)["key"]}
        main = [sw(N, x, inc, q, s)["key"] for x in A_]
        reps = [[sw(N, x, inc, q, s, k=r)["key"] for x in A_] for r in range(1, rmax + 1)] if need_reps else []
        if not all(x in res for x in list(k.values()) + main + [y for r in reps for y in r]):
            continue
        ok.append(s)
        for x in keys:
            keys[x].append(k[x])
        sets["main"].append(main)
        sets["reps"].append(reps)
    return ok, keys, sets


def or_in(res, main_sets) -> tuple:
    """Per seed: (delay, chosen key, any invalid run among the A runs) of the in-sample oracle."""
    out = []
    for main in main_sets:
        d = {k: _d(res, k) for k in main}
        best = fam.argmin_tie(d, main)
        out.append((d[best], best, any(not _v(res, k) for k in main)))
    return out


def orx(res, main_sets, rep_sets, R: int) -> tuple:
    """Per seed: (main-run delay of the action with the best mean over replicates 1..R, chosen key, invalid flag over
    the replicates used and the chosen main run)."""
    out = []
    for main, reps in zip(main_sets, rep_sets):
        use = reps[:R]
        m = {i: float(np.mean([_d(res, r[i]) for r in use])) for i in range(len(main))}
        i = fam.argmin_tie(m, list(range(len(main))))
        inv = any(not _v(res, r[j]) for r in use for j in range(len(main))) or not _v(res, main[i])
        out.append((_d(res, main[i]), main[i], inv))
    return out


def arm_row(res, keys) -> dict:
    v = lambda m: np.array([_d(res, k, m) for k in keys], float)
    return {"n": len(keys), "median_delay_s": float(np.median(v("delay_s"))),
            "median_served_vph": float(np.median(v("served_ctrl_vph"))),
            "median_ttt_ctrl_vehh": float(np.median(v("ttt_ctrl_vehh"))),
            "median_ttt_full_vehh": float(np.median(v("ttt_full_vehh"))),
            "median_max_queue": float(np.median(v("max_queue"))),
            "n_invalid": int(sum(not _v(res, k) for k in keys)),
            "n_teleport_runs": int(sum(res[k]["teleports"] > 0 for k in keys))}


def _arr(res, keys):
    return np.array([_d(res, k) for k in keys], float)


def _inv(res, keys):
    return np.array([not _v(res, k) for k in keys], bool)


def _two(r, t, inv, level, mean=False):
    """A paired statistic in both views (all seeds; seeds without an invalid run entering it)."""
    a = st.paired(r, t, level, mean)
    if not inv.any():
        return {"all_seeds": a, "valid_only": a, "n_invalid_seeds": 0}
    keep = ~inv
    v = st.paired(np.asarray(r)[keep], np.asarray(t)[keep], level, mean) if keep.any() else None
    return {"all_seeds": a, "valid_only": v, "n_invalid_seeds": int(inv.sum())}


# ---------------------------------------------------------------- evaluation statements
def evaluate(res, seeds, A_, arms: dict, rmax: int = RMAX, vsl: bool = False, log=print) -> dict:
    cells, s1_stats, s1b_stats, s2, s3, ladder, opmap, tp = {}, {}, {}, {}, {}, {}, {}, {}
    for inc in INCIDENTS:
        for q in QS:
            name, a = cell_name(inc, q), arms[qk(q)]
            ok, keys, sets = cell_runs(res, seeds, A_, q, inc, a, rmax)
            if not ok:
                cells[name] = {"n_seeds": 0}
                continue
            D = {x: _arr(res, keys[x]) for x in keys}
            I = {x: _inv(res, keys[x]) for x in keys}
            oi = or_in(res, sets["main"])
            D["OR_in"], I["OR_in"] = np.array([x[0] for x in oi]), np.array([x[2] for x in oi])
            ox = {R: orx(res, sets["main"], sets["reps"], R) for R in R_SET if R <= rmax}
            for R, v in ox.items():
                D[f"ORX_{R}"], I[f"ORX_{R}"] = np.array([x[0] for x in v]), np.array([x[2] for x in v])
            # S1 (one statistic per (t, r, cell), both views)
            s1_stats[name] = {r: _two(D[r], D["ID"], I[r] | I["ID"], st.LEVEL_S1) for r in L0}
            s1b_stats[name] = _two(D["ID"], D["IP"], I["ID"] | I["IP"], st.LEVEL_S1)
            ip_vs_l0 = {r: _two(D[r], D["IP"], I[r] | I["IP"], st.LEVEL_S1) for r in L0}
            # S2
            orx_d = {R: D[f"ORX_{R}"] for R in ox}
            v_all = st.s2_cell(D["IP"], D["OR_in"], orx_d)
            inv_s2 = {"IP": I["IP"], "OR_in": I["OR_in"], **{R: I[f"ORX_{R}"] for R in ox}}
            v_val = s2_valid(D, inv_s2, orx_d)
            s2[name] = {"all_seeds": _slim_s2(v_all), "valid_only": _slim_s2(v_val) if v_val else None,
                        "n_invalid_seeds": {k: int(np.sum(v)) for k, v in
                                            {"IP": I["IP"], "OR_in": I["OR_in"],
                                             **{f"ORX_{R}": I[f"ORX_{R}"] for R in ox}}.items()},
                        "statements": st.s2_statements(v_all, v_val),
                        "or_in_picks": dict(Counter(res[x[1]]["post"] + ("+back" if res[x[1]]["back"] else "")
                                                    for x in oi).most_common(5)),
                        "orx_picks": {R: dict(Counter(res[x[1]]["post"] + ("+back" if res[x[1]]["back"] else "")
                                                      for x in v).most_common(5)) for R, v in ox.items()}}
            reps_ip = np.array([[_d(res, sw(a["N"], a["IP"][inc], inc, q, s, k=r)["key"]) for r in range(1, rmax + 1)]
                                for s in ok], float)
            tp[name] = st.tp_placebo(D["IP"], reps_ip)
            # S3 (imperfection map) and extra rows
            s3[name] = imperfection_cell(res, ok, q, inc, a, D, I)
            # Fig. 1 ladder and Table 1 operating map
            strongest = min(L0, key=lambda r: (float(np.median(D[r])), L0.index(r)))
            rungs = [strongest, "ID", "IP", f"ORX_{max(ox)}", "OR_in"]
            ladder[name] = {"strongest_L0": strongest, "rungs": [
                {"arm": x, "median_delay_s": float(np.median(D[x])),
                 "vs_strongest_L0": (None if x == strongest else st.paired(D[strongest], D[x], st.LEVEL_95))}
                for x in rungs]}
            rows = {x: arm_row(res, keys[x]) for x in keys}
            for x in ("OR_in",) + tuple(f"ORX_{R}" for R in ox):
                src = oi if x == "OR_in" else ox[int(x.split("_")[1])]
                rows[x] = arm_row(res, [y[1] for y in src])
            if vsl and a.get("VSL_b"):
                kv = [sw(a["N"], a["IP"][inc], inc, q, s, vsl=a["VSL_b"][inc])["key"] for s in ok]
                if all(k in res for k in kv):
                    rows["IP+VSL"] = arm_row(res, kv)
                    rows["IP+VSL"]["vs_IP"] = st.paired(D["IP"], _arr(res, kv), st.LEVEL_95)
            opmap[name] = {"n_seeds": len(ok), "arms": rows,
                           "controllers": {**{x: a[x] for x in L0}, "ID": a["ID"], "IP": a["IP"][inc]}}
            cells[name] = {"n_seeds": len(ok), "n_dropped_seeds": len(seeds) - len(ok), "IP_vs_L0": ip_vs_l0}
            log(f"[analysis] {name}: n {len(ok)}")
    s1 = s1_decision(s1_stats, s1b_stats)
    per_q = {qk(q): clean_and_prevalence(res, seeds, q, arms[qk(q)]) for q in QS}
    return {"cells": cells, "S1": s1, "S2": s2, "TP": tp, "S3": s3, "per_q": per_q, "fig1_ladder": ladder,
            "table1_operating_map": opmap}


def s2_valid(D, inv: dict, orx_d: dict):
    """S2 in the 'valid' view, each statistic on its own seeds (IP with OR_in; IP with ORX_R; ORX_{R/2} with ORX_R).
    None if some statistic has no seed left."""
    if not any(np.any(v) for v in inv.values()):
        return st.s2_cell(D["IP"], D["OR_in"], orx_d)
    rmax = max(orx_d)
    out = {"OR_in": {}, "ORX": {}}
    keep = ~(inv["IP"] | inv["OR_in"])
    if not keep.any():
        return None
    out["OR_in"] = {"median": st.paired(D["IP"][keep], D["OR_in"][keep], st.LEVEL_S2),
                    "mean": st.paired(D["IP"][keep], D["OR_in"][keep], st.LEVEL_S2, mean=True)}
    for R, v in orx_d.items():
        kk = ~(inv["IP"] | inv[R])
        if not kk.any():
            return None
        out["ORX"][R] = {"median": st.paired(D["IP"][kk], v[kk], st.LEVEL_S2),
                         "mean": st.paired(D["IP"][kk], v[kk], st.LEVEL_S2, mean=True)}
    kp = ~(inv[rmax // 2] | inv[rmax]) if rmax // 2 in orx_d else None
    plateau = st.paired(orx_d[rmax // 2][kp], orx_d[rmax][kp], st.LEVEL_95, mean=True) \
        if kp is not None and kp.any() else None
    ok = plateau is not None and -st.PLATEAU_Z <= plateau["rel_ci"][0] and plateau["rel_ci"][1] <= st.PLATEAU_Z
    out.update({"x": out["OR_in"]["median"]["rel_ci"][1], "y": out["ORX"][rmax]["mean"]["rel_ci"][0],
                "y_hat": out["ORX"][rmax]["mean"]["rel"], "plateau": plateau, "plateau_holds": bool(ok), "Rmax": rmax})
    return out


def _slim_s2(v):
    return {k: v[k] for k in ("OR_in", "ORX", "x", "y", "y_hat", "plateau", "plateau_holds", "Rmax")}


def s1_decision(s1_stats: dict, s1b_stats: dict) -> dict:
    """S1a and S1b (page §6) from per-cell two-view statistics; each must pass in both views."""
    cells = [c for c in s1_stats]

    def view(stats_by_cell, v):
        return {c: stats_by_cell[c][v] for c in cells}

    out = {}
    for v in ("all_seeds", "valid_only"):
        per_r = {r: {c: s1_stats[c][r][v] for c in cells} for r in L0}
        out[v] = {"S1a": st.s1a(per_r), "S1b": st.rule_R(view(s1b_stats, v))}
    s1a_pass = bool(cells) and out["all_seeds"]["S1a"]["pass"] and out["valid_only"]["S1a"]["pass"]
    s1b_pass = bool(cells) and out["all_seeds"]["S1b"]["pass"] and out["valid_only"]["S1b"]["pass"]
    out["S1a_pass"], out["S1b_pass"] = s1a_pass, s1b_pass
    out["S1a_text"] = ("presence and timing pay: ID beats every L0 arm" if s1a_pass else
                       "knowing that an incident is on did not pay >= 10 % beyond strong always-on control")
    out["S1b_text"] = ("the type pays: IP beats ID" if s1b_pass else
                       "the incident type added no detected >= 10 % gain beyond presence and timing")
    out["per_cell_stats"] = {c: {"ID_vs": s1_stats[c], "IP_vs_ID": s1b_stats[c]} for c in cells}
    return out


def imperfection_cell(res, ok, q, inc, a, D, I) -> dict:
    """Page §4 rows for IP in one incident cell, against each L0 arm, both views."""
    N, ip, ot = a["N"], a["IP"][inc], a["IP"][other(inc)]
    kd = {d: [canon_sw(N, ip, inc, q, s, d=d)["key"] for s in ok] for d in D_GRID}
    kc = {c: [canon_sw(N, ip, inc, q, s, c=c)["key"] for s in ok] for c in C_GRID}
    k_ot = [sw(N, ot, inc, q, s)["key"] for s in ok]
    k_nb = [sw(N, fam.parse_action(ip)[0], inc, q, s)["key"] for s in ok]
    k_cb = [[canon_sw(N, x, inc, q, s, d=COMBINED["d"], c=COMBINED["c"])["key"] for s in ok] for x in (ip, ot)]
    need = [k for v in list(kd.values()) + list(kc.values()) + [k_ot, k_nb] + k_cb for k in v]
    missing = [k for k in need if k not in res]
    if missing:
        return {"n_missing_runs": len(missing), "note": "imperfection runs missing"}
    Dd = np.stack([_arr(res, kd[d]) for d in D_GRID], axis=1)
    Dc = np.stack([_arr(res, kc[c]) for c in C_GRID], axis=1)
    Dot = _arr(res, k_ot)
    Dp = np.stack([st.mixture(D["IP"], Dot, p) for p in P_GRID], axis=1)
    inv_d = np.any([_inv(res, kd[d]) for d in D_GRID], axis=0)
    inv_c = np.any([_inv(res, kc[c]) for c in C_GRID], axis=0)
    inv_p = I["IP"] | _inv(res, k_ot)
    out = {}
    for lab, Mx, grid, kind, inv in (("d_star", Dd, D_GRID, "linear", inv_d), ("c_star", Dc, C_GRID, "linear", inv_c),
                                     ("p_star", Dp, P_GRID, "first", inv_p)):
        X = {r: D[r][:, None] - Mx for r in L0}
        invx = {r: I[r] | inv for r in L0}
        out[lab] = _breakeven_two(X, invx, grid, kind)
    comb = st.mixture(_arr(res, k_cb[0]), _arr(res, k_cb[1]), COMBINED["p"])
    inv_cb = _inv(res, k_cb[0]) | _inv(res, k_cb[1])
    out["combined_row"] = {"setting": COMBINED, "median_delay_s": float(np.median(comb)),
                           "vs_L0": {r: _two(D[r], comb, I[r] | inv_cb, st.LEVEL_95) for r in L0},
                           "vs_IP": _two(D["IP"], comb, I["IP"] | inv_cb, st.LEVEL_95)}
    nb = _arr(res, k_nb)
    out["never_switch_back"] = {"action": fam.parse_action(ip)[0], "same_as_IP": not fam.parse_action(ip)[1],
                                "median_delay_s": float(np.median(nb)),
                                "vs_IP": _two(D["IP"], nb, I["IP"] | _inv(res, k_nb), st.LEVEL_95)}
    out["clearance_delay_applies"] = bool(fam.parse_action(ip)[1])
    out["n_detection_no_switch"] = {str(d): int(sum(k == sw(N, N, inc, q, s)["key"] for k, s in zip(kd[d], ok)))
                                    for d in D_GRID}
    return out


def _breakeven_two(X: dict, invx: dict, grid, kind) -> dict:
    a = st.breakeven(X, grid, kind)
    inv = np.any([v for v in invx.values()], axis=0)
    if not inv.any():
        return {"all_seeds": a, "valid_only": a, "n_invalid_seeds": 0}
    keep = ~inv
    v = st.breakeven({r: x[keep] for r, x in X.items()}, grid, kind) if keep.any() else None
    return {"all_seeds": a, "valid_only": v, "n_invalid_seeds": int(inv.sum())}


def clean_and_prevalence(res, seeds, q, a: dict) -> dict:
    """Per demand: clean-day rows of every arm (ID = IP = N), the cost of one false alarm, the prevalence line
    (report only, A4(a)) with f*(pi)."""
    N = a["N"]
    ctrl = {x: a[x] for x in L0}
    ctrl["NC"] = fam.NC
    prev_ctrl = {pi: p for pi, p in a["prev"].items()}
    ok = []
    for s in seeds:
        ks = [fixed(g, NONE, q, s)["key"] for g in ctrl.values()]
        ks += [fa_spec(N, a["IP"][i], q, s)["key"] for i in INCIDENTS]
        ks += [sw(N, x, i, q, s)["key"] for i in INCIDENTS for x in (a["ID"], a["IP"][i])]
        ks += [fixed(g, c, q, s)["key"] for p in prev_ctrl.values() for g in p.values() for c in CONDITIONS]
        if all(k in res for k in ks):
            ok.append(s)
    if not ok:
        return {"n_seeds": 0}
    clean = {x: [fixed(g, NONE, q, s)["key"] for s in ok] for x, g in ctrl.items()}
    rows = {x: arm_row(res, k) for x, k in clean.items()}
    rows["ID"] = rows["IP"] = {"same_as": "N"}
    Dn, In = _arr(res, clean["N"]), _inv(res, clean["N"])
    fa_k = {i: [fa_spec(N, a["IP"][i], q, s)["key"] for s in ok] for i in INCIDENTS}
    Dfa = (_arr(res, fa_k["slow"]) + _arr(res, fa_k["block"])) / 2.0
    Ifa = _inv(res, fa_k["slow"]) | _inv(res, fa_k["block"])
    cost = _two(Dfa, Dn, Ifa | In, st.LEVEL_95)   # diff = median(FA - N) s/veh
    inc_d = {i: {x: _arr(res, [sw(N, (a["ID"] if x == "ID" else a["IP"][i]), i, q, s)["key"] for s in ok])
                 for x in ("ID", "IP")} for i in INCIDENTS}
    inc_i = {i: {x: _inv(res, [sw(N, (a["ID"] if x == "ID" else a["IP"][i]), i, q, s)["key"] for s in ok])
                 for x in ("ID", "IP")} for i in INCIDENTS}
    prev = {}
    for pi_s, p in prev_ctrl.items():
        pi = float(pi_s)
        L = {}
        Linv = {}
        for r, g in p.items():
            dd = {c: _arr(res, [fixed(g, c, q, s)["key"] for s in ok]) for c in CONDITIONS}
            ii = {c: _inv(res, [fixed(g, c, q, s)["key"] for s in ok]) for c in CONDITIONS}
            L[r] = st.prevalence_mix(dd["slow"], dd["block"], dd[NONE], pi)
            Linv[r] = ii["slow"] | ii["block"] | ii[NONE]
        rowp = {"controllers": p}
        for x in ("ID", "IP"):
            T = st.prevalence_mix(inc_d["slow"][x], inc_d["block"][x], Dn, pi)
            Ti = inc_i["slow"][x] | inc_i["block"][x] | In
            rowp[f"{x}_vs"] = {r: _two(L[r], T, Linv[r] | Ti, st.LEVEL_95) for r in L0}
        X = {r: np.stack([L[r] - st.prevalence_mix(inc_d["slow"]["IP"], inc_d["block"]["IP"], st.mixture(Dn, Dfa, f), pi)
                          for f in F_GRID], axis=1) for r in L0}
        invx = {r: Linv[r] | inc_i["slow"]["IP"] | inc_i["block"]["IP"] | In | Ifa for r in L0}
        rowp["f_star"] = _breakeven_two(X, invx, F_GRID, "first")
        prev[pi_s] = rowp
    return {"n_seeds": len(ok), "clean_day": rows, "controllers": ctrl, "false_alarm_cost": cost,
            "false_alarm_plans": {i: fam.parse_action(a["IP"][i])[0] for i in INCIDENTS}, "prevalence": prev}
