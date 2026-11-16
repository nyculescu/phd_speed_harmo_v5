"""Screen #1 (docs/research/protocols/screen_1.md): online leader-braking margin on NGSIM.

Every constant comes from the screen text; nothing here is tuned on NGSIM outcomes.
Interpretations fixed before data (logged in the result):
- a "leader" window is one whose vehicle is someone's `Preceding` at the window's start frame;
- quantiles use numpy's default (linear) method;
- the placebo processes its shuffled windows sequentially, each outcome known before the next window.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass

import numpy as np
import pandas as pd

FT = 0.3048
DT_MS = 100                      # NGSIM frame step
HIST, WIN, LOOK = 50, 80, 20     # samples: 5 s history, 8 s window, 2 s look-ahead (10 Hz)
CLIP = 10.0                      # m/s², score clip
ALPHA, DELTA = 0.05, 0.025
ETA, Q_FLOOR = 0.5, 1.0
RHO, A_ACC, B_MIN, S0 = 0.5, 2.0, 4.0, 2.0
MIN_WINDOWS, MAX_CLIP_SHARE = 300, 0.05
E_MIN, B_BOOT, BLOCK_MS = 0.03, 2000, 120_000
SEED = 7_420_001
SITES = ("i-80", "us-101")
GATED = ("R1", "R2")


# ---------------------------------------------------------------- safe gap
def d_safe(b_hat, v, dt=0.01):
    """Largest closing distance (m): ego reacts RHO s at +A_ACC then brakes at B_MIN to a stop;
    leader brakes at b_hat to a stop; both start at speed v. Exact on a dt grid (valid for any b_hat > 0)."""
    b_hat = np.atleast_1d(np.asarray(b_hat, float))
    v = np.broadcast_to(np.asarray(v, float), b_hat.shape)
    t_end = RHO + (v + RHO * A_ACC) / B_MIN
    t_end = np.maximum(t_end, v / b_hat)
    n = int(np.ceil(t_end.max() / dt)) + 2
    t = np.arange(n) * dt
    out = np.empty(b_hat.shape)
    for s in range(0, b_hat.size, 4096):
        bh, vv = b_hat[s:s + 4096, None], v[s:s + 4096, None]
        # ego
        v1 = vv + A_ACC * RHO
        x1 = vv * RHO + 0.5 * A_ACC * RHO ** 2
        tb = np.clip(t - RHO, 0.0, v1 / B_MIN)
        xe = np.where(t <= RHO, vv * t + 0.5 * A_ACC * t ** 2, x1 + v1 * tb - 0.5 * B_MIN * tb ** 2)
        # leader
        tl = np.minimum(t, vv / bh)
        xl = vv * tl - 0.5 * bh * tl ** 2
        out[s:s + 4096] = np.maximum((xe - xl).max(axis=1), 0.0)
    return out


def rss_lemma2(b_hat, v):
    """Shalev-Shwartz et al. (arXiv 1708.06374) Lemma 2 with equal speeds; valid for b_hat >= B_MIN."""
    return np.maximum(v * RHO + 0.5 * A_ACC * RHO ** 2 + (v + RHO * A_ACC) ** 2 / (2 * B_MIN) - v ** 2 / (2 * b_hat), 0.0)


def req_gap(b_hat, v):
    return d_safe(b_hat, v) + S0


# ---------------------------------------------------------------- tracker
def track(starts_ms, scores, q0, delay_ms=(WIN + LOOK) * DT_MS):
    """Online quantile tracker with delayed feedback. Window k uses q at its start; its outcome is
    applied at start + delay. Events in time order; outcomes due at time t are applied before
    thresholds are assigned at t. Returns q_used per window (input order)."""
    order = np.argsort(starts_ms, kind="stable")
    st, sc = np.asarray(starts_ms)[order], np.asarray(scores)[order]
    q, used, j = float(q0), np.empty(len(st)), 0
    for k in range(len(st)):
        while j < k and st[j] + delay_ms <= st[k]:
            q = max(Q_FLOOR, q + ETA * ((sc[j] > used[j]) - ALPHA))
            j += 1
        used[k] = q
    out = np.empty(len(st))
    out[order] = used
    return out


def track_sequential(scores, q0):
    q, used = float(q0), np.empty(len(scores))
    for k, s in enumerate(scores):
        used[k] = q
        q = max(Q_FLOOR, q + ETA * ((s > q) - ALPHA))
    return used


# ---------------------------------------------------------------- data
def load(path):
    cols = ["Vehicle_ID", "Global_Time", "v_Vel", "Preceding", "Location", "Frame_ID"]
    df = pd.read_csv(path, usecols=cols)
    df = df[df.Location.isin(SITES)]
    n0 = len(df)
    df = df.drop_duplicates()
    n_exact = n0 - len(df)
    key = ["Location", "Vehicle_ID", "Global_Time"]
    n_keydup = int(df.duplicated(key).sum())
    df = df.drop_duplicates(key).sort_values(key, kind="stable").reset_index(drop=True)
    return df, {"rows_sites": n0, "exact_dups": n_exact, "key_dups_dropped": n_keydup}


def windows(df):
    """One row per 8-s window: site, start_ms, regime, score s, leader speed at start, clipped flag."""
    lead = set(zip(df.Location, df.Global_Time, df.Preceding))
    recs = []
    for (loc, vid), g in df.groupby(["Location", "Vehicle_ID"], sort=False):
        tms = g.Global_Time.to_numpy()
        v_raw = g.v_Vel.to_numpy(float) * FT
        cut = np.flatnonzero(np.diff(tms) > 200) + 1
        for a, b in zip(np.r_[0, cut], np.r_[cut, len(tms)]):
            tt, vr = tms[a:b], v_raw[a:b]
            if len(tt) < HIST + WIN + LOOK:
                continue
            vs = pd.Series(vr).rolling(11, center=True, min_periods=11).mean().to_numpy()
            for s0 in range(HIST, len(tt) - WIN - LOOK + 1, WIN):
                if (loc, tt[s0], vid) not in lead:
                    continue
                seg = vs[s0:s0 + WIN + LOOK]
                if np.isnan(seg).any():
                    continue
                d1 = (seg[:WIN] - seg[10:WIN + 10]) / 1.0
                d2 = (seg[:WIN] - seg[20:WIN + 20]) / 2.0
                raw = max(d1.max(), d2.max())
                hist = vr[s0 - HIST:s0]
                reg = "R1" if hist.min() < 2.0 else ("R2" if hist.mean() < 10.0 else "R3")
                recs.append((loc, int(tt[s0]), reg, float(np.clip(raw, 0, CLIP)), bool(raw >= CLIP), float(vs[s0])))
    return pd.DataFrame(recs, columns=["site", "start_ms", "regime", "s", "clipped", "v0"])


# ---------------------------------------------------------------- evaluation
def evaluate(W):
    rng = np.random.default_rng(SEED)
    res = {"cells": []}
    F = {site: W[W.site == site].groupby("regime").s.quantile(1 - ALPHA).to_dict() for site in SITES}
    for fit, ev in ((SITES[0], SITES[1]), (SITES[1], SITES[0])):
        E = W[W.site == ev]
        for reg in ("R1", "R2", "R3"):
            c = E[E.regime == reg].sort_values("start_ms", kind="stable")
            cell = {"fit": fit, "eval": ev, "regime": reg, "n": int(len(c))}
            if reg not in F[fit] or len(c) == 0:
                res["cells"].append(cell | {"status": "empty"}); continue
            s, v, st = c.s.to_numpy(), c.v0.to_numpy(), c.start_ms.to_numpy()
            qF = np.full(len(c), F[fit][reg])
            qO = track(st, s, F[fit][reg])
            qH = np.full(len(c), np.quantile(s, 1 - ALPHA))
            perm = rng.permutation(len(c))
            qP = np.empty(len(c)); qP[perm] = track_sequential(s[perm], F[fit][reg])
            d = {k: req_gap(q, v) for k, q in (("F", qF), ("O", qO), ("H", qH), ("P", qP))}
            miss = {k: float((s > q).mean()) for k, q in (("F", qF), ("O", qO), ("H", qH), ("P", qP))}
            blocks = st // BLOCK_MS
            ub, inv = np.unique(blocks, return_inverse=True)
            sums = {k: np.bincount(inv, d[k], len(ub)) for k in d}
            cnt = np.bincount(inv, minlength=len(ub)).astype(float)
            def ratio(a, b, idx=None):
                if idx is None:
                    return 1 - sums[a].sum() / sums[b].sum()
                return 1 - sums[a][idx].sum() / sums[b][idx].sum()
            boot = np.array([ratio("O", "F", rng.integers(0, len(ub), len(ub))) for _ in range(B_BOOT)])
            lo, hi = np.percentile(boot, [2.5, 97.5])
            clip_share = float(c.clipped.mean())
            gated = reg in GATED and len(c) >= MIN_WINDOWS and clip_share <= MAX_CLIP_SHARE
            validO, validF = miss["O"] <= ALPHA + DELTA, miss["F"] <= ALPHA + DELTA
            Eo = ratio("O", "F")
            win = gated and validO and ((not validF) or (Eo >= E_MIN and lo > 0))
            cell |= {"status": "gated" if gated else "report-only", "n_blocks": int(len(ub)),
                     "clip_share": clip_share, "miss": miss, "qF": float(F[fit][reg]), "qH": float(qH[0]),
                     "qO_median": float(np.median(qO)),
                     "mean_gap_m": {k: float(d[k].mean()) for k in d},
                     "E_O_vs_F": float(Eo), "E_CI95": [float(lo), float(hi)],
                     "E_H_vs_F": float(ratio("H", "F")), "E_P_vs_F": float(ratio("P", "F")),
                     "validO": bool(validO), "validF": bool(validF), "WIN": bool(win)}
            res["cells"].append(cell)
    g = [c for c in res["cells"] if c.get("status") == "gated"]
    res["outcome"] = "STOP (data)" if not g else ("CONTINUE" if any(c["WIN"] for c in g) else "STOP")
    return res


def main(path, out):
    df, info = load(path)
    W = windows(df)
    res = evaluate(W)
    res["data"] = info | {"windows": W.groupby(["site", "regime"]).size().to_dict().__repr__()}
    with open(out, "w") as f:
        json.dump(res, f, indent=1, default=str)
    print(res["outcome"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
