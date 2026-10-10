"""METANET v5 objective J5: pure item functions (protocol v5 §B1; docs/plans/day_pattern_metanet_protocol_v5.md).
Slice A of the implementation: no simulation, no real day, no file of a validation day. Episodes are inclusive bin
intervals (s, e) on the 5-min event grid; cells are 1-based as in the protocol (cell 26 = index 25).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from vsl_lab.data import metanet_events as E

EPS = 0.5                       # §B1.4 shaping weight
G_MPH = 40.0                    # §B1.4 speed-margin scale
BIN = E.BIN_MIN                 # 5 min
OVL = 12                        # ±60 min overlap tolerance (metanet_postcal.OVERLAP_BINS)
MATCH = 18                      # ±90 min match tolerance
CAP_ONSET, CAP_DUR, CAP_QDIS, CAP_RATIO, CAP_EXT = 90.0, 90.0, 0.15, 0.15, 3.0
TAPER_A, TAPER_B = 45.0, 90.0   # minutes
HINGE = {"P1a": (0.10, 0.20), "P1b": (0.20, 0.40)}            # (threshold, ramp width = 2 × threshold)
REALISM_CAP = {"P1a_ff": 0.30, "P1b_ff": 0.60}
BACK_CELLS = {"B1": (26, 27, 28), "B2": (33,)}                 # §B1.2 J5-backed bin (1-based cells)


# ---------- basic shapes ----------
def taper_t(donset_min: float) -> float:
    """§B1.3 taper weight t = clip((|Δonset| − 45)/45, 0, 1)."""
    return float(np.clip((abs(donset_min) - TAPER_A) / (TAPER_B - TAPER_A), 0.0, 1.0))


def taper(item: float, donset_min: float) -> float:
    t = taper_t(donset_min)
    return t + (1.0 - t) * item


def capped(x: float, cap: float) -> float:
    return min(abs(x), cap) / cap


def overlaps(a: tuple, b: tuple, tol: int = OVL) -> bool:
    return a[0] <= b[1] + tol and b[0] <= a[1] + tol


# ---------- creditability (§B1.2) ----------
def qualifying(cond: np.ndarray, ep: tuple) -> list:
    """Qualifying bins of an episode: bins where the pair condition holds (v4 §A12)."""
    return [b for b in range(ep[0], ep[1] + 1) if cond[b]]


def j5_backed(cong: np.ndarray, b: int, k: str) -> bool:
    """cong: (n_cells, n_bins) bool congested-cell matrix (0-based rows). P_1: cells 26, 27, 28 all congested;
    P_2: cell 33 congested."""
    return bool(all(cong[c - 1, b] for c in BACK_CELLS[k]))


def creditable(ep: tuple, cond: np.ndarray, cong: np.ndarray, k: str) -> bool:
    """An episode's own qualifying bins ≥ 50 % J5-backed; no qualifying bin -> not creditable."""
    q = qualifying(cond, ep)
    return bool(q) and sum(j5_backed(cong, b, k) for b in q) / len(q) >= 0.5


# ---------- per-bottleneck target items (§B1.3) ----------
def p3_item(real: list, model: list, credit: list, s: float, eps: float = EPS) -> float:
    """Real-active day: 0 if a creditable model episode overlaps a real one, else 1 + ε·s.
    Real-inactive day (real == []): 1 if any model episode."""
    if not real:
        return float(bool(model))
    hit = any(c and overlaps(m, r) for m, c in zip(model, credit) for r in real)
    return 0.0 if hit else 1.0 + eps * s


def x_item(real: list, model: list) -> float | None:
    """X-k on a real-inactive day; None (not in the qualifying set) on a real-active day."""
    return None if real else float(bool(model))


def p4_items(real: list, model: list, credit: list) -> list:
    """One item per real episode: gate matching over all model episodes; a match to a non-creditable episode -> 1."""
    from vsl_lab.jobs import metanet_items as IT
    return [capped(dt, CAP_ONSET) if j is not None and credit[j] else 1.0 for dt, j in IT.p4_day(real, model)]


def longest(eps: list) -> int | None:
    return max(range(len(eps)), key=lambda i: (eps[i][1] - eps[i][0], -eps[i][0])) if eps else None


