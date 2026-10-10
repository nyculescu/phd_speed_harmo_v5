"""U.S.169 SB METANET post-calibration stage, protocol v4 (v3 §2.5 step-halving at T vs T/2 = 0.75 vs 0.375 s,
§4.5 profiles with the §A3 rules, §4.7 capacity-factor grid on v4 cells, §A12 P11-k). Calibration days only; no
validation day is touched here. The freeze itself is in metanet_freeze.

python -m vsl_lab.jobs.metanet_postcal stephalving [--plant SEED]
python -m vsl_lab.jobs.metanet_postcal grid --plant SEED --c2-index I   # one c2 value x all 41 c1 values x all days
python -m vsl_lab.jobs.metanet_postcal grid-run --plant SEED --gate-ok  # the 41 grid jobs in parallel
python -m vsl_lab.jobs.metanet_postcal profile --param P --point J
python -m vsl_lab.jobs.metanet_postcal profile-run --gate-ok            # 8 x 9 profile jobs
A plant is identified by its CMA-ES restart seed (the nominal plant = the best restart).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import math
import sys
import time

import numpy as np

from vsl_lab.data import metanet_events as V
from vsl_lab.data import metanet_inputs as I
from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.plants import metanet as M

RUNS = C.RUNS
GRID = np.round(np.arange(0.80, 1.2001, 0.01), 2)          # G: 41 values
EV0 = M.SCORE_FROM_BIN                                       # event bin 0 (05:00) = model bin 12
NEV = 216                                                    # event bins 05:00-23:00
PROFILE_PARAMS = ["vf3", "rc3", "tau", "nu", "kappa", "delta_m", "phi", "theta1"]
RELOC_PAIR = ("S1141", "S1610")                              # (Old Shakopee Rd, T.H.101), §4.7 (b)
PAIR = {"B1": I.P1, "B2": I.P2}
DOWN = {"B1": "S1140", "B2": "S1141"}
EXIT_IN = {"B1": "X12", "B2": "X13"}
OVERLAP_BINS = 12                                            # +-60 min


# ---------------------------------------------------------------- plants
def summary(kind: str = "base") -> dict:
    """The CMA-ES summary of the base plant ('base') or of F1 ('f1', §6.1)."""
    return json.loads((RUNS / ("cma_summary.json" if kind == "base" else "f1_cma_summary.json")).read_text())


def plant_record(seed: int | None = None) -> dict:
    """The stored restart record (best_x is the vector CMA-ES evaluated; never rebuilt by a round trip). Seeds are
    unique across the base (7,191,010-017) and F1 (7,191,018-025) restarts."""
    s = summary()
    seed = s["nominal_seed"] if seed is None else seed
    for kind in ("base", "f1"):
        try:
            sk = s if kind == "base" else summary("f1")
        except FileNotFoundError:
            continue
        r = next((r for r in sk["restarts"] if r["seed"] == seed), None)
        if r is not None:
            return r
    raise KeyError(f"no restart record for seed {seed}")


def plant_params(seed: int | None = None) -> dict:
    """Frozen parameters of a restart (None = the nominal base plant); F1 plants carry Delta and eta."""
    return {k: float(v) for k, v in plant_record(seed)["best_params"].items()}


def is_f1(params_or_x) -> bool:
    return ("Delta" in params_or_x) if isinstance(params_or_x, dict) else len(params_or_x) == len(C.NAMES) + 2


def simf(net: M.Net, params: dict, inp: M.Inputs, **kw):
    """M.simulate with F1 switched on when the parameter set carries Delta and eta (§6.1)."""
    from vsl_lab.jobs.metanet_f1 import split_f1
    base, f1 = split_f1(params)
    return M.simulate(net, base, inp, f1=f1, **kw)


def objective_for(X: np.ndarray, data: dict, net: M.Net, T_s: float = C.T_RUN, return_parts: bool = False):
    """The base or the F1 objective, by the vector length."""
    if X.shape[1] == len(C.NAMES) + 2:
        from vsl_lab.jobs import metanet_f1
        return metanet_f1.objective(X, data, net, T_s=T_s, return_parts=return_parts)
    return C.objective(X, data, net, T_s=T_s, return_parts=return_parts)


def part1() -> dict:
    return C.part1()                                         # v3 raw input, read-only, sha256-verified (§A9)


def cell_rc(net: M.Net, p: dict, c1: float = 1.0, c2: float = 1.0) -> np.ndarray:
    """Per-cell critical density as simulate() applies it (G-group rc, c1 on B1, theta1 on the head, c2 on B2)."""
    rc = np.array([p.get(f"rc{g + 1}", p["rc3"]) for g in net.group], float)
    rc[net.b1_cells] *= c1
    rc[net.head1] *= p["theta1"]
    rc[net.b2_cells] *= c2
    return rc


# ---------------------------------------------------------------- model-side events (§5.1)
def model_speeds(day: str, v_st: np.ndarray, net: M.Net, cs: dict) -> tuple:
    """Model event-layer speeds (mph) through the observation operator v / c_s (computed c_s, dropped stations
    included, §3.2.4), masked per bin by the real event-layer series and per station-day by real event validity.
    The boundary station has no c_s (it is not in any §3.2.4 group): c = 1 (disclosed)."""
    sids = [s["id"] for s in net.stations]
    speeds, valid = {}, {}
    for sid in I.EVENT_STATIONS:
        real = I.event_station(day, sid)
        c = cs[sid]["c_s"] if sid in cs else 1.0
        speeds[sid] = V.observe(v_st[sids.index(sid)][EV0:EV0 + NEV], c, real["v"], real["valid"])
        valid[sid] = real["valid"]
    return speeds, valid


def model_pairs(day: str, v_st: np.ndarray, net: M.Net, cs: dict) -> dict:
    """Corridor rule (EA-2) on the model's event-layer speeds (model_speeds)."""
    speeds, valid = model_speeds(day, v_st, net, cs)
    return {k: e for k, e in I.event_pairs(day, speeds=speeds, valid=valid).items() if e}


