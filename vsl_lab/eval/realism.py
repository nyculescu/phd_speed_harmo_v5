"""Plant-realism signatures of one MRG3 run (docs/lab/t2_realism_protocol.md).

Inputs per run directory: probes10.csv (10 s spatial mean speeds at 5 probe points) and features.csv (30 s loop data;
`down_q` = exit flow per lane). Outputs: sustained onset/recovery, mean-based capacity-drop ratio, per-lane discharge,
origin of congestion, internal wave speed (cross-correlation), share of stopped samples inside congestion.
"""
from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

V_CONG = 60.0 / 3.6
V_REC = 70.0 / 3.6
V_STOP = 10.0 / 3.6
DT = 10.0
PROBES = ("up3", "up2", "up1", "up0a", "up0b")              # upstream -> downstream
PAIRS = (("up1", "up2"), ("up0a", "up1"), ("up0b", "up0a"))  # (downstream, upstream), preference order
DOWNSTREAM_ORIGINS = ("up0b", "up0a")


def probe_x(net_file: Path, probes) -> dict:
    """x coordinate of each probe (straight lanes along x): lane-0 shape start + lane position."""
    shapes = {ln.get("id"): ln.get("shape") for ln in ET.parse(net_file).getroot().iter("lane")}
    return {e: float(shapes[f"{e}_0"].split()[0].split(",")[0]) + pos for e, pos in probes}


def load_probes(run_dir: Path) -> tuple:
    with open(run_dir / "probes10.csv") as fh:
        rd = csv.reader(fh)
        hdr = next(rd)
        rows = list(rd)
    t = np.array([float(r[0]) for r in rows])
    names = [h.split("@")[0] for h in hdr[1:]]
    v = {n: np.array([float(r[i + 1]) if r[i + 1] != "" else np.nan for r in rows]) for i, n in enumerate(names)}
    return t, v


def load_exit_flow(run_dir: Path) -> tuple:
    with open(run_dir / "features.csv") as fh:
        rows = list(csv.DictReader(fh))
    return np.array([float(r["t"]) for r in rows]), np.array([float(r["down_q"]) for r in rows])


