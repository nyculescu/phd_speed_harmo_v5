"""E1 stage-0 rules on numbers (V213 §9.3-9.4, §10.3): power rule, noise floors, drop onset, ô_cr, lead-time tests.

Pure functions; no SUMO. Units: paired-difference SDs are relative to median(D_NC) (s = SD(d0) / median(D_NC)).
"""
from __future__ import annotations

import math

import numpy as np
from scipy.stats import chi2

from v5b.fleet.day import breakdowns
from v5b.p1.stats import REL_MIN, boot_idx

MDE, POWER = 0.15, 0.80
N_STEPS = (10, 15, 20)
MC_R, MC_B, MC_SEED = 2000, 2000, 20261031
NOISE_RULE = 0.05
NOON = 12 * 3600.0
FRESH_MIN = 0.05
MERGE_GAP = 600.0                          # V215 A3: episodes closer than 10 min are one breakdown


def s_upper(s: float, n_pairs: int = 10, level: float = 0.80) -> float:
    """Upper confidence bound of an SD estimated from n_pairs values (chi-square, n_pairs - 1 df)."""
    df = n_pairs - 1
    return s * math.sqrt(df / chi2.ppf(1.0 - level, df))


def p_pass(n: int, gain: float, s: float, r: int = MC_R, b: int = MC_B, seed: int = MC_SEED) -> float:
    """P(rel >= 0.10 and percentile lower bound of median d > 0) for d ~ N(gain, s^2), median(D_NC) = 1."""
    rng = np.random.default_rng(seed)
    d = gain + s * rng.standard_normal((r, n))
    idx = boot_idx(n, b)
    lo = np.percentile(np.median(d[:, idx], axis=2), 2.5, axis=1)
    return float(np.mean((np.median(d, axis=1) >= REL_MIN) & (lo > 0)))


def choose_n(s: float, n_pairs: int = 10) -> dict:
    """§9.3: the smallest n with P(pass | true 15 %) >= 0.80 at the upper 80 % bound of s; None if none up to 20."""
    su = s_upper(s, n_pairs)
    pw = {n: p_pass(n, MDE, su) for n in N_STEPS}
    ok = [n for n in N_STEPS if pw[n] >= POWER]
    return {"s": s, "s_upper": su, "power_at_mde": pw, "n": ok[0] if ok else None,
            "power_10_15_20_at_n": ({g: p_pass(ok[0], g, su) for g in (0.10, 0.15, 0.20)} if ok else None)}


def noise_floors(s: float, n: int, points: int = 12, family: int = 6, r: int = MC_R, seed: int = MC_SEED) -> dict:
    """§9.4 under the global null, per-run noise s / sqrt 2: phi_O = E[rel of O_off] (points + NC), phi_T = E[rel of
    the best of one family], and how often each reaches 0.10."""
    rng = np.random.default_rng(seed)
    e = s / math.sqrt(2.0) * rng.standard_normal((r, points + 1, n))   # row 0 = NC
    o = np.median(e[:, 0] - e.min(axis=1), axis=1)
    t = np.median(e[:, :1] - e[:, 1:1 + family], axis=2).max(axis=1)
    return {"phi_O": float(o.mean()), "p_O": float((o >= REL_MIN).mean()), "phi_T": float(t.mean()),
            "p_T": float((t >= REL_MIN).mean()), "rule1_c2_budgeted": bool(o.mean() >= NOISE_RULE),
            "rule2_tuned_replicate": bool(t.mean() >= NOISE_RULE)}