def longest_run(b: np.ndarray) -> int:
    best = run = 0
    for x in b:
        run = run + 1 if x else 0
        best = max(best, run)
    return best


RELOC_EXCLUDE_ADJACENT_JAM = True     # protocol v4 addendum 2026-10-07 (D4.10): acceleration-zone bins excluded


def relocation(pairs: dict, rho_bins: np.ndarray, rc_cells: np.ndarray, first_cell: int, n_consec: int = 3,
               exclude_adjacent_jam: bool | None = None) -> dict:
    """§4.7 / v4 §A1: (a) a cell downstream of B2 (index >= first_cell) with 5-min mean density > rho_cr for >= 3
    consecutive bins, or (b) a model episode at (Old Shakopee Rd, T.H.101). rho_bins (N, bins); rc_cells (N,) or
    (N, bins) effective rho_cr. exclude_adjacent_jam: bins in which B2's last scaled cell (first_cell - 1) is itself
    over-critical do not count (the acceleration zone of an active B2 jam)."""
    excl = RELOC_EXCLUDE_ADJACENT_JAM if exclude_adjacent_jam is None else exclude_adjacent_jam
    rc = rc_cells if np.ndim(rc_cells) == 2 else np.asarray(rc_cells)[:, None]
    over = rho_bins > rc
    mask = ~over[first_cell - 1] if excl else np.ones(rho_bins.shape[1], bool)
    cells = [i for i in range(first_cell, rho_bins.shape[0]) if longest_run(over[i] & mask) >= n_consec]
    pair = bool(pairs.get(RELOC_PAIR))
    return {"flag": bool(cells) or pair, "cells": cells, "pair": pair}


def p11_day(day: str, v_st: np.ndarray, rho_bins: np.ndarray, rc_bins: np.ndarray, net: M.Net, cs: dict,
            pairs: dict | None = None) -> dict:
    """§A12 P11-k for one model day. Qualifying bin: inside a model P_k episode with the pair condition on detector
    scale; backed: a congested cell (bin-mean rho > bin-mean effective rho_cr) strictly between the pair's station
    cells (P_1: cells 26-31; P_2: cells 33-34). Unbacked day: episodes whose pooled qualifying bins are < 50 % backed.
    Also §A13 item 4: per P_2 episode, the most upstream congested cell from Pioneer Tr's cell on (1-based)."""
    speeds, valid = model_speeds(day, v_st, net, cs)
    mp = pairs if pairs is not None else {k: e for k, e in I.event_pairs(day, speeds=speeds, valid=valid).items() if e}
    scell = {st["id"]: st["cell"] for st in net.stations}
    cong_all = rho_bins[:, EV0:EV0 + NEV] > rc_bins[:, EV0:EV0 + NEV]          # (N, 216)
    return p11_core(speeds, mp, cong_all, scell)


