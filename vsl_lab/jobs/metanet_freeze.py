"""Freeze of the U.S.169 SB METANET plant (protocol v3 §4.4-§4.8, §8.6 step 4). Calibration days only; nothing here
reads a validation day. Inputs: cma_summary.json, the grid_*, profile_* and stephalving_* files of metanet_postcal.

python -m vsl_lab.jobs.metanet_freeze            # writes docs/lab/day_pattern/metanet_calibration.{json,md}
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm, pearsonr, spearmanr

from vsl_lab.data import metanet_facts as F
from vsl_lab.data import metanet_inputs as I
from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import metanet_postcal as Q
from vsl_lab.plants import metanet as M

RUNS = C.RUNS
OUT = C.REPO / "docs" / "lab" / "day_pattern"
SEED_BOOT = 7190094
NEAR = 1.02
ENS_KEYS = ["tau", "nu", "kappa", "delta_m", "phi"]
STOP_OUTCOME = ("FAIL (N0: step-halving, §2.5); F1 not triggered (N0 is outside the §6.1 set); route stop before any "
                "validation run (§0.3, §6.2, §8.6 step 4)")
RECORD_NOTES = [
    "Everything in this record after the step-halving check (capacity grid, c2*, F-hat, identifiability profiles, "
    "§4.8 diagnostics) is post-stop and report-only: it ran on calibration days after the FAIL was known (a driver "
    "scheduled before the result) and may not inform any capacity-factor, plant or protocol choice.",
    "The step-halving FAIL was checked by an adversarial review (4 independent lenses: implementation, simulator time "
    "step, event rule, protocol reading; 2026-10-06): none refuted it. The step loop scales every term by T, the "
    "event rule is unchanged, and the observation operator does not cause the flip (the decisions are the same with "
    "c_s = 1).",
    "The 5-s plant is not converged in time step inside the B2 queue: finer steps (2.5, 1.25, 0.625 s) agree with "
    "each other and keep the 20230517 P_2 episode, while 5 s drops it (step_probe). The FAIL is a numerical defect of "
    "the T = 5 s plant, not a threshold artefact around a converged answer.",
    "Protocol inconsistency disclosed: §5.5 ('reported, not gated') and Appendix A round-1 row 16 still list "
    "step-halving as reported (a v1 remnant); §2.5, the §5.3 N0 row, §8.6 step 4 and Appendix C round-3 issue 2 make "
    "it gated, and the specific, amended text governs.",
    "Fix after results (logged, both outcomes): the model-side mask of §5.1 used np.isfinite (it also masked real "
    "+inf bins, K = 0); it now masks NaN only, as written. The step-halving check was re-run with the fix; both "
    "outcomes are in stephalving_7190016_mask_isfinite.json and stephalving_7190016.json.",
    "Provenance: the CMA-ES batch was launched at 06:08:58 from commit 663dd62 (the working tree held only untracked "
    "files the job does not import); its ledger row carries the commit at append time (9f0e477+dirty), because "
    "metanet.py gained diagnostic counters during the run (aaa8b21). J(5 s) in the step-halving run equals the CMA-ES "
    "best J bit for bit, so those counters left the dynamics unchanged.",
    "The capacity-grid batch report counts its 41 jobs as failed: the grid subcommand printed a path instead of a "
    "JSON line. All 41 jobs exited with code 0 and wrote their files; the subcommand now prints a JSON line.",
    "The nominal restart 7190016 is alone in its basin (the other 7 restarts end at J ~ 0.1697). Its tau = 12.0 s is "
    "the closest of all restarts to the 2T = 10 s bound (T/tau = 0.42 at 5 s); the fit may partly exploit the 5-s "
    "scheme. Choosing another restart now would be post hoc.",
    "Post-stop lesson (report-only; the explanation is a hypothesis, not tested): the event stations that close the "
    "bottleneck pairs sit inside the model's bottleneck cells: Pioneer Tr (S1140, P_1's downstream station) in B1's "
    "last cell (30) and Old Shakopee Rd (S1141, P_2's downstream station) in B2's last cell (32). In the capacity grid "
    "at c2 = 0.80, B2 is model-active on all 22 days and relocation branch (b) (an episode at Old Shakopee Rd -> "
    "T.H.101) fires on 869 of 902 (c1, day) points: S1141 reads the bottleneck cell's queue speeds. At c1 = c2 = 1, "
    "branch (a) fires on 6 of 22 days at cell 33 (the E15 merge cell). The same placement may contribute to the "
    "model's B2 activity on only 2 of the 9 real-B2 calibration days.",
]


# ---------------------------------------------------------------- small statistics
def km(exact: list, cens: list, upper: float) -> dict:
    """Kaplan-Meier with right censoring (ties: events before censorings); the mass left after the largest
    observation is placed at `upper` (the grid maximum)."""
    obs = sorted([(round(x, 4), 0) for x in exact] + [(round(x, 4), 1) for x in cens])
    S, risk, mass, i = 1.0, len(obs), {}, 0
    while i < len(obs):
        t, d, c = obs[i][0], 0, 0
        while i < len(obs) and obs[i][0] == t:
            d += obs[i][1] == 0
            c += obs[i][1] == 1
            i += 1
        if d:
            m = S * d / risk
            mass[t] = mass.get(t, 0.0) + m
            S -= m
        risk -= d + c
    up = max(S, 0.0)
    if up > 1e-12:
        mass[round(upper, 4)] = mass.get(round(upper, 4), 0.0) + up
    xs = np.array(sorted(mass))
    ps = np.array([mass[x] for x in xs])
    cdf = np.cumsum(ps)
    med = float(xs[np.searchsorted(cdf, 0.5 - 1e-12)]) if xs.size else None
    mu = float((xs * ps).sum()) if xs.size else None
    sd = float(np.sqrt((ps * (xs - mu) ** 2).sum())) if xs.size else None
    return {"support": xs.tolist(), "mass": ps.tolist(), "upper": upper, "upper_atom_mass": float(up), "median": med,
            "mean": mu, "sd": sd, "cv": sd / mu if mu else None,
            "mass_below_1": float(ps[xs < 1 - 1e-9].sum()), "mass_at_1": float(ps[np.abs(xs - 1) < 1e-9].sum()),
            "mass_above_1": float(ps[xs > 1 + 1e-9].sum()), "n_exact": len(exact), "n_censored": len(cens)}


def tobit(exact: list, cens: list) -> dict:
    """Right-censored normal ML fit (mu, sigma); usable only with >= 5 exact observations, convergence, sigma > 0."""
    if len(exact) < 2:
        return {"usable": False, "why": f"{len(exact)} exact observations", "n_exact": len(exact)}
    ex, ce = np.array(exact, float), np.array(cens, float)

    def nll(th):
        s = math.exp(th[1])
        return -(norm.logpdf(ex, th[0], s).sum() + (norm.logsf(ce, th[0], s).sum() if ce.size else 0.0))

    r = minimize(nll, [ex.mean(), math.log(max(ex.std(), 0.01))], method="Nelder-Mead",
                 options={"xatol": 1e-8, "fatol": 1e-10, "maxiter": 20000})
    mu, s = float(r.x[0]), float(math.exp(r.x[1]))
    ok = bool(r.success and s > 1e-6 and len(exact) >= 5)
    return {"mu": mu, "sigma": s, "converged": bool(r.success), "n_exact": len(exact), "n_censored": len(cens),
            "usable": ok, "why": None if ok else ("< 5 exact" if len(exact) < 5 else "not converged or sigma = 0")}


def spearman_ci(x, y, n_boot: int = 10000) -> dict | None:
    x, y = np.asarray(x, float), np.asarray(y, float)
    if x.size < 4:
        return {"n": int(x.size), "rho": None, "ci": None}
    rng = np.random.default_rng(SEED_BOOT)
    bs = []
    for _ in range(n_boot):
        i = rng.integers(0, x.size, x.size)
        if np.ptp(x[i]) > 0 and np.ptp(y[i]) > 0:
            bs.append(spearmanr(x[i], y[i]).statistic)
    rho = spearmanr(x, y).statistic if np.ptp(x) > 0 and np.ptp(y) > 0 else np.nan
    return {"n": int(x.size), "rho": float(rho) if np.isfinite(rho) else None,
            "ci": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))] if bs else None}


# ---------------------------------------------------------------- §4.7 capacity factors
def load_grid(seed: int) -> list:
    rows = []
    for i in range(len(Q.GRID)):
        rows += json.loads((RUNS / f"grid_{seed}_c2_{i:02d}.json").read_text())
    return rows


def capacity_factors(seed: int, days: list, real_active: dict, demand: dict, real_ev: dict) -> dict:
    rows = load_grid(seed)
    G = [float(g) for g in Q.GRID]
    idx = {(r["day"], r["c1"], r["c2"]): r for r in rows}
    reloc_by_c2 = {g: any(r["reloc"] for r in rows if r["c2"] == g) for g in G}
    cstar = Q.c2_star(reloc_by_c2)
    flags = {f"{g:.2f}": sum(r["reloc"] for r in rows if r["c2"] == g) for g in G}
    nxt = G[0] if cstar is None else (round(cstar + 0.01, 2) if cstar < 1.20 - 1e-9 else None)
    build = [{"day": r["day"], "c1": r["c1"], "cells_1based": r["reloc_cells"], "pair": r["reloc_pair"]}
             for r in rows if nxt is not None and r["c2"] == nxt and r["reloc"]]
    out = {"plant_seed": seed, "c2_star": cstar, "relocation_rows_by_c2": flags, "build_check_c2": nxt,
           "build_check_rows": build[:50], "build_check_days": sorted({b["day"] for b in build})}
    if cstar is None:
        out.update({"estimable": False, "rules_failed": ["iv"], "note": "c2* below the grid minimum 0.80"})
        return out
    G1, G2 = G, [g for g in G if g <= cstar + 1e-9]
    upper = {"B1": 1.20, "B2": cstar}
    gridk = {"B1": G1, "B2": G2}

    def E(d, k, ck, other):
        c1, c2 = (ck, other) if k == "B1" else (other, ck)
        return idx[(d, c1, c2)]["E" + k[1]]

    per_day, nonrep, nonmono = {}, [], []
    for d in days:
        ra = real_active[d]
        cset = []
        for c1 in G1:
            for c2 in G2:
                r = idx[(d, c1, c2)]
                ok = all((r["O" + k[1]] if ra[k] else not r["E" + k[1]]) for k in ("B1", "B2")) and not r["Z"]
                if ok:
                    cset.append(r)
        for k in ("B1", "B2"):                                      # monotonicity of E_k in c_k, every line
            oth = G2 if k == "B1" else G1
            bad = 0
            for o in oth:
                e = [E(d, k, g, o) for g in gridk[k]]
                bad += any((not e[i]) and e[i + 1] for i in range(len(e) - 1))
            if bad:
                nonmono.append({"day": d, "k": k, "lines": bad})
        if not cset:
            nonrep.append({"day": d, "real_active": [k for k in ("B1", "B2") if ra[k]]})
            per_day[d] = {"reproducible": False}
            continue
        best = min(cset, key=lambda r: (r["L"] if r["L"] is not None else np.inf,
                                        math.hypot(r["c1"] - 1, r["c2"] - 1), r["c1"]))
        hat = {"B1": best["c1"], "B2": best["c2"]}
        comp = {}
        for k in ("B1", "B2"):
            if ra[k]:
                comp[k] = {"type": "exact", "c": hat[k]}
        for k in ("B1", "B2"):
            if ra[k]:
                continue
            ko = "B2" if k == "B1" else "B1"
            other = hat[ko] if ra[ko] else upper[ko]
            e = [E(d, k, g, other) for g in gridk[k]]
            low, fb = None, False
            for i in range(len(e)):
                if not any(e[i:]):
                    low = gridk[k][i]
                    break
            if low is None:                                          # episode even at the top: non-monotone line
                low, fb = hat[k], True
            comp[k] = {"type": "censored", "c_low": low, "other_held_at": other, "fallback_argmin": fb}
        per_day[d] = {"reproducible": True, "c1_hat": hat["B1"], "c2_hat": hat["B2"], "L": best["L"],
                      "n_consistent": len(cset), "components": comp}
    act_days = [d for d in days if real_active[d]["B1"] or real_active[d]["B2"]]
    n_nonrep_act = sum(1 for x in nonrep if x["real_active"])
    F_hat, tob, comps = {}, {}, {}
    for k in ("B1", "B2"):
        ex = [per_day[d]["components"][k]["c"] for d in days if per_day[d]["reproducible"]
              and per_day[d]["components"][k]["type"] == "exact"]
        ce = [per_day[d]["components"][k]["c_low"] for d in days if per_day[d]["reproducible"]
              and per_day[d]["components"][k]["type"] == "censored"]
        comps[k] = {"exact": ex, "censored": ce}
        F_hat[k] = km(ex, ce, upper[k])
        tob[k] = tobit(ex, ce)
    rules = []
    if act_days and n_nonrep_act / len(act_days) > 0.20:
        rules.append("i")
    if any(F_hat[k]["upper_atom_mass"] > 0.25 for k in F_hat):
        rules.append("ii")
    if any(F_hat[k]["n_exact"] < 8 for k in F_hat):
        rules.append("iii")
    if cstar < 1.00:
        rules.append("iv")
    est = not rules
    sub = (not est) and not ({"i", "iv"} & set(rules))
    spread = "KM" if est else ("Tobit" if sub and all(tob[k]["usable"] for k in tob) else "none (deterministic-only)")
    # reported alongside (§4.7)
    corr = {}
    for k in ("B1", "B2"):
        ex_days = [d for d in days if per_day[d].get("reproducible") and per_day[d]["components"][k]["type"] == "exact"]
        hv = [d for d in ex_days if real_ev[d][k + "_long"] and real_ev[d][k + "_long"]["heavy"]]
        qd = [real_ev[d][k + "_long"]["c4"]["Q_dis"] for d in hv]
        corr[k] = {"c_vs_daily_demand": spearman_ci([per_day[d]["components"][k]["c"] for d in ex_days],
                                                    [demand[d] for d in ex_days]),
                   "c_vs_real_Qdis_heavy": spearman_ci([per_day[d]["components"][k]["c"] for d in hv], qd),
                   "real_Qdis_cv_heavy": float(np.std(qd) / np.mean(qd)) if len(qd) >= 2 else None,
                   "F_hat_cv": F_hat[k]["cv"]}
    both = [d for d in days if per_day[d].get("reproducible") and all(
        per_day[d]["components"][k]["type"] == "exact" for k in ("B1", "B2"))]
    corr["c1_vs_c2_both_exact"] = spearman_ci([per_day[d]["c1_hat"] for d in both], [per_day[d]["c2_hat"] for d in both])
    out.update({"per_day": per_day, "non_reproducible": nonrep,
                "non_reproducible_share_of_real_active_days": n_nonrep_act / len(act_days) if act_days else None,
                "n_real_active_days": len(act_days), "non_monotone": nonmono, "components": comps,
                "F_hat": F_hat, "tobit": tob, "estimable": est, "rules_failed": rules,
                "substitute_allowed": sub, "spread_used": spread,
                "recentring_m": {k: (F_hat[k]["median"] if est else (tob[k]["mu"] if spread == "Tobit" else None))
                                 for k in ("B1", "B2")},
                "clip_ranges": {"c1": [0.80, 1.20], "c2": [0.80, min(1.20, cstar)]}, "correlations": corr})
    return out


# ---------------------------------------------------------------- §4.5 identifiability
def identifiability(s: dict, data: dict, net: M.Net) -> dict:
    names = C.NAMES
    Jb = s["nominal_J"]
    near = [r for r in s["restarts"] if r["best_J"] <= NEAR * Jb]
    X = np.array([r["best_x"] for r in near])
    out = {"J_best": Jb, "near_best_seeds": [r["seed"] for r in near], "n_near_best": len(near)}
    assess = len(near) >= 3
    out["restart_range_norm"] = {n: float(np.ptp(X[:, i])) for i, n in enumerate(names)} if assess else "not assessable"
    prof = {}
    for pn in Q.PROFILE_PARAMS:
        pts = []
        for j in range(9):
            f = RUNS / f"profile_{pn}_{j}.json"
            pts.append(json.loads(f.read_text()) if f.exists() else None)
        Js = [p["best_J"] if p else None for p in pts]
        ok = [J is not None and J <= NEAR * Jb for J in Js]
        flat = sum(ok[i] and ok[i + 1] for i in range(8)) / 8.0     # share of bound width (inter-point intervals)
        prof[pn] = {"J": Js, "flat_share": flat, "min_J": min(J for J in Js if J is not None) if any(Js) else None,
                    "below_J_best": [j for j, J in enumerate(Js) if J is not None and J < Jb]}
    out["profiles"] = prof
    flags = {}
    for n in names:
        why = []
        if n in prof and prof[n]["flat_share"] >= 0.5:
            why.append("profile flat over >= 50 % of the bound")
        if not assess:
            why.append("restart spread not assessable")
        elif out["restart_range_norm"][n] >= 0.5:
            why.append("restart range >= 50 % of the bound")
        flags[n] = why
    out["non_identifiable"] = {n: w for n, w in flags.items() if w}
    xn = np.array(s["restarts"][[r["seed"] for r in s["restarts"]].index(s["nominal_seed"])]["best_x"])
    out["bound_active_nominal"] = [n for i, n in enumerate(names) if xn[i] < 0.01 or xn[i] > 0.99]
    out["bound_active_counts_near_best"] = {n: int(((X[:, i] < 0.01) | (X[:, i] > 0.99)).sum())
                                            for i, n in enumerate(names)}

    def caps(p):
        c = {f"G{g}": p[f"vf{g}"] * p[f"rc{g}"] * math.exp(-1.0 / p[f"a{g}"]) for g in (1, 2, 3, 4) if f"rc{g}" in p
             and f"vf{g}" in p}
        c["G4"] = p["vf3"] * p["rc4"] * math.exp(-1.0 / p["a4"])          # G4 shares v_f with G3 (§1.7 (b))
        c["B1_head"] = p["theta1"] * c["G3"]
        return c

    nom = Q.plant_params()
    out["capacity_per_lane_nominal"] = caps(nom)
    def pdict(x):
        return {k: float(np.ravel(v)[0]) for k, v in C.to_params(np.array(x)[None]).items()}

    cn = [caps(pdict(r["best_x"])) for r in near]
    out["capacity_range_near_best"] = {k: [min(c[k] for c in cn), max(c[k] for c in cn)] for k in cn[0]}
    pc = []
    for pn in Q.PROFILE_PARAMS:
        for j in range(9):
            f = RUNS / f"profile_{pn}_{j}.json"
            if f.exists():
                p = json.loads(f.read_text())
                if p["best_J"] <= NEAR * Jb:
                    pc.append(caps(pdict(p["best_x"])))
    out["capacity_range_profiles"] = {k: [min(c[k] for c in pc), max(c[k] for c in pc)] for k in pc[0]} if pc else None
    if assess:
        P = C.to_params(X)
        out["vf_rc_corr_near_best"] = {}
        for g in (1, 2, 3, 4):
            vf = P["vf3"] if g == 4 else P[f"vf{g}"]
            r = pearsonr(vf, P[f"rc{g}"]).statistic if np.ptp(vf) > 0 and np.ptp(P[f"rc{g}"]) > 0 else None
            out["vf_rc_corr_near_best"][f"G{g}"] = None if r is None else float(r)
    # per-group median (model - detector) speed 05:00-06:00 at the nominal plant
    o = M.simulate(net, {k: np.array([v]) for k, v in nom.items()}, M.Inputs(data["d0"], data["d_o"], data["beta"]),
                   record_cells=False)
    grp = np.array([net.group[s["cell"]] for s in net.stations])
    dv = (o.v_st - data["v"])[:, :, 12:24]
    m = data["mv"][:, :, 12:24] & np.isfinite(dv)
    out["median_model_minus_detector_0500_0600_kmh"] = {
        f"G{g + 1}": float(np.median(dv[:, grp == g][m[:, grp == g]])) if m[:, grp == g].any() else None
        for g in range(4)}
    return out


# ---------------------------------------------------------------- §4.8 diagnostics
def diagnostics(data: dict, net: M.Net, cs: dict, days: list, real_ev: dict, demand: dict) -> dict:
    nom = Q.plant_params()
    x = C.to_norm(nom)[None, :]
    J, parts = C.objective(x, data, net, return_parts=True)
    pr = parts["parts"][0]                                        # (D, 3)
    ok = np.isfinite(pr[:, :2])
    v0 = (np.where(ok, pr[:, :2], 0) * 0.5).sum(1) / (ok * 0.5).sum(1)
    o = M.simulate(net, {k: np.array([v]) for k, v in nom.items()}, M.Inputs(data["d0"], data["d_o"], data["beta"]),
                   record_cells=False)
    out = {"J": float(J[0]),
           "J_terms_mean": {"NRMSE_q": float(np.nanmean(pr[:, 0])), "NRMSE_v": float(np.nanmean(pr[:, 1])),
                            "NRMSE_v_congestion": float(np.nanmean(pr[:, 2]))},
           "J_terms_by_day": {d: [None if not np.isfinite(v) else float(v) for v in pr[i]] for i, d in enumerate(days)},
           "J_v0_whole_day": float(np.mean(v0)), "unscored_terms": parts["unscored_terms"],
           "clip": {"share_max": float(o.clipped_share.max()), "share_median": float(np.median(o.clipped_share)),
                    "floor_nonjam_max": float(o.floor_nonjam_share.max()),
                    "floor_jam_max": float(o.floor_jam_share.max()), "floor_jam_median": float(np.median(o.floor_jam_share))},
           "theta1": nom["theta1"]}
    origins = ["mainstream"] + [e["id"] for e in net.entrances]
    out["origin_misfit"] = {n: {"days_clipped": int((o.queue_clip_veh[:, i] > 1).sum()),
                                "clip_veh_median": float(np.median(o.queue_clip_veh[:, i])),
                                "clip_veh_max": float(o.queue_clip_veh[:, i].max()),
                                "queue_end_max": float(o.queue_end[:, i].max()),
                                "longest_queue_min_max": float(o.queue_long[:, i].max())} for i, n in enumerate(origins)}
    md = {d: Q.model_day(d, o.q_st[i], o.v_st[i], o.exit_flow[i], net, cs, real_ev[d]) for i, d in enumerate(days)}
    ev = {}
    for k in ("B1", "B2"):
        ra = [d for d in days if real_ev[d][k]]
        agree = [md[d][k]["agree"] for d in days]
        pairs = [(real_ev[d][k + "_long"]["c4"], md[d][k]["c4"]) for d in days
                 if real_ev[d][k + "_long"] and real_ev[d][k + "_long"]["heavy"] and md[d][k]["c4"]]
        heavy = [d for d in days if real_ev[d][k + "_long"] and real_ev[d][k + "_long"]["heavy"]]
        ev[k] = {"real_active_days": len(ra), "model_active_days": sum(md[d][k]["active"] for d in days),
                 "agreement_share": float(np.mean(agree)), "n_heavy_real": len(heavy), "n_heavy_matched": len(pairs),
                 "Q_dis_real_median": float(np.median([p[0]["Q_dis"] for p in pairs])) if pairs else None,
                 "Q_dis_model_median": float(np.median([p[1]["Q_dis"] for p in pairs])) if pairs else None,
                 "r_real_median": float(np.median([p[0]["r"] for p in pairs])) if pairs else None,
                 "r_model_median": float(np.median([p[1]["r"] for p in pairs])) if pairs else None,
                 "Q_dis_median_paired_diff": float(np.median([p[1]["Q_dis"] - p[0]["Q_dis"] for p in pairs]))
                 if pairs else None}
    rm, rr = [], []
    for d in days:
        if not all(real_ev[d][k + "_long"] and real_ev[d][k + "_long"]["heavy"] for k in ("B1", "B2")):
            continue
        real = [F.merge_section(d, k, real_ev[d]) for k in ("B1", "B2")]
        mod = [md[d][k]["merge"] for k in ("B1", "B2")]
        if all(real) and all(m is not None for m in mod):
            rr.append(real[1]["discharge"] / real[0]["discharge"])
            rm.append(mod[1] / mod[0])
    facts = json.loads(C.FACTS.read_text())
    ev["merge_ratio_B2_over_B1"] = {"n_days": len(rr), "model_median": float(np.median(rm)) if rm else None,
                                    "real_median_same_days": float(np.median(rr)) if rr else None,
                                    "F8_real_median": facts["F8"]["merge_ratio_B2_over_B1"]["discharge"]["median"]}
    out["events"] = ev
    # benchmarks (§4.8): threshold classifier ceiling and the demand-half climatology
    dem = np.array([demand[d] for d in days])
    med = float(np.median(dem))
    bm = {"daily_demand_median_veh": med}
    for k in ("B1", "B2"):
        y = np.array([bool(real_ev[d][k]) for d in days])
        best = (np.mean(y == y.all()) if y.size else None, None, None)
        for t in np.unique(dem):
            for sgn in (1, -1):
                pred = (dem >= t) if sgn == 1 else (dem < t)
                acc = float(np.mean(pred == y))
                if best[0] is None or acc > best[0]:
                    best = (acc, float(t), ">=" if sgn == 1 else "<")
        lo, hi = dem < med, dem >= med
        pc = {h: (float(y[m].sum()) + 0.5) / (m.sum() + 1) for h, m in (("lower", lo), ("upper", hi))}
        brier = float(np.mean([(pc["upper" if hi[i] else "lower"] - y[i]) ** 2 for i in range(len(y))]))
        bm[k] = {"real_active": int(y.sum()), "n": int(y.size), "threshold_classifier_accuracy": best[0],
                 "threshold": best[1], "direction": best[2], "threshold_brier": 1 - best[0],
                 "climatology": {"p_lower": pc["lower"], "p_upper": pc["upper"], "n_lower": int(lo.sum()),
                                 "n_upper": int(hi.sum()), "R_lower": int(y[lo].sum()), "R_upper": int(y[hi].sum()),
                                 "in_sample_brier": brier}}
    out["benchmarks"] = bm
    return out


def theta1_merge_profile(data, net, cs, days, real_ev) -> list:
    """§4.5: the model's B2/B1 merge-section ratio along theta1's profile (calibration days)."""
    pts = [json.loads((RUNS / f"profile_theta1_{j}.json").read_text()) for j in range(9)
           if (RUNS / f"profile_theta1_{j}.json").exists()]
    if not pts:
        return []
    X = np.array([p["best_x"] for p in pts])
    P, D = len(pts), len(days)
    o = M.simulate(net, C.to_params(X), M.Inputs(data["d0"], data["d_o"], data["beta"]), n_param_sets=P,
                   record_cells=False)
    res = []
    for pi, p in enumerate(pts):
        rm = []
        for di, d in enumerate(days):
            b = pi * D + di
            if not all(real_ev[d][k + "_long"] and real_ev[d][k + "_long"]["heavy"] for k in ("B1", "B2")):
                continue
            md = Q.model_day(d, o.q_st[b], o.v_st[b], o.exit_flow[b], net, cs, real_ev[d])
            if all(md[k]["merge"] is not None for k in ("B1", "B2")):
                rm.append(md["B2"]["merge"] / md["B1"]["merge"])
        th = float(C.to_params(X[pi][None])["theta1"][0])
        res.append({"point": p["point"], "theta1": th, "J": p["best_J"], "n_days": len(rm),
                    "model_merge_ratio_median": float(np.median(rm)) if rm else None})
    return res


# ---------------------------------------------------------------- report
def _f(x, nd=3):
    return "n/a" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def report_md(res: dict) -> str:
    cf, dg, idn, sh = res["capacity_factors"]["nominal"], res["diagnostics"], res["identifiability"], res["stephalving"]
    L = ["# U.S.169 SB METANET plant: calibration freeze", "",
         f"Protocol: `{res['protocol']}` (v3, binding). Stage: {res['stage']}{'; route stop record' if 'stop' in res else ''}. Variant `{res['variant']}` (§1.7 step (b), "
         f"G4). pycma {res['pycma']}. Calibration days only: {res['days']['n']} usable. Raw runs: "
         f"`{RUNS}`; full numbers in `metanet_calibration.json`.", "",
         f"**Route after the freeze: {res['route']}.**", "",
         "## Fit (§4.3–4.4)", "",
         f"- Nominal plant: restart seed {res['nominal_seed']}, J = {_f(res['nominal_J'], 4)} "
         f"(continued to 8,000 evaluations: {res['convergence']['continued_to_8000']}).",
         f"- J terms (mean over days): NRMSE_q {_f(dg['J_terms_mean']['NRMSE_q'])}, NRMSE_v "
         f"{_f(dg['J_terms_mean']['NRMSE_v'])}, NRMSE_v congestion {_f(dg['J_terms_mean']['NRMSE_v_congestion'])}; "
         f"v0 whole-day J {_f(dg['J_v0_whole_day'])}.",
         "", "| seed | evals | best J | inadmissible evals | improvement last 20 % |", "|---|---|---|---|---|"]
    for r in res["convergence"]["restarts"]:
        L.append(f"| {r['seed']} | {r['evals']} | {_f(r['best_J'], 4)} | {r['inadmissible_evals']} | "
                 f"{_f(r['rel_improvement_last20pct'], 4)} |")
    L += ["", "Frozen parameters: " + ", ".join(f"{k} = {v:.4g}" for k, v in res["frozen_params"].items()) + ".", "",
          "## Step-halving (§2.5; gated as part of N0)", "",
          f"J(5 s) = {_f(sh['J_5s'], 4)}, J(2.5 s) = {_f(sh['J_2p5s'], 4)}, relative change {_f(sh['rel_change'], 4)} "
          f"(limit 0.05); P_1/P_2 episode-day sets unchanged: {sh['episode_day_sets_unchanged']}; largest per-station RMS "
          f"speed change {_f(sh['rms_speed_change_kmh_max_station'], 2)} km/h. **{'PASS' if sh['PASS'] else 'FAIL'}**."
          + "".join(f" {k} days only at 5 s: {sorted(set(sh[k + '_days_5s']) - set(sh[k + '_days_2p5s']))}; only at "
                    f"2.5 s: {sorted(set(sh[k + '_days_2p5s']) - set(sh[k + '_days_5s']))}."
                    for k in ("P1", "P2") if sh[k + "_days_5s"] != sh[k + "_days_2p5s"]), "",
          "## Identifiability (§4.5; reported, not gated)", "",
          f"- Near-best restarts (J ≤ 1.02 J_best): {idn['n_near_best']} ({idn['near_best_seeds']}).",
          f"- Non-identifiable: " + ("; ".join(f"{k} ({', '.join(v)})" for k, v in idn["non_identifiable"].items())
                                    or "none") + ".",
          f"- Bound-active at the nominal: {idn['bound_active_nominal'] or 'none'}.",
          f"- Capacity per lane at the nominal (veh/h/lane): " + ", ".join(f"{k} {v:.0f}" for k, v in
                                                                         idn["capacity_per_lane_nominal"].items()) + ".",
          f"- Median model − detector speed 05:00–06:00 (km/h): {idn['median_model_minus_detector_0500_0600_kmh']}.",
          "- Profiles are re-optimised with 600 evaluations per point; under-optimisation can only make a profile look "
          "less flat.", "", "| parameter | flat share (J ≤ 1.02 J_best) | min profile J |", "|---|---|---|"]
    for k, v in idn["profiles"].items():
        L.append(f"| {k} | {_f(v['flat_share'], 3)} | {_f(v['min_J'], 4)} |")
    L += ["", "θ1 profile and the model's B2/B1 merge-section ratio: " + "; ".join(
        f"θ1 {p['theta1']:.3f}: J {p['J']:.4f}, ratio {_f(p['model_merge_ratio_median'])} (n {p['n_days']})"
        for p in dg["theta1_merge_profile"]) + ".", "",
          "## Capacity factors c1, c2 (§4.7)", "",
          f"- c2* = {_f(cf['c2_star'], 2)}; build check at {cf['build_check_c2']}: days {cf['build_check_days']}.",
          f"- Estimable: **{cf['estimable']}** (rules failed: {cf['rules_failed'] or 'none'}); spread used for the "
          f"stochastic rows: **{cf.get('spread_used', 'none')}**."]
    if "F_hat" in cf:
        for k in ("B1", "B2"):
            fh, tb = cf["F_hat"][k], cf["tobit"][k]
            L.append(f"- {k}: {fh['n_exact']} exact, {fh['n_censored']} censored; KM median {_f(fh['median'], 2)}, upper "
                     f"atom {_f(fh['upper_atom_mass'])}, mass < 1 {_f(fh['mass_below_1'])}, > 1 {_f(fh['mass_above_1'])}; "
                     f"Tobit μ {_f(tb.get('mu'))}, σ {_f(tb.get('sigma'))} (usable {tb['usable']}).")
        L.append(f"- Non-reproducible days: {len(cf['non_reproducible'])} "
                 f"(share of real-active days {_f(cf['non_reproducible_share_of_real_active_days'])}); non-monotone "
                 f"day-lines: {len(cf['non_monotone'])}.")
    L += ["", "## Calibration-day diagnostics (§4.8)", ""]
    for k in ("B1", "B2"):
        e = dg["events"][k]
        L.append(f"- {k}: real-active {e['real_active_days']}, model-active {e['model_active_days']}, agreement "
                 f"{_f(e['agreement_share'], 2)}; heavy matched {e['n_heavy_matched']}/{e['n_heavy_real']}; Q_dis real "
                 f"{_f(e['Q_dis_real_median'], 0)} vs model {_f(e['Q_dis_model_median'], 0)} veh/h; r real "
                 f"{_f(e['r_real_median'])} vs model {_f(e['r_model_median'])}.")
    mr = dg["events"]["merge_ratio_B2_over_B1"]
    L += [f"- Merge-section ratio B2/B1: model {_f(mr['model_median'])} vs real {_f(mr['real_median_same_days'])} on the "
          f"same {mr['n_days']} days (F8: {_f(mr['F8_real_median'])}).",
          f"- θ1 = {_f(dg['theta1'])}. Clipping: max share {_f(dg['clip']['share_max'], 5)}; non-jam v_min floor max "
          f"{_f(dg['clip']['floor_nonjam_max'], 5)}; in-jam floor max {_f(dg['clip']['floor_jam_max'], 5)} (reported only).",
          "- Origin misfits (days with supply-clipped volume > 1 veh): " + ", ".join(
              f"{k} {v['days_clipped']}" for k, v in dg["origin_misfit"].items() if v["days_clipped"]) + ".", "",
          "Benchmarks fixed before validation:", ""]
    for k in ("B1", "B2"):
        b = dg["benchmarks"][k]
        c = b["climatology"]
        thr = (f"demand {b['direction']} {_f(b['threshold'], 0)} veh" if b["threshold"] is not None
               else "every day active: the constant classifier")
        L.append(f"- {k}: best daily-demand threshold classifier accuracy {_f(b['threshold_classifier_accuracy'], 3)} "
                 f"({thr}); demand-half climatology p_lower "
                 f"{_f(c['p_lower'])} ({c['R_lower']}/{c['n_lower']}), p_upper {_f(c['p_upper'])} "
                 f"({c['R_upper']}/{c['n_upper']}), split at {dg['benchmarks']['daily_demand_median_veh']:.0f} veh.")
    L += ["", "## Ensemble candidates (§4.6)", "",
          res["ensemble_candidates"]["rule"] + ".", ""]
    for c in res["ensemble_candidates"]["candidates"]:
        L.append(f"- seed {c['seed']}: J {c['J']:.4f}, distance {c['distance']:.3f}, step-halving "
                 f"{c.get('stephalving_PASS')}.")
    if not res["ensemble_candidates"]["candidates"]:
        L.append("- none (no other restart within 1.02 J_best).")
    if "stop" in res:
        L += ["", "## Route stop", "", f"**{res['stop']['outcome']}.** Author decision: {res['stop']['author_decision']}.", ""]
        pb = res["stop"].get("step_probe")
        if pb:
            L.append(f"Step probe on {pb['day']} (real P_2 episodes {pb['real_P2_episodes']}):")
            for T, v in pb["steps"].items():
                L.append(f"- T = {T} s: P_2 episodes {v['P2_episodes']}, max qualifying bins in 7 = "
                         f"{v['max_qualifying_in_7']}, near misses {v['near_miss_bins']}"
                         + (f", RMS / max change of the Pioneer Tr speed vs the previous step "
                            f"{v['rms_change_S1140_mph_vs_previous']:.2f} / {v['max_abs_change_S1140_mph_vs_previous']:.1f} mph"
                            if "rms_change_S1140_mph_vs_previous" in v else "") + ".")
        L += [""] + [f"- {n}" for n in res["stop"]["notes"]]
    L += ["", "## Disclosures", "",
          "- The boundary station (Minnetonka Blvd) has no c_s (not in a §3.2.4 group); the observation operator uses "
          "c = 1 there. Dropped stations use their computed c_s (§3.2.4).",
          "- Relocation rule (a) is evaluated on 05:00–23:00 bin means (the warm-up hour is excluded).",
          "- Profile flatness is measured as the share of the 8 inter-point intervals whose two end points both have "
          "J ≤ 1.02 J_best.",
          "- Censoring points c_low on a non-monotone line fall back to the arg-min component (flagged per day).",
          "- The threshold classifier is evaluated in both directions (demand ≥ t and < t); its Brier score is "
          "1 − accuracy.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------- driver
def finalize() -> dict:
    import cma
    s = Q.summary()
    data = C.load_data()
    days = [str(d) for d in data["days"]]
    net = M.build_network(C.VARIANT)
    p1 = Q.part1()
    cs = p1["c_s"]
    real_ev = {d: F.day_events(d) for d in days}
    real_active = {d: {k: bool(real_ev[d][k]) for k in ("B1", "B2")} for d in days}
    demand = {d: float(data["d0"][i, M.SCORE_FROM_BIN:].sum() * 5 / 60) for i, d in enumerate(days)}
    nom_seed = s["nominal_seed"]
    sh = json.loads((RUNS / f"stephalving_{nom_seed}.json").read_text())
    ident = identifiability(s, data, net)
    near = [r for r in s["restarts"] if r["best_J"] <= NEAR * s["nominal_J"] and r["seed"] != nom_seed]
    lo_hi = dict(zip(C.NAMES, C.bounds()))
    xn = C.to_norm(Q.plant_params())
    ki = [C.NAMES.index(k) for k in ENS_KEYS]
    cand = sorted(({"seed": r["seed"], "J": r["best_J"],
                    "distance": float(np.linalg.norm(np.array(r["best_x"])[ki] - xn[ki]))} for r in near),
                  key=lambda c: -c["distance"])
    cap = {"nominal": capacity_factors(nom_seed, days, real_active, demand, real_ev)}
    for c in cand:
        if all((RUNS / f"grid_{c['seed']}_c2_{i:02d}.json").exists() for i in range(len(Q.GRID))):
            cap[str(c["seed"])] = capacity_factors(c["seed"], days, real_active, demand, real_ev)
        f = RUNS / f"stephalving_{c['seed']}.json"
        c["stephalving_PASS"] = json.loads(f.read_text())["PASS"] if f.exists() else None
    diag = diagnostics(data, net, cs, days, real_ev, demand)
    diag["theta1_merge_profile"] = theta1_merge_profile(data, net, cs, days, real_ev)
    res = {
        "protocol": "docs/plans/day_pattern_metanet_protocol_v3.md", "stage": "freeze (before any validation run)",
        "variant": C.VARIANT, "pycma": cma.__version__,
        "days": {"calibration_usable": days, "n": len(days), "facts": str(C.FACTS.relative_to(C.REPO))},
        "network": {"N": net.N, "km_from": net.km_from.round(3).tolist(), "km_to": net.km_to.round(3).tolist(),
                    "lanes": net.lam.tolist(), "group": [int(g) + 1 for g in net.group],
                    "b1_cells_1based": [i + 1 for i in net.b1_cells], "b2_cells_1based": [i + 1 for i in net.b2_cells],
                    "head1_1based": net.head1 + 1, "phi_cell_1based": net.phi_cell + 1,
                    "entrances": {e["id"]: e["cell"] + 1 for e in net.entrances},
                    "exits": {x["id"]: x["cell"] + 1 for x in net.exits}},
        "bounds": {n: list(b) for n, b in lo_hi.items()},
        "frozen_params": Q.plant_params(), "nominal_seed": nom_seed, "nominal_J": s["nominal_J"],
        "convergence": {"budget": s["budget"], "continued_to_8000": s["continued_to_8000"],
                        "restarts": [{k: r[k] for k in ("seed", "evals", "best_J", "final_sigma", "cov_condition",
                                                         "inadmissible_evals", "rel_improvement_last20pct")}
                                     for r in s["restarts"]]},
        "stephalving": {k: v for k, v in sh.items() if k != "rms_speed_change_kmh_by_station"}
        | {"rms_speed_change_kmh_max_station": max(sh["rms_speed_change_kmh_by_station"].values())},
        "identifiability": ident,
        "ensemble_candidates": {"rule": "J <= 1.02 J_best, farthest first in normalised (tau, nu, kappa, delta_m, phi);"
                                        " admissibility filter (N0, deterministic rows, stochastic rows) runs at §8.6 "
                                        "step 5 on validation days as a filter only", "candidates": cand},
        "capacity_factors": cap, "diagnostics": diag,
        "route": "STOP (N0 FAIL: step-halving)" if not sh["PASS"] else "continue to the plant gate (§5)",
    }
    if not sh["PASS"]:
        pr = RUNS / "step_probe_20230517.json"
        first = RUNS / f"stephalving_{nom_seed}_mask_isfinite.json"
        res["stop"] = {"outcome": STOP_OUTCOME, "author_decision": "accept the route stop as pre-registered "
                       "(option (a), 2026-10-06)", "notes": RECORD_NOTES,
                       "step_probe": json.loads(pr.read_text()) if pr.exists() else None,
                       "stephalving_first_outcome": {k: v for k, v in json.loads(first.read_text()).items()
                                                     if k != "rms_speed_change_kmh_by_station"} if first.exists() else None}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "metanet_calibration.json").write_text(json.dumps(res, indent=1, default=float))
    (OUT / "metanet_calibration.md").write_text(report_md(res))
    return {"nominal_J": s["nominal_J"], "stephalving_PASS": sh["PASS"], "c2_star": cap["nominal"]["c2_star"],
            "estimable": cap["nominal"]["estimable"], "rules_failed": cap["nominal"]["rules_failed"],
            "spread": cap["nominal"].get("spread_used"), "n_candidates": len(cand)}


if __name__ == "__main__":
    print(json.dumps(finalize()))
    sys.exit(0)
