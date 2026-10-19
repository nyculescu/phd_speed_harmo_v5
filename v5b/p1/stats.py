"""P1 statistics and pre-registered rules on numbers (page §3-§6; pure, no SUMO).

Convention (page §5): for reference r and treatment t (delays: lower is better), d_i = r_i - t_i,
rel = median(d) / median(r); the CI is the two-sided percentile bootstrap over seeds (resampled jointly for d and r),
B = 20,000; its rel CI is the percentile CI of median(d*) / median(r*) over the same draws. Mean version (S2):
rel_mean = mean(d) / mean(r), same draws. Levels: S1 1 - 0.05/8, S2 1 - 0.05/4, TV entry 1 - 0.05/12, else 95 %.
"""
from __future__ import annotations

import numpy as np

from v5b.d2.stats import t1_cells  # noqa: F401  (T1 per cell, unchanged from D2)

B_BOOT = 20_000
BOOT_SEED = 20261019
LEVEL_95 = 0.95
LEVEL_S1 = 1.0 - 0.05 / 8
LEVEL_S2 = 1.0 - 0.05 / 4
LEVEL_TV = 1.0 - 0.05 / 12
REL_MIN = 0.10        # S1(a), T0, TV entry
NONINF = -0.05        # S1(b), A2(a): point estimate
T4_MIN = 0.10
TV_BIND = 0.05        # TV-T0: entries into edge 4 change by >= 5 %
TAD_MIN = 2.0         # T-AD: vehicles
PLATEAU_Z = 0.01      # A8: z = 1 point
CHUNK = 1000
TV_NO_BIND_TEXT = ("posted VSL cannot bind on BN4 (the gantry capacity is far above the incident bottleneck): a plant "
                   "limit, not evidence against VSL")
TV_NO_ENTRY_TEXT = "no >= 10 % gain detected on 20 seeds"
NO_SEED = "no seed left in this view"

_IDX = {}


def boot_idx(n: int, B: int = B_BOOT, seed: int = BOOT_SEED) -> np.ndarray:
    key = (n, B, seed)
    if key not in _IDX:
        if len(_IDX) > 8:
            _IDX.clear()
        _IDX[key] = np.random.default_rng(seed).integers(0, n, size=(B, n))
    return _IDX[key]


def _pct(level: float) -> tuple:
    return 100.0 * (1.0 - level) / 2.0, 100.0 * (1.0 + level) / 2.0