def p11_core(speeds: dict, mp: dict, cong_all: np.ndarray, scell: dict) -> dict:
    """Pure §A12 classifier (test 21): speeds (mph, detector scale) per station on event bins, model episodes per
    pair, congested-cell matrix (N, bins), station -> 0-based cell."""
    out = {}
    for k, (u, d) in (("B1", I.P1), ("B2", I.P2)):
        eps = [tuple(e) for e in mp.get((u, d), [])]
        between = list(range(scell[u] + 1, scell[d]))
        with np.errstate(invalid="ignore"):
            cond = np.nan_to_num((speeds[u] < 40.0) & ((speeds[d] - speeds[u]) >= 20.0)).astype(bool)
        qual = [b for s_, e_ in eps for b in range(s_, e_ + 1) if cond[b]]
        backed = [b for b in qual if cong_all[between, b].any()]
        share = len(backed) / len(qual) if qual else None
        unb = bool(eps) and (share is None or share < 0.5)
        r = {"episodes": [list(e) for e in eps], "n_qualifying": len(qual), "n_backed": len(backed), "share": share,
             "unbacked": unb}
        if unb and qual:
            dn = [int(np.flatnonzero(cong_all[:, b]).max()) + 1 for b in qual if cong_all[:, b].any()]
            r["most_downstream_congested_cell"] = max(dn) if dn else None
        if k == "B2":
            ups = []
            for s_, e_ in eps:
                cells = sorted({int(c) + 1 for b in range(s_, e_ + 1)
                                for c in np.flatnonzero(cong_all[scell[u]:, b]) + scell[u]})
                ups.append({"episode": [s_, e_], "most_upstream_congested_cell": cells[0] if cells else None,
                            "only_35_39": bool(cells) and min(cells) >= scell[d] + 1})
            r["a13_item4"] = ups
        out[k] = r
    return out


def p11_verdict(days_res: dict) -> dict:
    """§A12 criterion per k: PASS iff unbacked episode-days <= max(2, ceil(0.10 n))."""
    n = len(days_res)
    tol = max(2, math.ceil(0.10 * n))
    out = {"n_days": n, "tolerance": tol}
    for k in ("B1", "B2"):
        unb = [d for d, r in days_res.items() if r[k]["unbacked"]]
        q = sum(r[k]["n_qualifying"] for r in days_res.values())
        bk = sum(r[k]["n_backed"] for r in days_res.values())
        out[k] = {"unbacked_days": unb, "n_unbacked": len(unb), "pooled_backed_share": bk / q if q else None,
                  "most_downstream_congested_cell": {d: days_res[d][k].get("most_downstream_congested_cell")
                                                     for d in unb},
                  "PASS": len(unb) <= tol}
    out["PASS"] = out["B1"]["PASS"] and out["B2"]["PASS"]
    return out


def c2_star(reloc_by_c2: dict, grid=GRID):
    """Largest g in the grid such that no pair with c2 <= g relocates on any day (reloc_by_c2: c2 -> bool, already
    OR-ed over c1 and days). None if the smallest grid value relocates (c2* < grid minimum)."""
    best = None
    for g in grid:
        if reloc_by_c2[float(g)]:
            break
        best = float(g)
    return best


def spurious(model: dict, real: dict) -> list:
    """P8 (i)-(ii): model episodes at pairs outside {P_1, P_2} with no real episode that day at that pair or at any
    pair sharing a station with it. Returns the offending pairs."""
    out = []
    for p, eps in model.items():
        if p in (I.P1, I.P2) or not eps:
            continue
        if not [q for q, e in real.items() if e and (set(q) & set(p))]:
            out.append(p)
    return out


def overlaps(a: list, b: list, tol: int = OVERLAP_BINS) -> bool:
    return any(s <= e2 + tol and s2 <= e + tol for s, e in a for s2, e2 in b)


def model_day(day: str, q_st: np.ndarray, v_st: np.ndarray, x_flow: np.ndarray, net: M.Net, cs: dict,
              real_ev: dict) -> dict:
    """Model side of one day for the §4.8 diagnostics and the gate: episodes, B_k-active agreement (P3 rule),
    C4 block on the model episode matched to the real longest episode (B1 censored at the real t_c), and the
    merge-section discharge. real_ev = metanet_facts.day_events(day)."""
    sids = [s["id"] for s in net.stations]
    xids = [x["id"] for x in net.exits]
    mp = model_pairs(day, v_st, net, cs)
    out = {"pairs": mp}
    for k in ("B1", "B2"):
        me, re = mp.get(PAIR[k], []), [tuple(e) for e in real_ev[k]]
        agree = overlaps(me, re) if re else not me
        r = {"episodes": me, "active": bool(me), "agree": bool(agree), "c4": None, "merge": None}
        lg = real_ev[k + "_long"]
        if lg is not None and me:
            ri = re.index(tuple(lg["ep"]))
            m = V.match_episodes(re, me)
            if ri in m:
                mep = me[m[ri]]
                cap = real_ev["censor"].get(ri) if k == "B1" else None
                real_q = I.event_station(day, DOWN[k])
                qm = np.where(np.isfinite(real_q["q"]), q_st[sids.index(DOWN[k])][EV0:EV0 + NEV], np.nan)
                c = V.c4(qm, tuple(mep), 2, end_cap=cap)
                r.update({"matched": list(mep), "c4": c})
                if c is not None:
                    a, b = c["window"]
                    xm = x_flow[xids.index(EXIT_IN[k])][EV0:EV0 + NEV]
                    r["merge"] = float(np.nanmean((qm[a:b] + xm[a:b]) / 2.0))
        out[k] = r
    return out


