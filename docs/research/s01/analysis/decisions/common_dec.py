"""Shared helpers: per-run decision metrics, arm means over learners and round 2's statistic (conf3/common.py raw, reimplemented)."""
import pickle
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
HEADWAYS = (1.6, 1.2, 1.0, 0.8)     # b_env.HEADWAYS_S: level index -> time gap, s
GROUPS = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"], "tail": [f"t{i}" for i in range(5)],
          "sw": [f"s{i}u500" for i in range(5)], "baseline-v3": [f"d{i}u500" for i in range(5)]}
RULES = {"nc": ["nc"], "p333": ["p333"], "os1_15_10": ["os1_15_10"], "3E-T": ["3e"]}
ROADS = ("1", "2", "3a", "3", "4a", "4", "5", "r", "rj", "r2", "rj2")
MAIN_KM = 136 * 0.05     # space-time grid: 136 cells of 50 m
EPISODE_S = 1500.0
B, SEED_RNG = 20000, 20261104


def quantile_binned(counts, lo, width, q):
    """measure.quantiles for one q."""
    c = np.asarray(counts, float)
    tot = c.sum()
    if tot <= 0:
        return None
    cum = np.cumsum(c) / tot
    i = int(np.searchsorted(cum, q))
    prev = cum[i - 1] if i else 0.0
    return lo + width * (i + (q - prev) / max(cum[i] - prev, 1e-12))


def metrics(r: dict) -> dict:
    out = {"all_delay": r["all_delay"], "ttc_net": r["ttc_net"], "passed": r["passed"],
           "density": r["st_veh_s"] / EPISODE_S / MAIN_KM}
    for rd in ROADS:
        n = r.get(f"lv_n_{rd}", 0.0)
        out[f"lv_{rd}"] = r.get(f"lv_sum_{rd}", 0.0) / n if n else None
    T = r.get("m_dec_totals") or {}
    if not T:
        return out
    L = np.asarray(r["m_dec_level_s"], float)
    on = L.sum()
    W = np.asarray(r["m_dec_want"], float)
    C = np.asarray(r["m_dec_conf"], float)
    out |= {"applied_share": T["changed"] / T["asked"], "kept_share": T["kept"] / T["asked"], "ignored_share": T["ignored"] / T["asked"],
            "reversal_share": T["reversals"] / T["changed"] if T["changed"] else None,
            "excess_per_veh": r["m_dec_excess"] / r["m_dec_vehicles"], "changes_per_veh": T["changed"] / r["m_dec_vehicles"],
            "asked_per_veh": T["asked"] / r["m_dec_vehicles"],
            "v2v_on": on / (on + r["m_dec_off_s"]), "gap_on": float((L * np.array(HEADWAYS)).sum() / on) if on else None,
            "conf_med": quantile_binned(C, 0.0, 0.1, 0.5), "conf_p05": quantile_binned(C, 0.0, 0.1, 0.05),
            "conf_lt05": float(C[:5].sum() / C.sum()) if C.sum() else None, "entropy": r["m_dec_entropy_mean"]}
    for i in range(4):
        out[f"share{i}"] = L[i] / on if on else None
        out[f"want{i}"] = W[i] / W.sum() if W.sum() else None
    pl = r["m_dec_place"]
    tot_changed = sum(v[1] for v in pl.values())
    for k, v in pl.items():
        out[f"changed_at_{k}"] = v[1] / tot_changed if tot_changed else None
    return out


def load_table() -> dict:
    """(phase, cell, q) -> arm name -> seed -> metrics."""
    T = pickle.load(open(HERE / "compact.pkl", "rb"))
    M = {}
    for (ph, name, q, seed), r in T.items():
        cell, arm = name.split("|")
        M.setdefault((ph, cell, q), {}).setdefault(arm, {})[seed] = metrics(r)
    return M


def arm_values(M: dict, key: tuple, names: list, f: str) -> dict:
    """seed -> mean over the arm's learners (decide2.arm_mean); seeds where any learner lacks the value are dropped."""
    runs = [M[key].get(n) for n in names]
    if any(x is None for x in runs):
        return {}
    seeds = sorted(set.intersection(*[set(x) for x in runs]))
    out = {}
    for s in seeds:
        v = [x[s].get(f) for x in runs]
        if all(y is not None for y in v):
            out[s] = float(np.mean(v))
    return out


def raw(A: dict, Bd: dict, sign: int = -1, pct=(2.5, 97.5)) -> tuple:
    """conf3/common.py raw on seed -> value dicts: sign x median(A - B) / median(B) x 100, percentile bootstrap."""
    ds = sorted(set(A) & set(Bd))
    ref = max(float(np.median([Bd[k] for k in ds])), 1e-9)
    d = np.array([sign * (A[k] - Bd[k]) / ref * 100 for k in ds])
    rng = np.random.default_rng(SEED_RNG)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (B, len(d)))], axis=1), pct)
    return float(np.median(d)), float(lo), float(hi), len(ds)


def paired_diff(A: dict, Bd: dict, pct=(2.5, 97.5)) -> tuple:
    """median(A - B) in the metric's own units, same bootstrap."""
    ds = sorted(set(A) & set(Bd))
    d = np.array([A[k] - Bd[k] for k in ds])
    rng = np.random.default_rng(SEED_RNG)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (B, len(d)))], axis=1), pct)
    return float(np.median(d)), float(lo), float(hi), len(ds)


def med_ci(A: dict, pct=(2.5, 97.5)) -> tuple:
    """Median over seeds and its percentile bootstrap CI (one arm, no pairing)."""
    x = np.array(list(A.values()), float)
    rng = np.random.default_rng(SEED_RNG)
    lo, hi = np.percentile(np.median(x[rng.integers(0, len(x), (B, len(x)))], axis=1), pct)
    return float(np.median(x)), float(lo), float(hi), len(x)


def fmt(t: tuple, nd: int = 3) -> str:
    return f"{t[0]:.{nd}f} [{t[1]:.{nd}f}, {t[2]:.{nd}f}] n={t[3]}"