def matched_longest(real: list, model: list, credit: list):
    """(index of the real longest episode, matched model index or None, creditable?)"""
    i = longest(real)
    if i is None:
        return None, None, False
    j = E.match_episodes(real, model, MATCH).get(i)
    return i, j, (j is not None and bool(credit[j]))


def p5a_item(real: list, model: list, credit: list, qdis_real: float, qdis_model: list) -> float:
    """Heavy day: min(|Q̂/Q − 1|, 0.15)/0.15 on the matched longest episode if creditable and C4-usable, tapered;
    else 1. qdis_model[j] is the model C4 discharge of model episode j (None if unusable)."""
    i, j, ok = matched_longest(real, model, credit)
    if not ok or qdis_model[j] is None or not qdis_real:
        return 1.0
    return taper(capped(qdis_model[j] / qdis_real - 1.0, CAP_QDIS), (model[j][0] - real[i][0]) * BIN)


def p7a_item(real: list, model: list, credit: list, t_c: int | None = None) -> float:
    """Heavy day: min(|dur_m − dur_r|, 90)/90 on the matched longest episode if creditable (B1: both censored at the
    real t_c), tapered; else 1."""
    i, j, ok = matched_longest(real, model, credit)
    if not ok:
        return 1.0
    dr = E.censored_duration(tuple(real[i]), t_c)
    dm = E.censored_duration(tuple(model[j]), t_c)
    return taper(capped(dm - dr, CAP_DUR), (model[j][0] - real[i][0]) * BIN)


# ---------- system items (all model episodes, as the gate) ----------
def p5c_item(ratio_real: float, ratio_model: float | None, donset_max_min: float) -> float:
    if ratio_model is None or not ratio_real:
        return 1.0
    return taper(capped(ratio_model / ratio_real - 1.0, CAP_RATIO), donset_max_min)


def p7b_item(index_error: int | None, donset_max_min: float) -> float:
    if index_error is None:
        return 1.0
    return taper(capped(index_error, CAP_EXT), donset_max_min)


def p7c_item(real1: list, real2: list, mod1: list, mod2: list) -> float:
    """Gate's p7c_pair on all model episodes; 1 if no model union interval overlaps the real longest one; taper on
    the difference of the union start times."""
    dr, dm = E.p7c_pair(real1, real2, mod1, mod2)
    if dr == 0:
        return None
    if dm == 0:
        return 1.0
    ri = E.union_intervals(real1, real2)
    rs, re_ = max(ri, key=lambda x: (x[1] - x[0], -x[0]))
    mi = [x for x in E.union_intervals(mod1, mod2) if x[0] <= re_ + OVL and rs <= x[1] + OVL]
    ms = max(mi, key=lambda x: (x[1] - x[0], -x[0]))[0]
    return taper(capped(dm - dr, CAP_DUR), (ms - rs) * BIN)


# ---------- shaping (§B1.4) ----------
def margins(v_u: np.ndarray, v_d: np.ndarray) -> np.ndarray:
    """m(b) = min(40 − v_u, (v_d − v_u) − 20) in mph; −inf where either speed is NaN."""
    with np.errstate(invalid="ignore"):
        m = np.minimum(40.0 - v_u, (v_d - v_u) - 20.0)
    return np.where(np.isfinite(m), m, -np.inf)


def windows(real: list, censor: dict | None, n_bins: int) -> list:
    """Per real episode j: I_j = [onset − 60 min, end + 60 min]; a censored B1 episode (censor[j] = t_c):
    [onset − 60 min, t_c]. Returns the 7-bin window starts overlapping each I_j (clipped to the series)."""
    out = []
    for j, (s, e) in enumerate(real):
        t_c = (censor or {}).get(j)
        a, b = s - 12, (t_c if t_c is not None else e + 12)
        out.append([w for w in range(max(0, a - 6), min(b, n_bins - 7) + 1)])
    return out


def g_value(m: np.ndarray, wins: list) -> float:
    best = -np.inf
    for ws in wins:
        for w in ws:
            best = max(best, float(np.sort(m[w:w + 7])[::-1][4]))
    return best