# ---------------------------------------------------------------- capacity-factor grid (§4.7)
def grid_job(seed: int, c2_index: int, p: dict | None = None, runs: Path | None = None, jd=None):
    """jd (protocol v5 §B3): a J5 evaluator; each row then also carries J_d (the v5 selector) and b1cells_qual (a
    cell of 28-31 congested in a P_1 qualifying bin; c1-inert report). p, runs: the v5 plant and raw directory."""
    data = C.load_data()
    days = [str(d) for d in data["days"]]
    net = M.build_network(C.VARIANT)
    cs = part1()["c_s"]
    p = plant_params(seed) if p is None else p
    c2 = float(GRID[c2_index])
    P, D = len(GRID), len(days)
    o = simf(net, {k: np.full(P, v) for k, v in p.items()}, M.Inputs(data["d0"], data["d_o"], data["beta"]),
                   n_param_sets=P, c1=GRID.copy(), c2=np.full(P, c2), record_cells=True)
    real = {d: {k: e for k, e in I.event_pairs(d).items() if e} for d in days}
    a13_5 = abs(c2 - 1.0) < 1e-9                              # §A13 item 5 runs on the c2 = 1.00 slice only
    if a13_5:
        from vsl_lab.data import metanet_facts as F
        rev = {d: F.day_events(d) for d in days}
    res = []
    for pi, c1 in enumerate(GRID):
        rc = cell_rc(net, p, float(c1), c2)
        for di, day in enumerate(days):
            b = pi * D + di
            mp = model_pairs(day, o.v_st[b], net, cs)
            rl = relocation(mp, o.rho_cell[b][:, EV0:], o.rc_cell[b][:, EV0:], net.b2_cells[-1] + 1)
            sp = spurious(mp, real[day])
            row = {"day": day, "c1": float(c1), "c2": c2, "Z": bool(sp) or rl["flag"], "reloc": rl["flag"],
                   "reloc_cells": [int(i) + 1 for i in rl["cells"]], "reloc_pair": rl["pair"],
                   "spurious": [list(x) for x in sp],
                   "L": V.nrmse(o.v_st[b], data["v"][di], data["mc"][di]),
                   "clip": float(o.clipped_share[b])}
            pk = p11_day(day, o.v_st[b], o.rho_cell[b], o.rc_cell[b], net, cs, pairs=mp)
            for k in ("B1", "B2"):
                me = mp.get(PAIR[k], [])
                row["E" + k[1]] = bool(me)
                row["O" + k[1]] = overlaps(me, real[day].get(PAIR[k], []))
                row["backed_share_" + k] = pk[k]["share"]           # §A13 item 7 (report-only)
            if jd is not None:
                from vsl_lab.jobs import metanet_j5 as J5m
                row["J_d"] = J5m.j_day(jd.day_items(di, o.q_st[b], o.v_st[b], o.exit_flow[b], o.rho_cell[b],
                                                    o.rc_cell[b]), jd.w)
                sp_, _ = model_speeds(day, o.v_st[b], net, cs)
                u_, d_ = PAIR["B1"]
                with np.errstate(invalid="ignore"):
                    cond = np.nan_to_num((sp_[u_] < 40.0) & ((sp_[d_] - sp_[u_]) >= 20.0)).astype(bool)
                cong = o.rho_cell[b][:, EV0:EV0 + NEV] > o.rc_cell[b][:, EV0:EV0 + NEV]
                row["b1cells_qual"] = bool(any(cong[27:31, t].any() for s_, e_ in mp.get(PAIR["B1"], [])
                                               for t in range(s_, e_ + 1) if cond[t]))
            if a13_5 and rev[day]["B1"] and not rev[day]["B2"] and row["E1"] and not row["E2"] and not rl["flag"]:
                md = model_day(day, o.q_st[b], o.v_st[b], o.exit_flow[b], net, cs, rev[day])
                row["b1_discharge_vph"] = None if md["B1"]["merge"] is None else 2.0 * md["B1"]["merge"]
            res.append(row)
    out = (RUNS if runs is None else runs) / f"grid_{seed}_c2_{c2_index:02d}.json"
    out.write_text(json.dumps(res))
    return out


# ---------------------------------------------------------------- step-halving (§2.5, gated as part of N0)
def _fin(x):
    return None if x is None or not np.isfinite(x) else round(float(x), 3)


