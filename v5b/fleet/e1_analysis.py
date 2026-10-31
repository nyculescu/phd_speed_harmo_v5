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


def drop_onset(ser: list, field: int = 7) -> float | None:
    """§10.3: start of the first breakdown after 12:00 at the drop loop (the breakdowns() speed rule), any length."""
    ep = [e["t_break"] for e in breakdowns(ser, field) if e["t_break"] >= NOON]
    return min(ep) if ep else None


def _episodes(ser: list, field: int) -> list:
    return [(e["t_break"], e["t_recover"]) for e in breakdowns(ser, field)]


def ocr_day(t: np.ndarray, q: np.ndarray, occ: np.ndarray, t_b: float, earlier: list) -> float | None:
    """ô_cr for one day and loop group: in the hour before t_b, excluding 10 min after any earlier breakdown, the 5-min
    window (10 consecutive 30-s intervals) with the highest mean flow; its mean occupancy."""
    best, val = -1.0, None
    for i in range(9, len(t)):
        a, z = t[i - 9] - 30.0, t[i]          # the window covers (a, z]
        if a < t_b - 3600.0 or z > t_b:
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
    """Drop-loop choice (§10.3): the 60-s occupancy reaches ô_cr within [t_b - 5 min, t_b + 2 min] and stays below it
    for >= 80 % of the hour before t_b - 5 min."""
    tm, o = occ60(t, occ)
    near = (tm >= t_b - 300.0) & (tm <= t_b + 120.0)
    pre = (tm > t_b - 3900.0) & (tm <= t_b - 300.0)
    return bool((o[near] >= o_cr).any() and pre.any() and (o[pre] < o_cr).mean() >= 0.80)


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
