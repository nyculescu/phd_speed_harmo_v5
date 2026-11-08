"""Loading, arm definitions and round 2's statistic for the x1_exposure analysis. Reads only."""
import json
import pickle
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
DATA = Path("/home/catalin/work/phd/v5b1_runs/measure_s01_remote")
R2ROWS = Path("/home/catalin/work/phd/v5b1_runs/round2/test/rows_6c49e7e.jsonl")
WT = Path("/home/catalin/work/phd/wt/r2-metrics")
Q = 5300.0
DT = 0.1     # simulation step (s); vehicle-steps x DT = vehicle-seconds
V_BIN = 5.0     # km/h, measure.py speed histogram bins
LEARNERS = {"v3w": ["w0u250", "w1u500", "w2u250", "w3u500", "w4u500"], "tail": [f"t{i}" for i in range(5)],
            "sw": [f"s{i}u500" for i in range(5)], "baseline-v3": [f"d{i}u500" for i in range(5)]}


def arms(cell: str) -> dict:
    a = {"nc": ["nc"], "p333": ["p333"], "os1_15_10": ["os1_15_10"], "3E-T": ["3e"], f"3E-X{cell[1]}": [f"3ex{cell[1]}"]}
    return a | LEARNERS


# Mainline edges (start offsets from the rows' m_offsets) and the slowdown periods in absolute time (plant_sweep.period).
OFF = {"1": 0.0, "2": 3000.0, "3a": 3498.3, "3": 3793.02, "4a": 4987.32, "4": 5282.04, "5": 6278.04, "_end": 6778.04}
EDGES = ("1", "2", "3a", "3", "4a", "4", "5")
PERT = {"X1": {"times": [600.0, 1200.0], "dur": 120.0, "taper": 20.0}, "X2": {"times": [700.0], "dur": 180.0, "taper": 20.0}}
PERIODS = ("before", "taper", "hold", "after", "rest")
SPEED_CLS = (0.0, 18.0, 36.0, 60.0, 80.0, 1e9)     # km/h, cell mean speed classes of the space-time field


def period(t: float, spec: dict) -> str:
    if t < spec["times"][0]:
        return "before"
    for t0 in spec["times"]:
        if t0 <= t < t0 + spec["taper"]:
            return "taper"
        if t0 <= t < t0 + spec["dur"]:
            return "hold"
        if t0 + spec["dur"] <= t < t0 + spec["dur"] + 120.0:
            return "after"
    return "rest"


def time_bin_period(cell: str, nt: int = 150) -> list:
    """Period of each 10-s field bin by its majority second; bin k holds t in (300 + 10k, 310 + 10k]."""
    out = []
    for k in range(nt):
        ps = [period(300.0 + 10 * k + s, PERT[cell]) for s in range(1, 11)]
        out.append(max(set(ps), key=ps.count))
    return out


def space_bin_edge(nx: int = 136, dx: float = 50.0) -> list:
    """Edge of each 50-m field bin by its centre."""
    out = []
    for j in range(nx):
        c = (j + 0.5) * dx
        out.append(next(e for e in reversed(EDGES) if c >= OFF[e]))
    return out


def band_exposure(vh: list) -> dict:
    """Vehicle-steps per 5 km/h bin -> vehicle-seconds in plant_sweep's follower speed bands (lo < 18 km/h, mid 18-36, hi >= 36),
    splitting the 15-20 and 35-40 km/h bins uniformly; plus moving (>= 5 km/h) and bounds of the lo band."""
    h = np.asarray(vh, float) * DT
    lo = h[:3].sum() + 0.6 * h[3]
    mid = 0.4 * h[3] + h[4:7].sum() + 0.2 * h[7]
    hi = 0.8 * h[7] + h[8:].sum()
    return {"e_lo": lo, "e_mid": mid, "e_hi": hi, "e_stop5": h[0], "e_mov5": h[1:].sum(), "e_lo_min": h[:3].sum(), "e_lo_max": h[:4].sum(), "e_all": h.sum()}


def st_features(f: Path, cell: str, tp: list, se: list) -> dict:
    z = np.load(f)
    v, n = z["v"].astype(float), z["n"].astype(float)
    sp = np.where(n > 0, 3.6 * v / np.maximum(n, 1.0), np.nan)
    out = {"st_vs": n.sum(), "st_jam": n[sp < 30.0].sum(), "st_dist": v.sum()}
    cls = np.digitize(np.nan_to_num(sp, nan=200.0), SPEED_CLS[1:-1])     # 0..4
    tp, se = np.array(tp), np.array(se)
    for p in PERIODS:
        m = tp == p
        out[f"st_vs_p_{p}"] = n[m].sum()
        out[f"st_mov18_p_{p}"] = n[m][sp[m] >= 18.0].sum()
    for e in EDGES:
        m = se == e
        out[f"st_vs_e_{e}"] = n[:, m].sum()
        out[f"st_mov18_e_{e}"] = n[:, m][sp[:, m] >= 18.0].sum()
        out[f"st_jam_e_{e}"] = n[:, m][sp[:, m] < 30.0].sum()
    for p in PERIODS:
        m = tp == p
        out[f"st_jam_p_{p}"] = n[m][sp[m] < 30.0].sum()
        out[f"st_lo_p_{p}"] = n[m][sp[m] < 18.0].sum()
        for e in ("3", "4a", "4"):
            me = se == e
            sub_n, sub_s = n[m][:, me], sp[m][:, me]
            out[f"st_vs_pe_{p}_{e}"] = sub_n.sum()
            out[f"st_jam_pe_{p}_{e}"] = sub_n[sub_s < 30.0].sum()
    for k in range(len(SPEED_CLS) - 1):
        out[f"st_vs_c{k}"] = n[cls == k].sum()
    # density-weighted exposure: vehicle-seconds times the cell's density (veh/km over all lanes), moving cells only
    dens = n / 10.0 / 0.05
    out["st_dense_mov"] = (n * dens)[sp >= 18.0].sum() / max(n[sp >= 18.0].sum(), 1.0)
    return out