def margins_pair(sp_T: dict, sp_T2: dict) -> dict:
    """§A2 report-only margins per pair at T and T/2: best 7-bin count - 5, and the signed m_v = 40 - v_u and
    m_d = (v_d - v_u) - 20 (mph, detector scale) at every bin of every window reaching the maximum plus every bin
    whose status differs between T and T/2."""
    out = {}
    for k, (u, d) in (("B1", I.P1), ("B2", I.P2)):
        rec, conds = {}, {}
        for lab, sp in (("T", sp_T), ("T_half", sp_T2)):
            with np.errstate(invalid="ignore"):
                conds[lab] = np.nan_to_num((sp[u] < 40.0) & ((sp[d] - sp[u]) >= 20.0)).astype(int)
        diff = set(np.flatnonzero(conds["T"] != conds["T_half"]).tolist())
        for lab, sp in (("T", sp_T), ("T_half", sp_T2)):
            w = np.convolve(conds[lab], np.ones(7, int), mode="valid")
            wm = int(w.max()) if w.size else 0
            bins = set(diff)
            if wm > 0:
                for j in np.flatnonzero(w == wm):
                    bins |= set(range(int(j), int(j) + 7))
            rec[lab] = {"count_margin": wm - 5,
                        "bins": {int(b): {"m_v": _fin(40.0 - sp[u][b]), "m_d": _fin(sp[d][b] - sp[u][b] - 20.0)}
                                 for b in sorted(bins)}}
        rec["status_differs_bins"] = sorted(int(b) for b in diff)
        out[k] = rec
    return out


def stephalving(seed: int | None = None) -> dict:
    """§A2: T vs T/2 on all usable calibration days: |dJ|/J <= 0.05 and identical P_1, P_2 episode-day sets."""
    data = C.load_data()
    days = [str(d) for d in data["days"]]
    net = M.build_network(C.VARIANT)
    cs = part1()["c_s"]
    rec = plant_record(seed)
    x = np.array(rec["best_x"], float)[None, :]
    sids = [s["id"] for s in net.stations]
    Ts = (C.T_RUN, C.T_RUN / 2.0)
    out = {}
    for T in Ts:
        J, parts = objective_for(x, data, net, T_s=T, return_parts=True)
        if parts["a3_violation"][0]:
            raise RuntimeError("the stored optimum is A3-infeasible: step-halving would pass vacuously")
        if T == Ts[0] and abs(float(J[0]) - rec["best_J"]) > 1e-12 * max(1.0, abs(rec["best_J"])):
            raise RuntimeError(f"J(T) {float(J[0])!r} != calibrated best J {rec['best_J']!r}: plant not reproduced")
        o = simf(net, {k: v for k, v in plant_params(seed).items()}, M.Inputs(data["d0"], data["d_o"], data["beta"]),
                 record_cells=False, T_s=T)
        mp = [model_pairs(d, o.v_st[i], net, cs) for i, d in enumerate(days)]
        out[T] = {"J": float(J[0]), "v": o.v_st, "clip_max": float(o.clipped_share.max()),
                  "P1": sorted(d for d, m in zip(days, mp) if m.get(I.P1)),
                  "P2": sorted(d for d, m in zip(days, mp) if m.get(I.P2)),
                  "speeds": {d: model_speeds(d, o.v_st[i], net, cs)[0] for i, d in enumerate(days)}}
    T1, T2 = Ts
    rel = abs(out[T2]["J"] - out[T1]["J"]) / out[T1]["J"]
    same = out[T2]["P1"] == out[T1]["P1"] and out[T2]["P2"] == out[T1]["P2"]
    dv = out[T2]["v"][:, :, EV0:] - out[T1]["v"][:, :, EV0:]
    rms = {sid: float(np.sqrt(np.nanmean(dv[:, j] ** 2))) for j, sid in enumerate(sids)}
    differ = sorted((set(out[T1]["P1"]) ^ set(out[T2]["P1"])) | (set(out[T1]["P2"]) ^ set(out[T2]["P2"])))
    margins = {d: margins_pair(out[T1]["speeds"][d], out[T2]["speeds"][d]) for d in days}
    res = {"protocol": C.PROTOCOL, "plant_seed": seed if seed is not None else summary()["nominal_seed"],
           "T_s": T1, "T_half_s": T2, "J_T": out[T1]["J"], "J_T_half": out[T2]["J"], "rel_change": rel,
           "episode_day_sets_unchanged": same,
           "P1_days_T": out[T1]["P1"], "P1_days_T_half": out[T2]["P1"],
           "P2_days_T": out[T1]["P2"], "P2_days_T_half": out[T2]["P2"],
           "clip_max_T": out[T1]["clip_max"], "clip_max_T_half": out[T2]["clip_max"],
           "rms_speed_change_kmh_by_station": rms, "PASS": bool(rel <= 0.05 and same),
           "differing_days": differ, "margins_report_only": margins}
    if differ:                                                # §A2 T/4 check, numbers only
        res["T_quarter_report_only"] = step_probe_days(differ, (T1, T2, T1 / 4.0), seed)
    (RUNS / f"stephalving_{res['plant_seed']}.json").write_text(json.dumps(res, indent=1))
    return res


