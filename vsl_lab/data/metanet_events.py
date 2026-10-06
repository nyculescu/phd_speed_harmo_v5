"""Model/real event comparison for the U.S.169 SB METANET plant (protocol v3 §4.2, §5.1; binding).

Pure functions on 5-min series so that they are unit-testable on toy data:
- nrmse                       §4.2
- scale_table                 §3.2.4 group references m_G and c_s
- observe                     §5.1 observation operator (model km/h -> detector-scale mph) + per-bin real mask
- pair_episodes               §3.2.1 corridor rule with EA-2 (named pair allowed beyond 3 km)
- censor_b1                   §5.1 B1 right-censored by B2
- match_episodes              §5.1 one-to-one nearest onset within +-90 min
- p7c                         §5.4 system duration = longest union interval of P_1 and P_2 episodes
- c4                          C4 block (Q_dis, r) with an optional window end
Bins are 5-min; event-layer series start at 05:00 (216 bins), as in corridor_analysis.
"""
from __future__ import annotations

import numpy as np

from vsl_lab.data.corridor_analysis import episodes

MPH = 1.609344
BIN_MIN = 5


def nrmse(xhat: np.ndarray, x: np.ndarray, mask: np.ndarray, min_pairs: int = 100):
    """sqrt(mean((xhat - x)^2)) / mean(x) over the masked pairs; None if fewer than min_pairs."""
    m = mask & np.isfinite(x) & np.isfinite(xhat)
    if m.sum() < min_pairs:
        return None
    return float(np.sqrt(np.mean((xhat[m] - x[m]) ** 2)) / np.mean(x[m]))


def scale_table(m_s: dict, group: dict, full_lanes: set, max_dev: float = 0.15) -> dict:
    """m_G = median of m_s over the group's stations whose speed lanes are all their lanes; c_s = m_G / m_s;
    dropped if |c_s - 1| > max_dev."""
    out = {}
    for g in sorted(set(group.values())):
        sids = [s for s in group if group[s] == g]
        ref = [m_s[s] for s in sids if s in full_lanes and np.isfinite(m_s.get(s, np.nan))]
        mG = float(np.median(ref)) if ref else np.nan
        for s in sids:
            c = mG / m_s[s] if np.isfinite(m_s.get(s, np.nan)) else np.nan
            out[s] = {"group": g, "m_s": m_s.get(s), "m_G": mG, "c_s": c, "in_mG": s in full_lanes,
                      "dropped": bool(np.isfinite(c) and abs(c - 1.0) > max_dev)}
    return out


def observe(v_model_kmh: np.ndarray, c_s: float, real_v_mph: np.ndarray, station_valid: bool) -> np.ndarray:
    """Observation operator: model speed (km/h, fitted to scaled real speeds) -> detector scale (mph) by / c_s;
    masked wherever the real bin is NaN, and entirely when the real station-day is event-invalid."""
    if not station_valid:
        return np.full(real_v_mph.shape, np.nan)
    v = v_model_kmh / c_s / MPH
    return np.where(np.isfinite(real_v_mph), v, np.nan)


def pair_episodes(speeds: dict, km: dict, valid: dict, named=(("S1773", "S1140"),), max_km: float = 3.0) -> dict:
    """Corridor rule on consecutive valid stations <= max_km apart; pairs in `named` are allowed beyond max_km."""
    seq = [s for s in sorted(speeds, key=lambda s: km[s]) if valid.get(s, False)]
    out = {}
    for u, d in zip(seq[:-1], seq[1:]):
        if km[d] - km[u] > max_km + 1e-9 and (u, d) not in named:
            continue
        with np.errstate(invalid="ignore"):
            cond = np.nan_to_num(((speeds[u] < 40.0) & ((speeds[d] - speeds[u]) >= 20.0)).astype(float)).astype(bool)
        out[(u, d)] = episodes(cond)
    return out


def censor_time(real_b1: list, real_b2: list):
    """t_c: the onset of a real B2 episode inside a real B1 episode or within 30 min (6 bins) after its end.
    Returns {b1 episode index: t_c}."""
    out = {}
    for i, (s, e) in enumerate(real_b1):
        cands = [s2 for s2, _ in real_b2 if s <= s2 <= e + 6]
        if cands:
            out[i] = min(cands)
    return out


def censored_duration(ep: tuple | None, t_c: int | None) -> int:
    """B1 duration in minutes, censored at t_c (anchored on the real day): min(end, t_c) - onset; 0 for an
    episode starting at or after t_c, and 0 if unmatched (ep is None)."""
    if ep is None:
        return 0
    s, e = ep
    if t_c is None:
        return (e - s + 1) * BIN_MIN
    if s >= t_c:
        return 0
    return (min(e + 1, t_c) - s) * BIN_MIN


def match_episodes(real: list, model: list, tol_bins: int = 18) -> dict:
    """One-to-one, smallest |delta onset| first, within +-90 min. Returns {real index: model index}."""
    pairs = sorted((abs(r[0] - m[0]), i, j) for i, r in enumerate(real) for j, m in enumerate(model)
                   if abs(r[0] - m[0]) <= tol_bins)
    used_r, used_m, out = set(), set(), {}
    for _, i, j in pairs:
        if i not in used_r and j not in used_m:
            out[i] = j
            used_r.add(i)
            used_m.add(j)
    return out


def p7c(eps1: list, eps2: list) -> int:
    """Longest union interval (minutes) of the P_1 and P_2 episodes (inclusive bins); overlapping or
    back-to-back episodes join."""
    iv = sorted([tuple(e) for e in eps1] + [tuple(e) for e in eps2])
    best, cur = 0, None
    for s, e in iv:
        if cur is None or s > cur[1] + 1:
            if cur is not None:
                best = max(best, cur[1] - cur[0] + 1)
            cur = [s, e]
        else:
            cur[1] = max(cur[1], e)
    if cur is not None:
        best = max(best, cur[1] - cur[0] + 1)
    return best * BIN_MIN


def c4(q_down: np.ndarray, ep: tuple, lanes: int, end_cap: int | None = None) -> dict | None:
    """The C4 block: Q_pre = mean flow in the 3 bins before onset; Q_dis = mean from onset + 2 bins to end - 1
    (needs >= 4 bins); r = Q_dis / Q_pre; Q_dis per lane. end_cap censors the window end (B1 on censored days)."""
    s, e = ep
    dur_bins = (e - s + 1) if end_cap is None else (min(e + 1, end_cap) - s)
    last = e if end_cap is None else min(e, end_cap)        # window [s + 2, min(end, t_c)), as uncensored [s + 2, e)
    if dur_bins * BIN_MIN < 30 or s < 3:
        return None
    qpre = np.nanmean(q_down[s - 3:s])
    dis = q_down[s + 2:last]
    if len(dis) < 4 or not np.isfinite(qpre) or qpre <= 0:
        return None
    qd = float(np.nanmean(dis))
    return {"Q_pre": float(qpre), "Q_dis": qd, "r": qd / float(qpre), "Q_dis_per_lane": qd / lanes,
            "window": (s + 2, last)}