def load(rows_file: str = "rows_test.jsonl", cache: str = "cache_test_v2.pkl") -> dict:
    """(name, q) -> seed -> row with numeric fields, pack band exposures and space-time features."""
    cf = HERE / cache
    if cf.exists():
        return pickle.load(open(cf, "rb"))
    T = defaultdict(dict)
    tps = {c: time_bin_period(c) for c in PERT}
    se = space_bin_edge()
    with open(DATA / rows_file) as h:
        for line in h:
            r = json.loads(line)
            cell = r["name"].split("|")[0]
            x = {k: v for k, v in r.items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
            x["name"] = r["name"]
            vh = np.sum([r[f"m_vh_{c}"] for c in ("car", "alks", "truck")], axis=0)
            x |= band_exposure(vh)
            x["vh_all"] = (np.asarray(vh, float) * DT).tolist()
            if cell in PERT:
                x |= st_features(DATA / "st" / r["m_st_file"], cell, tps[cell], se)
            T[(r["name"], r["q"])][r["seed"]] = x
    T = dict(T)
    pickle.dump(T, open(cf, "wb"))
    return T


def val(row: dict, key: str) -> float:
    v = row.get(key)
    return 0.0 if v is None else float(v)


def arm_mean(T: dict, names: list, q: float = Q) -> dict:
    """Per seed, the mean over the learners of every numeric key (decide2/common1.arm_mean)."""
    rows = [T[(n, q)] for n in names]
    seeds = sorted(set.intersection(*(set(r) for r in rows)))
    keys = {k for r in rows for s in seeds for k, v in r[s].items() if isinstance(v, (int, float)) and not isinstance(v, bool)}
    return {s: {"seed": s, **{k: sum(val(r[s], k) for r in rows) / len(rows) for k in keys}} for s in seeds}


N_BOOT, RNG = 20000, 20261104


def boot_idx(n: int) -> np.ndarray:
    return np.random.default_rng(RNG).integers(0, n, (N_BOOT, n))


def raw(A: dict, B: dict, key: str, sign: int = -1, pct=(2.5, 97.5)) -> tuple:
    """conf3/common.raw at 95 %: sign x median(P - O) / median(O) x 100, percentile bootstrap of seeds, denominator fixed."""
    ds = sorted(set(A) & set(B))
    ref = max(float(np.median([val(B[k], key) for k in ds])), 1e-9)
    d = np.array([sign * (val(A[k], key) - val(B[k], key)) / ref * 100 for k in ds])
    lo, hi = np.percentile(np.median(d[boot_idx(len(d))], axis=1), pct)
    return float(np.median(d)), float(lo), float(hi)


def paired(A: dict, B: dict, key: str) -> np.ndarray:
    ds = sorted(set(A) & set(B))
    return np.array([val(A[k], key) - val(B[k], key) for k in ds])


def ci(x: np.ndarray, stat=np.median) -> tuple:
    b = stat(x[boot_idx(len(x))], axis=1)
    return float(stat(x)), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def ratio_ci(num: np.ndarray, den: np.ndarray) -> tuple:
    """mean(num) / mean(den) with a paired seed bootstrap."""
    idx = boot_idx(len(num))
    b = num[idx].mean(1) / den[idx].mean(1)
    return float(num.mean() / den.mean()), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = np.argsort(np.argsort(x)), np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def corr_ci(x: np.ndarray, y: np.ndarray, n_perm: int = 10000) -> dict:
    """Spearman rho, its seed-bootstrap 95 % CI and a two-sided permutation p (the no-association null)."""
    rho = spearman(x, y)
    idx = boot_idx(len(x))
    bs = np.array([spearman(x[i], y[i]) for i in idx])
    rng = np.random.default_rng(RNG + 1)
    null = np.array([spearman(x, rng.permutation(y)) for _ in range(n_perm)])
    return {"rho": round(rho, 3), "ci": [round(float(np.nanpercentile(bs, 2.5)), 3), round(float(np.nanpercentile(bs, 97.5)), 3)],
            "perm_p": round(float((np.abs(null) >= abs(rho)).mean()), 4), "null_95": round(float(np.percentile(np.abs(null), 95)), 3)}