def h_value(beta: np.ndarray, wins: list) -> float:
    """beta(b) = min over §B1.2's cells of ρ_i/ρ̄_cr,i (bin means)."""
    bins = sorted({b for ws in wins for w in ws for b in range(w, w + 7)})
    return float(np.max(beta[bins])) if bins else 0.0


def s_override(real: list, model: list, credit: list, wins: list) -> bool:
    """s = 1 if a model episode overlaps a real one, or a non-creditable one has a bin in a window used for g."""
    if any(overlaps(m, r) for m in model for r in real):
        return True
    span = {b for ws in wins for w in ws for b in range(w, w + 7)}
    return any(not c and span & set(range(m[0], m[1] + 1)) for m, c in zip(model, credit))


def shaping(g: float, h: float, override: bool) -> float:
    if override:
        return 1.0
    return 0.5 * float(np.clip(-g / G_MPH, 0.0, 1.0)) + 0.5 * float(np.clip(1.0 - h, 0.0, 1.0))


# ---------- guard and realism rows ----------
def hinge(name: str, x: float | None) -> float | None:
    if x is None or not np.isfinite(x):
        return None
    thr, width = HINGE[name]
    return float(np.clip((x - thr) / width, 0.0, 1.0))


def p1c_hinge(model: float, n1: float, n2: float) -> float | None:
    if any(v is None or not np.isfinite(v) for v in (model, n1, n2)):
        return None
    return float(np.clip((model - n2) / max(0.02, n1 - n2), 0.0, 1.0))


def realism(name: str, x: float | None) -> float | None:
    if x is None or not np.isfinite(x):
        return None
    return min(1.0, x / REALISM_CAP[name])


# ---------- aggregation ----------
def j5(rows: dict, weights: dict) -> float:
    """rows: name -> list of items (None = unscored, left out); weights: name -> w_r. Rows with no scored item are
    dropped from both sums. J5 = Σ w_r·A_r / Σ w_r."""
    num = den = 0.0
    for r, items in rows.items():
        x = [v for v in items if v is not None]
        if x:
            num += weights[r] * float(np.mean(x))
            den += weights[r]
    return num / den if den else float("nan")


def j_day(day_rows: dict, weights: dict) -> float:
    """§B1.6 per-day form: day_rows: name -> list of that day's items."""
    return j5(day_rows, weights)


def parity_omega(active: list, n: dict, keep_p5c: bool = True) -> tuple:
    """§B1.5. active: per real-active B_k day, dict(e=#real episodes, heavy=bool, both=bool in P5c's set);
    n: qualifying-set sizes {P3, P4, P5a, P7a, P5c, X}. Returns (U_k, ω_k)."""
    u = [1 / n["P3"] + d["e"] / n["P4"] + (1 / n["P5a"] + 1 / n["P7a"]) * bool(d["heavy"])
         + (bool(d["both"]) and keep_p5c) / n["P5c"] for d in active]
    U = float(np.mean(u))
    return U, n["X"] * (U - 1 / n["P3"])


# ---------- facts guard (test 35) ----------
def load_facts(path: str | Path, sha256: str) -> dict:
    raw = Path(path).read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != sha256:
        raise RuntimeError(f"J5 refuses to run: facts hash {got[:12]} != committed {sha256[:12]}")
    return json.loads(raw)


# ---------- §B5 head-cell report (report-only)
HEAD_ANCHOR = {"B1": 26, "B2": 33}
FIRST_CELL = {"B1": 28, "B2": 33}


def head_cell(ep: tuple, cond: np.ndarray, cong: np.ndarray, k: str) -> int | None:
    """Most downstream cell (1-based) of the contiguous congested run that contains the anchor cell (26 for P_1,
    33 for P_2), modal over the episode's qualifying bins (ties: the lower cell); None if no run."""
    a = HEAD_ANCHOR[k] - 1
    heads = []
    for b in qualifying(cond, ep):
        if not cong[a, b]:
            continue
        c = a
        while c + 1 < cong.shape[0] and cong[c + 1, b]:
            c += 1
        heads.append(c + 1)
    if not heads:
        return None
    vals, cnt = np.unique(heads, return_counts=True)
    return int(vals[np.flatnonzero(cnt == cnt.max())[0]])