def _fwd(x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        w = x[i:i + n]
        if len(w) == n and np.isfinite(w).any():
            out[i] = np.nanmean(w)
    return out


def _cen(x: np.ndarray, n: int) -> np.ndarray:
    h = n // 2
    out = np.full(len(x), np.nan)
    for i in range(len(x)):
        w = x[max(0, i - h):i + h + 1]
        if np.isfinite(w).any():
            out[i] = np.nanmean(w)
    return out


def _longest(mask: np.ndarray):
    best, start = None, None
    for i, m in enumerate(list(mask) + [False]):
        if m and start is None:
            start = i
        elif not m and start is not None:
            if best is None or i - start > best[1] - best[0]:
                best = (start, i)
            start = None
    return best


def onset_recovery(t: np.ndarray, v_up0b: np.ndarray) -> tuple:
    f2, f5 = _fwd(v_up0b, 12), _fwd(v_up0b, 30)
    tb = None
    for i in range(len(t)):
        if 600.0 <= t[i] <= 3600.0 and f2[i] < V_CONG and f5[i] < V_CONG:
            tb = i
            break
    if tb is None:
        return None, None
    rec = next((j for j in range(tb + 1, len(t)) if f5[j] > V_REC), None)
    return float(t[tb]), (float(t[rec]) if rec is not None else None)


PLATEAU_EXIT = (1400.0, 3000.0)   # demand plateau as seen at the exit loops (Addendum A)


def _mean_in(tq: np.ndarray, q: np.ndarray, a: float, b: float):
    v = q[(tq > a) & (tq <= b)]
    return float(np.mean(v)) if len(v) else None


def capacity_ratio(tq: np.ndarray, q: np.ndarray, t_b: float, t_rec, t_end: float = 3900.0) -> dict:
    """Discharge flow after a sustained onset; the original (10 min, pre-registered) and the ramp-corrected within-run
    ratios are reported only (Addendum A: the gated R-a ratio is between runs, see plateau_flow)."""
    d0 = t_b + 300.0
    d1 = min(t_b + 1200.0, t_rec if t_rec is not None else np.inf, t_end)
    dis = _mean_in(tq, q, d0, d1) if d1 - d0 >= 300.0 else None
    pre10 = _mean_in(tq, q, t_b - 600.0, t_b)
    pre5 = _mean_in(tq, q, t_b - 300.0, t_b) if t_b - 300.0 >= PLATEAU_EXIT[0] else None
    return {"discharge_vphpl": dis, "window_s": max(0.0, d1 - d0),
            "ratio_original_10min": dis / pre10 if dis and pre10 else None,
            "ratio_within_ramp_corrected": dis / pre5 if dis and pre5 else None}


def plateau_flow(tq: np.ndarray, q: np.ndarray):
    return _mean_in(tq, q, *PLATEAU_EXIT)


def origin(t: np.ndarray, v: dict) -> str | None:
    first = {}
    for n in PROBES:
        if n not in v:
            continue
        f2 = _fwd(v[n], 12)
        idx = np.nonzero(f2 < V_CONG)[0]
        if len(idx):
            first[n] = float(t[idx[0]])
    if not first:
        return None
    tmin = min(first.values())
    return [n for n in reversed(PROBES) if first.get(n) == tmin][0]    # ties -> most downstream


def wave_speed(v: dict, xs: dict) -> dict | None:
    for d, u in PAIRS:
        a, b = v[d], v[u]
        ca, cb = _cen(a, 31), _cen(b, 31)
        seg = _longest((ca < V_CONG) & (cb < V_CONG))
        if seg is None or seg[1] - seg[0] < 90:
            continue
        i0, i1 = seg
        ha = np.nan_to_num((a - ca)[i0:i1])
        hb = np.nan_to_num((b - cb)[i0:i1])
        k_max = min(60, (i1 - i0) - 60)
        rs = []
        for k in range(0, k_max + 1):
            x, y = ha[:len(ha) - k], hb[k:]
            rs.append(float(np.corrcoef(x, y)[0, 1]) if x.std() > 1e-9 and y.std() > 1e-9 else np.nan)
        if not np.isfinite(rs).any():
            return {"pair": f"{d}->{u}", "valid": False, "reason": "flat"}
        k = int(np.nanargmax(rs))
        r = rs[k]
        dx = xs[d] - xs[u]
        valid = r >= 0.3 and 1 <= k <= k_max - 1
        return {"pair": f"{d}->{u}", "seg_s": (i1 - i0) * DT, "lag_s": k * DT, "r": round(r, 3), "dx_m": round(dx, 1),
                "valid": bool(valid), "c_kmh": round(-dx / (k * DT) * 3.6, 2) if valid else None}
    return None


def stopped_share(v: dict) -> tuple:
    n_cong, n_stop = 0, 0
    for n in PROBES:
        if n not in v:
            continue
        c = _cen(v[n], 31)
        m = (c < V_CONG) & np.isfinite(v[n])
        n_cong += int(m.sum())
        n_stop += int((m & (v[n] < V_STOP)).sum())
    return n_cong, n_stop


def run_signatures(run_dir: Path, xs: dict) -> dict:
    t, v = load_probes(run_dir)
    tq, q = load_exit_flow(run_dir)
    t_b, t_rec = onset_recovery(t, v["up0b"])
    out = {"t_b": t_b, "t_rec": t_rec, "origin": origin(t, v), "wave": wave_speed(v, xs)}
    out["cap"] = capacity_ratio(tq, q, t_b, t_rec) if t_b is not None else None
    out["plateau_vphpl"] = plateau_flow(tq, q)
    out["n_cong_samples"], out["n_stop_samples"] = stopped_share(v)
    return out


def sustained_onset(run_dir: Path):
    t, v = load_probes(run_dir)
    return onset_recovery(t, v["up0b"])[0]