def _passes(d: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """§9.2 (1)-(2) per row of paired differences d (relative to median D_NC = 1)."""
    lo = np.percentile(np.median(d[:, idx], axis=2), 2.5, axis=1)
    return (np.median(d, axis=1) >= REL_MIN) & (lo > 0)


def global_null(s: float, n: int, rule2: bool, r: int = 500, b: int = 1000, seed: int = MC_SEED) -> dict:
    """§9.4 report-only: P(a continue in one cell) under the global null for the whole procedure: M* and C* (best of
    6), MC* as a 7th point, C1 on 10 fresh seeds for a borderline best, Rule 2 twins if rule2, O_off over NC + 13
    points with its C2 twins. The B1 extension (one more point) is left out. Per-run noise SD s / sqrt 2."""
    rng = np.random.default_rng(seed)
    sd = s / math.sqrt(2.0)
    e = sd * rng.standard_normal((r, 14, n))                 # row 0 NC, 1-6 meter, 7-12 CAV, 13 MC*
    tw = sd * rng.standard_normal((r, 14, n))                # twin SUMO seeds
    fr = sd * rng.standard_normal((r, 2, 10))                # C1 fresh seeds: NC and the arm
    idx, idx2 = boot_idx(n, b), boot_idx(n + 10, b)
    d = e[:, :1] - e[:, 1:]                                  # (r, 13, n)
    med = np.median(d, axis=2)
    m_i, c_i = med[:, :6].argmax(axis=1), 6 + med[:, 6:12].argmax(axis=1)
    rows = np.arange(r)
    tuned = {"M*": m_i, "C*": c_i, "MC*": np.full(r, 12)}
    tp = np.zeros(r, bool)
    best_rel, best_k = np.full(r, -np.inf), np.zeros(r, int)
    for k in tuned.values():
        dk = d[rows, k]
        ok = _passes(dk, idx)
        if rule2:
            ok &= _passes(tw[:, 0] - tw[rows, k + 1], idx)
        tp |= ok
        rel = np.median(dk, axis=1)
        better = rel > best_rel
        best_rel, best_k = np.where(better, rel, best_rel), np.where(better, k, best_k)
    db = d[rows, best_k]
    lo = np.percentile(np.median(db[:, idx], axis=2), 2.5, axis=1)
    c1 = (best_rel >= REL_MIN) & (lo <= 0)
    dall = np.concatenate([db, fr[:, 0] - fr[:, 1]], axis=1)
    c1_ok = c1 & _passes(dall, idx2) & (np.median(fr[:, 0] - fr[:, 1], axis=1) >= FRESH_MIN)
    if rule2:
        c1_ok &= _passes(tw[:, 0] - tw[rows, best_k + 1], idx)
    tp |= c1_ok
    j = e.argmin(axis=1)                                     # O_off picks per seed (0 = NC)
    o_in = _passes(e[:, 0] - e.min(axis=1), idx)
    twin_pick = np.take_along_axis(tw, j[:, None, :], axis=1)[:, 0]
    po = o_in & ~tp & _passes(tw[:, 0] - twin_pick, idx)
    cont = tp | po
    return {"s": s, "n": n, "rule2": rule2, "r": r, "p_continue_cell": float(cont.mean()),
            "p_tuned": float(tp.mean()), "p_c1": float(c1_ok.mean()), "p_oracle": float(po.mean()),
            "p_continue_either_cell": float(1.0 - (1.0 - cont.mean()) ** 2), "b1_left_out": True}


def main_pm(ser: list, field: int = 7, start: float = NOON) -> dict | None:
    """V215 A3: the main PM breakdown at the drop loop. Episodes of the breakdowns() speed rule starting after
    `start` are merged when the gap is below 10 min; the longest merged episode, with its pre-queue flow (highest
    5-min exit flow in the hour before), QDF (mean exit flow from 5 min after the onset to the recovery) and drop."""
    ep = [(e["t_break"], e["t_recover"]) for e in breakdowns(ser, field) if e["t_break"] >= start]
    if not ep:
        return None
    merged = [list(ep[0])]
    for a, b in ep[1:]:
        if a - merged[-1][1] < MERGE_GAP:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    tb, tr = max(merged, key=lambda e: e[1] - e[0])
    t = np.array([x[0] for x in ser], dtype=float)
    q = np.array([x[1] for x in ser], dtype=float) * 120.0
    roll = np.convolve(q, np.ones(10) / 10, mode="valid")
    cand = roll[(t[9:] > tb - 3600.0) & (t[9:] < tb)]
    m = (t >= tb + 300.0) & (t <= tr)
    pre = float(cand.max()) if cand.size else None
    qdf = float(q[m].mean()) if m.any() else None
    return {"t_break": tb, "t_recover": tr, "min": round((tr - tb) / 60.0, 1), "pre": pre, "qdf": qdf,
            "drop": (1.0 - qdf / pre) if pre and qdf else None, "n_merged": sum(1 for a, _ in ep if tb <= a <= tr)}


def drop_onset(ser: list, field: int = 7) -> float | None:
    """§10.3 with V215 A3: start of the main PM breakdown at the drop loop."""
    e = main_pm(ser, field)
    return e["t_break"] if e else None


def _episodes(ser: list, field: int) -> list:
    return [(e["t_break"], e["t_recover"]) for e in breakdowns(ser, field)]


def ocr_day(t: np.ndarray, q: np.ndarray, occ: np.ndarray, t_b: float, earlier: list) -> float | None:
    """ô_cr for one day and loop group: in the hour before t_b, excluding 10 min after any earlier breakdown, the 5-min
    window (10 consecutive 30-s intervals) with the highest mean flow; its mean occupancy."""
    best, val = -1.0, None
    for i in range(9, len(t)):
        a, z = t[i - 9] - 30.0, t[i]          # the window covers (a, z]
        if a < t_b - 3600.0 or z >= t_b:     # the interval stamped t_b is the first slow one
            continue
        if any(r0 < z and a < r1 + 600.0 for r0, r1 in earlier if r0 < t_b):
            continue
        f = float(q[i - 9:i + 1].mean())
        if f > best:
            best, val = f, float(occ[i - 9:i + 1].mean())
    return val


def occ60(t: np.ndarray, occ: np.ndarray) -> tuple:
    """60-s occupancy at each 60-s mark: the mean of the two 30-s intervals ending there."""
    k = np.where(np.isclose(t % 60.0, 0.0))[0]
    k = k[k >= 1]
    return t[k], (occ[k] + occ[k - 1]) / 2.0


def lead_ok(t: np.ndarray, occ: np.ndarray, o_cr: float, t_b: float) -> bool:
    """Drop-loop choice (§10.3): the 60-s occupancy crosses ô_cr upward within [t_b - 5 min, t_b + 2 min] (below at
    the previous mark, at or above at this one) and stays below it for >= 80 % of the hour before t_b - 5 min."""
    tm, o = occ60(t, occ)
    up = np.r_[False, (o[1:] >= o_cr) & (o[:-1] < o_cr)]
    near = (tm >= t_b - 300.0) & (tm <= t_b + 120.0)
    pre = (tm > t_b - 3900.0) & (tm <= t_b - 300.0)
    if not (up & near).any() or not pre.any():
        return False
    above_at_window = o[np.where(tm < t_b - 300.0)[0][-1]] >= o_cr if (tm < t_b - 300.0).any() else False
    return bool(not above_at_window and (o[pre] < o_cr).mean() >= 0.80)


def spill_ok(t: np.ndarray, occ: np.ndarray, o_cr: float, t_b: float) -> bool:
    """'alinea_3' sees the spillback (§10.3): above ô_cr within 60 min after t_b, below it >= 80 % of the hour before
    t_b - 5 min."""
    tm, o = occ60(t, occ)
    post = (tm >= t_b) & (tm <= t_b + 3600.0)
    pre = (tm > t_b - 3900.0) & (tm <= t_b - 300.0)
    return bool((o[post] > o_cr).any() and pre.any() and (o[pre] < o_cr).mean() >= 0.80)


def loop_arrays(day: dict, group: str) -> tuple:
    """(t, flow veh/h, occupancy %) of one loop group from a day's 'loops30'."""
    g, rows = day["loops30"]["groups"], day["loops30"]["rows"]
    j = 1 + 3 * g.index(group)
    a = np.array([[r[0], r[j], r[j + 1]] for r in rows], dtype=float)
    return a[:, 0], a[:, 1], a[:, 2]


def calibrate(days: list, groups: tuple = ("drop", "dropend", "alinea")) -> dict:
    """§10.3 on the NC R days: t_b per day, ô_cr per loop group (median over days), the drop-loop choice and the
    'alinea_3' spillback test."""
    per = []
    for d in days:
        t_b = drop_onset(d["series"])
        row = {"seed": d["seed"], "t_b": t_b}
        if t_b is not None:
            earlier = _episodes(d["series"], 7)
            for g in groups:
                t, q, o = loop_arrays(d, g)
                row[g] = ocr_day(t, q, o, t_b, earlier)
        per.append(row)
    have = [r for r in per if r["t_b"] is not None]
    out = {"days": per, "n_onset": len(have), "stop": len(have) < 8}
    if out["stop"]:
        return out
    ocr = {g: float(np.median([r[g] for r in have if r[g] is not None])) for g in groups}
    out["o_cr"] = ocr
    tests = {}
    for g in groups:
        f = spill_ok if g == "alinea" else lead_ok
        ok = []
        for d, r in zip(days, per):
            if r["t_b"] is None:
                continue
            t, _, o = loop_arrays(d, g)
            ok.append(f(t, o, ocr[g], r["t_b"]))
        tests[g] = {"n_ok": int(sum(ok)), "n": len(ok), "pass": sum(ok) >= 8}
    out["tests"] = tests
    out["drop_loop"] = "drop" if tests["drop"]["pass"] else "dropend" if tests["dropend"]["pass"] else None
    out["stop"] = out["drop_loop"] is None or not tests["alinea"]["pass"]
    return out


# Stages A-C (V213 §8-9): D arrays per point are aligned by seed; NC is the reference.
TIE = 0.1                                  # s/veh: ties go to the middle setpoint, then the short zone, then ALINEA
SETPOINTS = (0.85, 0.95, 1.05)
EDGE_STEP = 0.10
HARM = -0.05


def effect(d_nc, d_x) -> dict:
    from v5b.p1.stats import paired, rule_cell
    st = paired(d_nc, d_x)
    return {**st, "pass": rule_cell(st)["a"], "sign": int(np.sum(np.asarray(d_x) < np.asarray(d_nc))),
            "mean": paired(d_nc, d_x, mean=True)}


def _tie_key(point: str) -> tuple:
    """Lower is preferred: distance of the setpoint from 0.95, then short zone, then ALINEA (point 'ma/p0.95')."""
    fam, p = point.split("/", 1)
    sp = float(p.split("_")[0][1:])
    return round(abs(sp - 0.95), 6), 0 if "short" in p or "_" not in p else 1, 0 if fam == "ma" else 1


def tuned(d_nc, points: dict, family: tuple) -> str:
    """M* or C*: the point of the family with the largest median paired difference (ties within TIE s/veh)."""
    cand = {k: float(np.median(np.asarray(d_nc) - np.asarray(v))) for k, v in points.items() if k.split("/")[0] in family}
    best = max(cand.values())
    return min((k for k, v in cand.items() if v >= best - TIE), key=_tie_key)


def o_off(d_nc, points: dict) -> tuple:
    """Per-day oracle that may choose no control: (D per seed, pick per seed; 'nc' when no point beats NC)."""
    keys = list(points)
    m = np.vstack([np.asarray(d_nc)] + [np.asarray(points[k]) for k in keys])
    j = m.argmin(axis=0)
    return m.min(axis=0), ["nc" if i == 0 else keys[i - 1] for i in j]


def edge_fires(d_nc, points: dict, best: str, any_tuned_pass: bool) -> float | None:
    """§8 edge rule: the next setpoint beyond the grid edge, or None. 'best' is a family's tuned point."""
    if any_tuned_pass:
        return None
    fam, p = best.split("/", 1)
    sp = float(p.split("_")[0][1:])
    rest = "_".join(p.split("_")[1:])
    sps = sorted({float(k.split("/", 1)[1].split("_")[0][1:]) for k in points if k.startswith(fam + "/")
                  and "_".join(k.split("/", 1)[1].split("_")[1:]) == rest})
    if sp not in (sps[0], sps[-1]) or len(sps) < 3:
        return None
    mid = f"{fam}/p0.95" + (f"_{rest}" if rest else "")
    if mid not in points or np.median(np.asarray(d_nc) - np.asarray(points[best])) <= \
            np.median(np.asarray(d_nc) - np.asarray(points[mid])):
        return None
    return round(sp - EDGE_STEP, 2) if sp == sps[0] else round(sp + EDGE_STEP, 2)


def c1_needed(eff: dict) -> bool:
    return eff["rel"] >= 0.10 and eff["diff_ci"][0] <= 0.0


def c1_pass(d_nc_all, d_x_all, n_first: int) -> dict:
    """§9.6: §9.2 on all seeds, and the fresh seeds alone give rel >= 0.05."""
    a = effect(d_nc_all, d_x_all)
    f = effect(d_nc_all[n_first:], d_x_all[n_first:])
    return {"all": a, "fresh": f, "pass": bool(a["pass"] and f["rel"] >= FRESH_MIN)}


def harm_label(eff: dict) -> str:
    lo, hi = eff["rel_ci"]
    return "clearly worse" if hi < HARM else "harm not excluded" if lo < HARM else "no harm"


def intrusion_flag(x_arm: int, x_nc: int, alpha: float = 0.05) -> dict:
    """§7.5 (Q8): exact one-sided conditional binomial test, equal exposure."""
    from scipy.stats import binomtest
    n = x_arm + x_nc
    p = binomtest(x_arm, n, 0.5, alternative="greater").pvalue if n else 1.0
    return {"x_arm": x_arm, "x_nc": x_nc, "p": float(p), "flag": bool(p < alpha)}


def throughput_loss(served_nc, served_x) -> bool:
    """§7.2: the whole CI of the PM served difference lies below -1 % of NC's PM throughput."""
    from v5b.p1.stats import paired
    st = paired(np.asarray(served_x, float), np.asarray(served_nc, float))   # d = x - nc
    return bool(st["diff_ci"][1] < -0.01 * float(np.median(served_nc)))


def ttt_conflict(ttt_nc, ttt_x) -> bool:
    """§7.3: the whole CI of the relative TTT_w difference lies below -5 %."""
    return harm_label(effect(ttt_nc, ttt_x)) == "clearly worse"


def verdict(cells: dict) -> dict:
    """§9.7 decision tree. cells[τ] = {"P_T": bool, "P_O": bool, "F": list of flagged passes, "powered": bool}."""
    r, i = cells["R"], cells["I"]
    if r["P_T"]:
        v = "CONTINUE-T"
    elif r["P_O"]:
        v = "CONTINUE-O"
    elif i["P_T"] or i["P_O"]:
        v = "I-ONLY"
    elif r["F"] or i["F"]:
        v = "FLAGGED-ONLY"
    else:
        v = "KILL"
    default = {"I-ONLY": "KILL of the recurrent line; E2 does not start; an incident study needs its own protocol",
               "FLAGGED-ONLY": "treated as no pass: KILL, flags reported"}.get(v)
    powered = [c for c in ("R", "I") if not cells[c]["powered"]]
    return {"verdict": v, "default_next": default,
            "kill_label": None if v not in ("KILL", "FLAGGED-ONLY") else
            "powered" if not powered else "underpowered: " + ", ".join(powered)}
