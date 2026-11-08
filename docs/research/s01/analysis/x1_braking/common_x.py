"""Shared loading and statistics for the x1_braking analysis. The statistic is round 2's own: conf3/common.raw (median of paired
differences over the opponent's median, percentile bootstrap, 20,000 resamples, default_rng(20261104)) at 95 % (2.5, 97.5), and
common1.arm_mean (an arm's value per seed = the mean over its learners), imported read-only from the r2-metrics worktree."""
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

WT = Path("/home/catalin/work/phd/wt/r2-metrics/docs/research")
sys.path[:0] = [str(WT / "round1"), str(WT / "conf3")]
from common1 import arm_mean  # noqa: E402
from common import raw, val  # noqa: E402

OUT = Path(__file__).resolve().parent
Q = 5300.0
P95 = (2.5, 97.5)
GROUPS = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"], "tail": ["t0", "t1", "t2", "t3", "t4"],
          "sw": ["s0u500", "s1u500", "s2u500", "s3u500", "s4u500"], "bv3": ["d0u500", "d1u500", "d2u500", "d3u500", "d4u500"]}
POLICIES = ("v3w", "tail", "sw", "bv3")
RULES = {"X1": ("nc", "3e", "3ex1", "p333", "os1_15_10"), "X2": ("nc", "3e", "3ex2", "p333", "os1_15_10")}


def derive(r: dict) -> dict:
    """Derived per-run braking metrics. Peak bins (measure.PEAK_EDGES): 0 (-3,-3.5], 1 (-3.5,-4], 2 (-4,-4.5], 3 (-4.5,-5], 4 (-5,-6],
    5 (-6,-7], 6 (-7,-8], 7 (-8,-9], 8 (-9 or harder]. Acceleration bins (m_ah): index int((a + 10) / 0.5)."""
    d = {}
    km = {c: r[f"m_dist_m_{c}"] / 1000.0 for c in ("car", "alks", "truck")}
    km_all = sum(km.values())
    for c in ("car", "alks", "truck"):
        pk = np.asarray(r[f"m_peak_{c}"])
        d[f"ev45_{c}"] = float(pk[3:].sum())     # = summary events_ge45_<c>
        d[f"ev4_{c}"] = float(pk[2:].sum())     # peak at -4.0 or harder: insensitive to the floating-point side of -4.5
        d[f"ev5_{c}"] = float(pk[4:8].sum())     # peak beyond -5.0 and above -9.0: harder than the normal decel limit
        d[f"ev9_{c}"] = float(pk[8])
        d[f"ev_{c}"] = float(r[f"m_events_{c}"])
        d[f"casc_{c}"] = float(r[f"m_cascade_{c}"])
        d[f"cshare_{c}"] = r[f"m_cascade_{c}"] / r[f"m_events_{c}"] if r[f"m_events_{c}"] else 0.0
        d[f"km_{c}"] = km[c]
        d[f"vs_{c}"] = r[f"m_n_{c}"] * 0.1
        d[f"lt5_steps_{c}"] = float(sum(r[f"m_ah_{c}"][:10]))     # vehicle-steps with a < -5.0
        d[f"ev45_{c}_per_km"] = d[f"ev45_{c}"] / km[c] if km[c] else 0.0
        d[f"ev4_{c}_per_km"] = d[f"ev4_{c}"] / km[c] if km[c] else 0.0
        d[f"ev5_{c}_per_km"] = d[f"ev5_{c}"] / km[c] if km[c] else 0.0
    d["ev45_all"] = d["ev45_car"] + d["ev45_alks"] + d["ev45_truck"]
    d["ev4_all"] = d["ev4_car"] + d["ev4_alks"] + d["ev4_truck"]
    d["ev_all"] = d["ev_car"] + d["ev_alks"] + d["ev_truck"]
    d["casc_all"] = d["casc_car"] + d["casc_alks"] + d["casc_truck"]
    d["cshare_all"] = d["casc_all"] / d["ev_all"] if d["ev_all"] else 0.0
    d["km_all"] = km_all
    d["ev45_all_per_km"] = d["ev45_all"] / km_all
    d["ev4_all_per_km"] = d["ev4_all"] / km_all
    for k in ("ev45_all", "ev45_car", "ev45_alks", "ev4_all", "ev5_alks"):
        d[f"{k}_per_served"] = d[k] / r["passed"] if r["passed"] else 0.0
    d["human_b45_step"] = val(r, "b45_step") - val(r, "alks_b45_step")     # cars and trucks
    d["human_b3_step"] = val(r, "b3_step") - val(r, "alks_b3_step")
    d["alks_b45_step_per_km"] = val(r, "alks_b45_step") / km["alks"]
    d["human_b45_step_per_km"] = d["human_b45_step"] / (km["car"] + km["truck"])
    d["b45_step_per_km"] = val(r, "b45_step") / km_all
    d["b45_step_per_served"] = val(r, "b45_step") / r["passed"]
    d["alks_b45_share"] = val(r, "alks_b45_step") / val(r, "b45_step") if val(r, "b45_step") else 0.0
    return d


def load_T(fname: str = "test_rows.pkl") -> dict:
    """(name, q) -> seed -> row, with the derived keys added."""
    rows = pickle.load(open(OUT / fname, "rb"))
    T = defaultdict(dict)
    for (n, s), r in rows.items():
        x = {k: v for k, v in r.items() if not isinstance(v, (list, dict))}
        x |= derive(r)
        T[(n, r["q"])][s] = x
    return T


def arm(T: dict, cell: str, g: str) -> dict:
    names = GROUPS.get(g, [g])
    return arm_mean(T, [f"{cell}|{n}" for n in names], Q)


def diff_ci(A: dict, B: dict, key: str) -> tuple:
    """Median of paired differences A - B in the metric's own units, with the same bootstrap (resample seeds, same rng seed)."""
    ds = sorted(set(A) & set(B))
    d = np.array([val(A[k], key) - val(B[k], key) for k in ds])
    rng = np.random.default_rng(20261104)
    lo, hi = np.percentile(np.median(d[rng.integers(0, len(d), (20000, len(d)))], axis=1), P95)
    return float(np.median(d)), float(lo), float(hi)


def effect95(A: dict, B: dict, key: str, sign: int = -1) -> tuple:
    return raw(A, B, key, sign=sign, pct=P95)


def med(A: dict, key: str) -> float:
    return float(np.median([val(x, key) for x in A.values()]))
