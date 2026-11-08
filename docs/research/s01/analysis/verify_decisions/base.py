"""Own helpers: table by (cell, arm, q) -> seed -> row; arm pooling; the round-2 statistic, written from its definition."""
import pickle
from collections import defaultdict
from pathlib import Path
import numpy as np

HERE = Path(__file__).parent
HW = (1.6, 1.2, 1.0, 0.8)
ARMS = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"], "tail": [f"t{i}" for i in range(5)],
        "sw": [f"s{i}u500" for i in range(5)], "bv3": [f"d{i}u500" for i in range(5)]}

def load():
    rows = pickle.load(open(HERE / "rows.pkl", "rb"))
    T = defaultdict(dict)
    for r in rows:
        cell, arm = r["name"].split("|")
        T[(cell, arm, float(r["q"]))][int(r["seed"])] = r
    return rows, T

def g(r, k):
    v = r.get(k)
    return 0.0 if v is None else float(v)

def derived(r):
    """Decision metrics of one run from the raw pack fields."""
    if not r.get("m_dec_totals"):
        return None
    T = r["m_dec_totals"]; L = np.array(r["m_dec_level_s"], float); on = L.sum()
    c = np.array(r["m_dec_conf"], float)
    out = {"asked": T["asked"], "changed": T["changed"], "reversals": T["reversals"], "ignored": T["ignored"], "kept": T["kept"],
           "veh": r["m_dec_vehicles"], "applied": T["changed"] / T["asked"], "rev_share": T["reversals"] / T["changed"] if T["changed"] else np.nan,
           "excess_pv": r["m_dec_excess"] / r["m_dec_vehicles"], "chg_pv": T["changed"] / r["m_dec_vehicles"], "asked_pv": T["asked"] / r["m_dec_vehicles"],
           "on_s": on, "off_s": r["m_dec_off_s"], "on_share": on / (on + r["m_dec_off_s"]),
           "share0": L[0] / on, "share3": L[3] / on, "gap_on": float((L / on) @ np.array(HW)), "s3_abs": L[3],
           "want3": r["m_dec_want"][3] / max(sum(r["m_dec_want"]), 1),
           "ent": r["m_dec_entropy_mean"] if r["m_dec_entropy_mean"] is not None else np.nan,
           "conf_med": binned_q(c, 0.5) if c.sum() else np.nan, "conf_lt05": c[:5].sum() / c.sum() if c.sum() else np.nan}
    return out

def binned_q(c, q, lo=0.0, w=0.1):
    """Quantile of a histogram with linear interpolation within the bin (my own, from the docstring's definition)."""
    cum = np.cumsum(c) / c.sum()
    i = int(np.argmax(cum >= q))
    prev = cum[i - 1] if i > 0 else 0.0
    return lo + w * (i + (q - prev) / max(cum[i] - prev, 1e-12))

def arm_series(T, cell, names, q, f):
    """Per seed, mean over learners of f(row); only seeds every learner has."""
    tabs = [T[(cell, n, q)] for n in names]
    seeds = sorted(set.intersection(*[set(t) for t in tabs]))
    return {s: float(np.mean([f(t[s]) for t in tabs])) for s in seeds}

def boot_median(d, B=20000, pct=(2.5, 97.5)):
    d = np.asarray(d, float)
    rng = np.random.default_rng(20261104)
    m = np.median(d[rng.integers(0, len(d), (B, len(d)))], axis=1)
    lo, hi = np.percentile(m, pct)
    return float(np.median(d)), float(lo), float(hi)

def paired_diff(A, B):
    s = sorted(set(A) & set(B))
    return boot_median([A[k] - B[k] for k in s]), len(s)

def effect(P, O, sign=-1):
    """sign x median(P-O)/median(O) x 100, fixed denominator, bootstrap of seeds."""
    s = sorted(set(P) & set(O))
    ref = max(float(np.median([O[k] for k in s])), 1e-9)
    d = [sign * (P[k] - O[k]) / ref * 100 for k in s]
    return boot_median(d), len(s)

def fmt(t, nd=3):
    return f"{t[0]:+.{nd}f} [{t[1]:+.{nd}f}, {t[2]:+.{nd}f}]"