def step_probe_days(days_: list, steps, seed) -> dict:
    """Report-only: v_u and v_d - v_u per deciding bin at T, T/2, T/4 for the differing days, with
    r = |x(T/2) - x(T/4)| / |x(T) - x(T/2)|."""
    data = C.load_data()
    days = [str(d) for d in data["days"]]
    net = M.build_network(C.VARIANT)
    cs = part1()["c_s"]
    p = plant_params(seed)
    out = {}
    for day in days_:
        i = days.index(day)
        sl = slice(i, i + 1)
        series = {}
        for T in steps:
            o = simf(net, {k: np.array([v]) for k, v in p.items()},
                           M.Inputs(data["d0"][sl], data["d_o"][sl], data["beta"][sl]), record_cells=False, T_s=T)
            sp, _ = model_speeds(day, o.v_st[0], net, cs)
            series[T] = sp
        rec = {}
        for k, (u, d) in (("B1", I.P1), ("B2", I.P2)):
            xs = [(series[T][u], series[T][d] - series[T][u]) for T in steps]
            with np.errstate(invalid="ignore", divide="ignore"):
                r_u = np.abs(xs[1][0] - xs[2][0]) / np.abs(xs[0][0] - xs[1][0])
                r_d = np.abs(xs[1][1] - xs[2][1]) / np.abs(xs[0][1] - xs[1][1])
            bins = sorted(set(np.flatnonzero(np.nan_to_num((xs[0][0] < 40) & (xs[0][1] >= 20)))) ^
                          set(np.flatnonzero(np.nan_to_num((xs[1][0] < 40) & (xs[1][1] >= 20)))))
            rec[k] = {int(b): {"v_u": [round(float(x[0][b]), 2) for x in xs], "dv": [round(float(x[1][b]), 2) for x in xs],
                               "r_u": _fin(r_u[b]), "r_dv": _fin(r_d[b])} for b in bins}
        out[day] = rec
    return out


def step_probe(day: str, steps=(0.75, 0.375, 0.1875), seed: int | None = None) -> dict:
    """Post-stop diagnostic (report-only): the P_2 decision on one calibration day as T shrinks; the maximum number
    of qualifying bins in a 7-bin window, near-miss bins (v_u < 40 mph, 19 <= v_d - v_u < 20 mph) and the RMS change
    of the Pioneer Tr 5-min speed against the previous step."""
    data = C.load_data()
    days = [str(d) for d in data["days"]]
    i = days.index(day)
    sl = slice(i, i + 1)
    net = M.build_network(C.VARIANT)
    cs = part1()["c_s"]
    p = plant_params(seed)
    u_id, d_id = I.P2
    out, prev = {}, None
    for T in steps:
        o = simf(net, {k: np.array([v]) for k, v in p.items()}, M.Inputs(data["d0"][sl], data["d_o"][sl],
                                                                            data["beta"][sl]), record_cells=False, T_s=T)
        sp, _ = model_speeds(day, o.v_st[0], net, cs)
        u, dv = sp[u_id], sp[d_id] - sp[u_id]
        with np.errstate(invalid="ignore"):
            cond = np.nan_to_num((u < 40) & (dv >= 20)).astype(int)
            near = np.flatnonzero((u < 40) & (dv >= 19) & (dv < 20))
        w = np.convolve(cond, np.ones(7, int), mode="valid")
        r = {"P2_episodes": model_pairs(day, o.v_st[0], net, cs).get(I.P2, []), "max_qualifying_in_7": int(w.max()),
             "near_miss_bins": {int(b): round(float(dv[b]), 2) for b in near}}
        if prev is not None:
            r["rms_change_S1140_mph_vs_previous"] = float(np.sqrt(np.nanmean((u - prev) ** 2)))
            r["max_abs_change_S1140_mph_vs_previous"] = float(np.nanmax(np.abs(u - prev)))
        prev = u
        out[str(T)] = r
    res = {"day": day, "plant_seed": seed if seed is not None else summary()["nominal_seed"], "steps": out,
           "real_P2_episodes": [list(e) for e in I.event_pairs(day).get(I.P2, [])]}
    (RUNS / f"step_probe_{day}.json").write_text(json.dumps(res, indent=1))
    return res