def paired(r, t, level: float = LEVEL_95, mean: bool = False, B: int = B_BOOT, seed: int = BOOT_SEED) -> dict:
    r, t = np.asarray(r, float), np.asarray(t, float)
    if r.shape != t.shape or r.size == 0:
        raise ValueError("paired arrays must be non-empty and of equal length")
    d = r - t
    f = np.mean if mean else np.median
    idx = boot_idx(r.size, B, seed)
    sd, sr = f(d[idx], axis=1), f(r[idx], axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel_b = sd / sr
    lo, hi = _pct(level)
    pd_, pr = float(f(d)), float(f(r))
    return {"n": int(r.size), "version": "mean" if mean else "median", "level": level,
            "ref": pr, "treat": float(f(t)), "diff": pd_,
            "diff_ci": [float(np.percentile(sd, lo)), float(np.percentile(sd, hi))],
            "rel": pd_ / pr if pr else float("nan"),
            "rel_ci": [float(np.nanpercentile(rel_b, lo)), float(np.nanpercentile(rel_b, hi))]}


# ---------------------------------------------------------------- invalid runs (page §5)
def views(arrays: dict, invalid) -> dict:
    """The two views of one statistic: all seeds, and the seeds without an invalid run entering it.
    'valid' is None if no seed is left (the statistic then fails in that view)."""
    inv = np.asarray(invalid, bool)
    arrays = {k: np.asarray(v, float) for k, v in arrays.items()}
    keep = ~inv
    return {"all": arrays, "valid": ({k: v[keep] for k, v in arrays.items()} if keep.any() else None),
            "n_invalid_seeds": int(inv.sum()), "n": int(inv.size)}


# ---------------------------------------------------------------- S1 (page §6)
def rule_cell(st: dict) -> dict:
    return {"a": bool(st["rel"] >= REL_MIN and st["diff_ci"][0] > 0.0), "b": bool(st["rel"] >= NONINF)}


def rule_R(per_cell: dict) -> dict:
    """R(t, r) on one view: per_cell = {cell: paired(r, t, LEVEL_S1)} (None = no data in that view: fails)."""
    if not per_cell or any(v is None for v in per_cell.values()):
        return {"cells": {}, "a_cells": [], "pass_a": False, "pass_b": False, "pass": False}
    cells = {c: rule_cell(st) for c, st in per_cell.items()}
    a_cells = [c for c, v in cells.items() if v["a"]]
    pa, pb = bool(a_cells), all(v["b"] for v in cells.values())
    return {"cells": cells, "a_cells": a_cells, "pass_a": pa, "pass_b": pb, "pass": pa and pb}


def s1a(per_r: dict) -> dict:
    """S1a on one view: per_r = {L0 arm r: {cell: paired(r, ID)}}. Passes iff R(ID, r) passes for every r, with (a) met
    in the same cell for all of them (intersection-union, no extra correction)."""
    R = {r: rule_R(pc) for r, pc in per_r.items()}
    if not R:
        return {"R": {}, "common_a_cells": [], "pass": False}
    common = [c for c in next(iter(R.values()))["cells"] if all(c in R[r]["a_cells"] for r in R)]
    return {"R": R, "common_a_cells": common,
            "binding": min(R, key=lambda r: (R[r]["pass"], len(R[r]["a_cells"]))),
            "pass": bool(common) and all(R[r]["pass"] for r in R)}


def two_views(fn, view_all, view_valid) -> dict:
    """A statement must hold on all seeds AND with the invalid seeds of each statistic removed (page §5)."""
    a, v = fn(view_all), fn(view_valid)
    return {"all_seeds": a, "valid_only": v, "pass": bool(a["pass"] and v["pass"])}


# ---------------------------------------------------------------- S2 (page §6)
def s2_cell(ip, or_in, orx: dict, level: float = LEVEL_S2, z: float = PLATEAU_Z) -> dict:
    """One view of one cell. orx = {R: per-seed ORX_R delays}. x = upper CI bound of rel(IP, OR_in) (median);
    y = lower CI bound of rel_mean(IP, ORX_Rmax); y_hat = rel_mean(IP, ORX_Rmax) if the 95 % CI of
    rel_mean(ORX_{Rmax/2}, ORX_Rmax) lies within +-z."""
    Rs = sorted(orx)
    rmax = Rs[-1]
    out = {"OR_in": {"median": paired(ip, or_in, level), "mean": paired(ip, or_in, level, mean=True)},
           "ORX": {R: {"median": paired(ip, orx[R], level), "mean": paired(ip, orx[R], level, mean=True)} for R in Rs}}
    x = out["OR_in"]["median"]["rel_ci"][1]
    y = out["ORX"][rmax]["mean"]["rel_ci"][0]
    y_hat = out["ORX"][rmax]["mean"]["rel"]
    plateau = paired(orx[rmax // 2], orx[rmax], LEVEL_95, mean=True) if rmax // 2 in orx else None
    ok = plateau is not None and -z <= plateau["rel_ci"][0] and plateau["rel_ci"][1] <= z
    out.update({"x": x, "y": y, "y_hat": y_hat, "plateau": plateau, "plateau_holds": bool(ok), "Rmax": rmax})
    return out


def s2_statements(v_all: dict, v_valid) -> dict:
    """Combine the two views (page §5): 'at most' uses the larger x, 'at least' the smaller y (stated only if > 0 in
    both views), 'about y_hat' only if the plateau holds in both views; otherwise only the bracket [y, x]."""
    vs = [v for v in (v_all, v_valid) if v is not None]
    x = max(v["x"] for v in vs) if v_valid is not None else float("inf")
    y = min(v["y"] for v in vs) if v_valid is not None else float("-inf")
    about = v_valid is not None and all(v["plateau_holds"] for v in vs)
    st = {"x": x, "y": y, "adds_at_most_pct": 100 * x, "adds_at_least_pct": (100 * y if y > 0 else None),
          "adds_about_pct": (100 * v_all["y_hat"] if about else None),
          "adds_about_pct_valid_only": (100 * v_valid["y_hat"] if about else None)}
    st["text"] = (f"adds at most {100 * x:.1f} %" + (f"; adds at least {100 * y:.1f} %" if y > 0 else "") +
                  (f"; adds about {100 * v_all['y_hat']:.1f} % (biased low)" if about else
                   f"; bracket [{100 * y:.1f}, {100 * x:.1f}] %"))
    return st


def tp_placebo(ip_main, ip_reps) -> dict:
    """TP (report only): per seed, IP's main run vs the best of IP's main run and its replicates, rel(IP_main, min)."""
    m = np.asarray(ip_main, float)
    best = np.minimum(m, np.asarray(ip_reps, float).min(axis=1))
    return paired(m, best, LEVEL_95)


# ---------------------------------------------------------------- mixtures (page §4, §6)
def mixture(a, b, p):
    """Per-seed exact mixture (1 - p) a + p b."""
    return (1.0 - p) * np.asarray(a, float) + p * np.asarray(b, float)


def prevalence_mix(d_slow, d_block, d_clean, pi: float):
    """Per-seed pi (D_slow + D_block) / 2 + (1 - pi) D_clean."""
    return pi * (np.asarray(d_slow, float) + np.asarray(d_block, float)) / 2.0 + (1.0 - pi) * np.asarray(d_clean, float)


# ---------------------------------------------------------------- break-even (page §4)
def crossing(M: np.ndarray, grid, kind: str) -> tuple:
    """Vectorised over rows of M (b x G): (value, flag) with flag 0 = crossing found, 1 = 'IP never ahead'
    (M(grid[0]) <= 0; value grid[0]), 2 = beyond the grid ('> max'; value grid[-1]).
    kind 'linear' (d*, c*): linear interpolation to the first crossing of M = 0; kind 'first' (p*, f*): the first grid
    point with M <= 0."""
    M = np.atleast_2d(np.asarray(M, float))
    g = np.asarray(grid, float)
    leq = M <= 0.0
    has = leq.any(axis=1)
    i = np.argmax(leq, axis=1)
    val = np.where(has, g[i], g[-1])
    flag = np.where(~has, 2, np.where(i == 0, 1, 0))
    if kind == "linear":
        j = np.where(has & (i > 0), i, 1)
        m0, m1 = M[np.arange(M.shape[0]), j - 1], M[np.arange(M.shape[0]), j]
        with np.errstate(divide="ignore", invalid="ignore"):
            x = g[j - 1] + (g[j] - g[j - 1]) * m0 / (m0 - m1)
        val = np.where(has & (i > 0), x, val)
    elif kind != "first":
        raise ValueError(kind)
    return val, flag


FLAGS = {0: "crossing", 1: "IP never ahead", 2: "> max"}


def breakeven(X_by_arm: dict, grid, kind: str, level: float = LEVEL_95, B: int = B_BOOT, seed: int = BOOT_SEED) -> dict:
    """X_by_arm = {L0 arm: (n seeds x G) per-seed L0 - IP at each grid level}. Per arm M = median over seeds; the
    reported break-even is the smallest over the L0 arms (intersection-union; ties to the earlier arm). CI: percentile
    bootstrap over seeds of the same procedure (one joint resample for all arms, the minimum per draw); censored draws
    stay at their censoring value (grid end), and their shares are reported."""
    arms = list(X_by_arm)
    X = {a: np.asarray(X_by_arm[a], float) for a in arms}
    n = next(iter(X.values())).shape[0]
    per = {}
    for a in arms:
        v, f = crossing(np.median(X[a], axis=0)[None, :], grid, kind)
        per[a] = {"value": float(v[0]), "flag": FLAGS[int(f[0])], "M": np.median(X[a], axis=0).tolist()}
    bind = min(arms, key=lambda a: (per[a]["value"], arms.index(a)))
    idx = boot_idx(n, B, seed)
    vals, flags = np.empty(B), np.empty(B, int)
    for s in range(0, B, CHUNK):
        ib = idx[s:s + CHUNK]
        vv, ff = [], []
        for a in arms:
            v, f = crossing(np.median(X[a][ib], axis=1), grid, kind)
            vv.append(v)
            ff.append(f)
        vv, ff = np.array(vv), np.array(ff)
        k = np.argmin(vv, axis=0)            # first minimal arm per draw
        vals[s:s + CHUNK] = vv[k, np.arange(vv.shape[1])]
        flags[s:s + CHUNK] = ff[k, np.arange(vv.shape[1])]
    lo, hi = _pct(level)
    return {"value": per[bind]["value"], "flag": per[bind]["flag"], "binding_arm": bind, "per_arm": per,
            "ci": [float(np.percentile(vals, lo)), float(np.percentile(vals, hi))],
            "share_censored_gt_max": float(np.mean(flags == 2)), "share_never_ahead": float(np.mean(flags == 1)),
            "n": int(n), "grid": [float(x) for x in grid]}


# ---------------------------------------------------------------- tool checks (page §3)
def t0_cells(best_by_cell: dict, nc_by_cell: dict, best_name: dict) -> dict:
    """T0: in every incident cell the best non-oracle arm beats NC: rel >= 10 % and 95 % CI of median(NC - best) > 0.
    A cell given as None (no seed left in a view) fails."""
    per = {}
    for c in best_by_cell:
        if best_by_cell[c] is None:
            per[c] = {"n": 0, "best_arm": best_name[c], "pass": False, "note": NO_SEED}
            continue
        r = paired(nc_by_cell[c], best_by_cell[c], LEVEL_95)
        r["best_arm"] = best_name[c]
        r["pass"] = bool(r["rel"] >= REL_MIN and r["diff_ci"][0] > 0.0)
        per[c] = r
    return {"cells": per, "pass": bool(per) and all(p["pass"] for p in per.values())}


def t4_cell(n_delays, best_delays, n_id: str, best_id: str) -> dict:
    """T4 (D2-A5): N_t vs the hindsight-best fixed controller of G in this cell: rel >= 10 % (point; CI reported).
    None delays (no seed left in a view) fail."""
    if n_delays is None:
        return {"n": 0, "N": n_id, "best_fixed": best_id, "same_controller": n_id == best_id, "pass": False,
                "note": NO_SEED}
    r = paired(n_delays, best_delays, LEVEL_95)
    r.update({"N": n_id, "best_fixed": best_id, "same_controller": n_id == best_id,
              "pass": bool(n_id != best_id and r["rel"] >= T4_MIN)})
    return r


def t4_overall(cells: dict) -> dict:
    return {"cells": cells, "n_pass": int(sum(c["pass"] for c in cells.values())),
            "pass": bool(cells) and all(c["pass"] for c in cells.values())}


def tad_cells(devs_by_cell: dict) -> dict:
    """T-AD: per incident cell, AD binds iff the median over runs of max |n_hat - n_hat(0)| during the incident
    is >= 2 vehicles; otherwise 'AD not identifiable on BN4' for that cell (report only; AD stays in every comparison)."""
    out = {}
    for c, v in devs_by_cell.items():
        v = np.asarray(v, float)
        med = float(np.median(v)) if v.size else float("nan")
        out[c] = {"n": int(v.size), "median_max_dev": med, "binds": bool(med >= TAD_MIN),
                  "note": "" if med >= TAD_MIN else "AD not identifiable on BN4"}
    return out


def tv_binding(nc_counts: dict, vsl_counts: dict) -> dict:
    """TV-T0: NC vs NC + VSL (b = 0.4). Binding iff, in >= 1 incident cell, the number of vehicles entering edge 4
    between onset and clearance changes by >= 5 % (|rel|) with the 95 % CI of the median paired difference excluding 0."""
    per = {}
    for c in nc_counts:
        if nc_counts[c] is None:
            per[c] = {"n": 0, "binds": False, "note": NO_SEED}
            continue
        r = paired(nc_counts[c], vsl_counts[c], LEVEL_95)
        r["binds"] = bool(abs(r["rel"]) >= TV_BIND and (r["diff_ci"][0] > 0.0 or r["diff_ci"][1] < 0.0))
        per[c] = r
    ok = any(p["binds"] for p in per.values())
    return {"cells": per, "pass": ok, "text": "" if ok else TV_NO_BIND_TEXT}


def tv_entry(ip_by_bc: dict, ipv_by_bc: dict) -> dict:
    """TV entry: IP_t + VSL vs IP_t per (b, cell); VSL enters iff rel >= 10 % with the Bonferroni (m = 12) CI lower
    bound of median(IP - IP+VSL) > 0 in >= 1 (b, cell)."""
    per = {}
    for k in ip_by_bc:
        if ip_by_bc[k] is None:
            per[k] = {"n": 0, "pass": False, "note": NO_SEED}
            continue
        r = paired(ip_by_bc[k], ipv_by_bc[k], LEVEL_TV)
        r["pass"] = bool(r["rel"] >= REL_MIN and r["diff_ci"][0] > 0.0)
        per[k] = r
    ok = any(p["pass"] for p in per.values())
    return {"cells": per, "enters": ok, "text": "" if ok else TV_NO_ENTRY_TEXT}