# ---------------------------------------------------------------- profiles (§4.5)
def a3_warm_start(p0: dict, thr: dict) -> dict | None:
    """§A3 (e): None if no A3-feasible completion exists (some v_f below thr x e^(1/a_max)); otherwise p0 with each
    violating a_g raised to its smallest A3-feasible value."""
    p0 = dict(p0)
    a_hi = M.BOUNDS["a"][1]
    vf_of = {0: "vf1", 1: "vf2", 2: "vf3", 3: "vf3"}
    a_of = {0: "a1", 1: "a2", 2: "a3", 3: "a4"}
    for g, t in thr.items():
        vf = p0[vf_of[g]]
        if vf * math.exp(-1.0 / a_hi) < t:
            return None
        if vf * math.exp(-1.0 / p0[a_of[g]]) < t:
            p0[a_of[g]] = 1.0 / math.log(vf / t) * (1 + 1e-9)
    return p0


def profile_job(pi: int, j: int) -> dict:
    """§4.5 with §A3 (e): points with no A3-feasible completion are not run; the warm start raises each violating
    a_g to its smallest A3-feasible value. Seeds 7,191,026 + 9p + j (§A8)."""
    import cma
    data = C.load_data()
    net = M.build_network(C.VARIANT)
    name = PROFILE_PARAMS[pi]
    k = C.NAMES.index(name)
    fixed = j / 8.0                                   # 9 equally spaced points across the bound (normalised)
    seed = 7191026 + 9 * pi + j
    thr = C.a3_thresholds(net)
    p0 = dict(plant_params())
    p0[name] = float(C.to_params(np.where(np.arange(len(C.NAMES)) == k, fixed, C.to_norm(p0))[None, :])[name][0])
    p0 = a3_warm_start(p0, thr)
    if p0 is None:
        res = {"param": name, "point": j, "fixed_norm": fixed, "seed": seed, "status": "infeasible (A3)",
               "best_J": None, "best_x": None}
        (RUNS / f"profile_{name}_{j}.json").write_text(json.dumps(res))
        return res
    x_nom = np.clip(C.to_norm(p0), 0.0, 1.0)
    x_nom[k] = fixed
    free = [i for i in range(len(C.NAMES)) if i != k]
    es = cma.CMAEvolutionStrategy(x_nom[free], 0.1, C.cma_options(seed, len(free)))   # lambda = 4 + floor(3 ln(n-1))
    best, n_inadm, n_a3 = (np.inf, None), 0, 0
    while es.countevals < 600:
        Xf = np.array(es.ask())
        X = np.repeat(x_nom[None, :], len(Xf), axis=0)
        X[:, free] = Xf
        X[:, k] = fixed
        J, parts = C.objective(X, data, net, return_parts=True)
        n_a3 += int(parts["a3_violation"].sum())
        n_inadm += int(((J >= C.J_INADMISSIBLE) & ~parts["a3_violation"]).sum())
        es.tell(list(Xf), list(J))
        i = int(np.argmin(J))
        if J[i] < best[0]:
            best = (float(J[i]), np.clip(X[i], 0, 1).tolist())
    res = {"param": name, "point": j, "fixed_norm": fixed, "seed": seed, "status": "run", "popsize": es.popsize,
           "evals": int(es.countevals), "best_J": best[0], "best_x": best[1], "inadmissible_evals": n_inadm,
           "inadmissible_a3_evals": n_a3}
    (RUNS / f"profile_{name}_{j}.json").write_text(json.dumps(res))
    return res


def all_run(gate_ok: bool) -> dict:
    """§8.6 step 4 after calibration as ONE batch, decisive jobs first: nominal step-halving, the nominal capacity
    grid, the ensemble candidates' step-halving and grids, then the 72 profile jobs filling every free slot. Same jobs,
    seeds and outputs as the separate subcommands; only the scheduling changes."""
    from vsl_lab.ops import ledger
    from vsl_lab.ops.scheduler import Job
    s = summary()
    nom = s["nominal_seed"]
    cands = [r["seed"] for r in s["restarts"] if r["best_J"] <= 1.02 * s["nominal_J"] and r["seed"] != nom]
    mod = "vsl_lab.jobs.metanet_postcal"
    jobs = [Job(jid=f"sh_{nom}", argv=[mod, "stephalving"])]
    jobs += [Job(jid=f"grid_{nom}_{i:02d}", argv=[mod, "grid", "--plant", str(nom), "--c2-index", str(i)])
             for i in range(len(GRID))]
    for c in cands:
        jobs.append(Job(jid=f"sh_{c}", argv=[mod, "stephalving", "--plant", str(c)]))
        jobs += [Job(jid=f"grid_{c}_{i:02d}", argv=[mod, "grid", "--plant", str(c), "--c2-index", str(i)])
                 for i in range(len(GRID))]
    jobs += [Job(jid=f"prof_{q}_{j}", argv=[mod, "profile", "--param", str(q), "--point", str(j)])
             for q in range(len(PROFILE_PARAMS)) for j in range(9)]
    rep = _batch(jobs, "all", gate_ok)
    out = {"jobs": rep.n_jobs, "failed": rep.n_failed_proc, "wall_s": rep.wall_s, "candidates": cands}
    for name, seeds in (("metanet_v4_capacity_grid", [nom] + cands), ("metanet_v4_profiles", None)):
        ledger.append("DP", "metanet-v4-calib", "S", name, {"plants": seeds, "T_s": C.T_RUN, "batch": "all-run"},
                      "7191026-7191097 (profiles); grids deterministic", rep.n_jobs,
                      {"proc_failed": rep.n_failed_proc}, {"wall_s": round(rep.wall_s, 1)}, notes=str(RUNS))
    return out


def _batch(jobs, tag, gate_ok):
    from vsl_lab.ops.scheduler import run_batch
    try:
        return run_batch(jobs, RUNS / f"batch_{tag}_{int(time.time())}", max_workers=32, gate_ok=gate_ok)
    finally:
        C.verify_v3()                                          # §A9: after every v4 batch


def main(argv=None) -> int:
    from vsl_lab.ops import ledger
    from vsl_lab.ops.scheduler import Job
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["stephalving", "grid", "grid-run", "profile", "profile-run", "probe", "all-run"])
    ap.add_argument("--day", default="20230517")
    ap.add_argument("--plant", type=int, default=None)
    ap.add_argument("--c2-index", type=int, default=0)
    ap.add_argument("--param", type=int, default=0)
    ap.add_argument("--point", type=int, default=0)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "stephalving":
        r = stephalving(a.plant)
        print(json.dumps({k: r[k] for k in ("plant_seed", "T_s", "J_T", "J_T_half", "rel_change", "episode_day_sets_unchanged",
                                            "PASS")}))
        ledger.append("DP", "metanet-v4-calib", "S", "metanet_v4_stephalving", {"T_s": [r["T_s"], r["T_half_s"]], "plant": r["plant_seed"]},
                      "none (deterministic); calibration days", 1, {},
                      {"rel_change": round(r["rel_change"], 4), "same_episode_days": r["episode_day_sets_unchanged"],
                       "PASS": r["PASS"]}, notes=str(RUNS / f"stephalving_{r['plant_seed']}.json"))
        C.verify_v3()
    elif a.what == "grid":
        seed = a.plant if a.plant is not None else summary()["nominal_seed"]
        print(json.dumps({"grid_file": str(grid_job(seed, a.c2_index))}))   # a JSON line: the scheduler counts it ok
    elif a.what == "grid-run":
        seed = a.plant if a.plant is not None else summary()["nominal_seed"]
        jobs = [Job(jid=f"grid_{seed}_{i:02d}", argv=["vsl_lab.jobs.metanet_postcal", "grid", "--plant", str(seed),
                                                      "--c2-index", str(i)]) for i in range(len(GRID))]
        rep = _batch(jobs, f"grid_{seed}", a.gate_ok)
        print(json.dumps({"jobs": rep.n_jobs, "failed": rep.n_failed_proc, "wall_s": rep.wall_s}))
        ledger.append("DP", "metanet-v4-calib", "S", "metanet_v4_capacity_grid", {"plant": seed, "grid": "0.80:0.01:1.20 x2", "T_s": C.T_RUN},
                      "none (deterministic); calibration days", rep.n_jobs, {"proc_failed": rep.n_failed_proc},
                      {"wall_s": round(rep.wall_s, 1)}, notes=str(RUNS / f"grid_{seed}_c2_*.json"))
    elif a.what == "all-run":
        r = all_run(a.gate_ok)
        print(json.dumps(r))
    elif a.what == "profile":
        print(json.dumps(profile_job(a.param, a.point)))
    elif a.what == "probe":
        r = step_probe(a.day, seed=a.plant)
        print(json.dumps({T: {k: v[k] for k in ("P2_episodes", "max_qualifying_in_7")} for T, v in r["steps"].items()}))
    else:
        jobs = [Job(jid=f"prof_{p}_{j}", argv=["vsl_lab.jobs.metanet_postcal", "profile", "--param", str(p),
                                               "--point", str(j)]) for p in range(len(PROFILE_PARAMS)) for j in range(9)]
        rep = _batch(jobs, "profiles", a.gate_ok)
        print(json.dumps({"jobs": rep.n_jobs, "failed": rep.n_failed_proc, "wall_s": rep.wall_s}))
        ledger.append("DP", "metanet-v4-calib", "S", "metanet_v4_profiles", {"params": PROFILE_PARAMS, "points": 9, "evals": 600, "T_s": C.T_RUN},
                      "7191026-7191097 (optimizer); T = 0.75 s", rep.n_jobs, {"proc_failed": rep.n_failed_proc},
                      {"wall_s": round(rep.wall_s, 1)}, notes=str(RUNS / "profile_*.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
