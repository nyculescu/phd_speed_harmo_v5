"""Confirmatory protocol #1 (docs/research/protocols/confirmatory_1.md, V84).

Stage 1 uses window metadata only (times, regimes, units: no scores) and fixes c, the gated cells and J.
Stage 2 computes scores and decides the outcome. Interpretations fixed before data (logged in the result):
- direction = sign of lane_kf at the window's start step (the protocol's I-294 rule, applied to every set);
- a cell = dataset x regime, pooling its direction units; blocks = (run, 2-min) and may hold both directions;
- an outcome is known at max(start + 10.5 s, the step after the last raw sample the window's centred mean
  needs); the two agree unless the window spans short sample gaps (then the later time is the true one);
- W freezes when all of its first N windows' outcomes are known; comparison windows start strictly after;
- O's A1 is required on the comparison windows and on all windows of the cell;
- clip share and floor-bound share use all windows of the cell;
- test vehicles: a (run, id) with any acc/av row equal to "yes" (any case), or I-395 type_most_common = 4;
- d_safe's grid ends at the ego's stop time (constants table); values equal screen1.d_safe for b_hat > 0;
- L1 probe: the first 20,000 rows of the Socrata resource CSV (resource/7zjf-a4zf.csv?$limit=20000), the
  request that reproduces the recorded fitting-set probe MD5s; on an MD5 match a sensitivity row drops
  its (run, id) pairs from L1.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys

import numpy as np
import pandas as pd
from scipy import stats

from v5b import screen1 as s1
from v5b import screen1b as sb

ALPHA, LIMIT, ETA = 0.04, 0.075, 0.5
FLOOR = 1.0
NEED = s1.WIN + s1.LOOK + 5           # raw samples after the start needed by the last centred mean (+1)
DELAY = NEED                          # 105 steps = window end + 2.5 s when samples are gap-free
TICK, RUN_SPAN, BLOCK = 10, sb.RUN_SPAN, 1200
N_W, N_W_REPORT = 300, 1000
MIN_CMP, MIN_BLOCKS, MAX_CLIP = 1000, 10, 0.05
E_BEAT, HARM = 0.03, 0.05
B_BOOT, SEED_BOOT = 10_000, 7_420_200
SEEDS_P = list(range(7_420_201, 7_420_221))
C_PCT = 90
DEFF = 2.0
FIT = {"i90_94_stationary": "tgsim_9uas-hf8b.csv", "i395": "tgsim_97n2-kuqi.csv"}
CONF = {"i294_l1": "tgsim_7zjf-a4zf.csv", "i294_l2": "tgsim_tpsq-zrwa.csv", "i90_94_moving": "tgsim_6a6e-vfvi.csv"}
ROWS = {"i294_l1": 1_024_281, "i294_l2": 137_928, "i90_94_moving": 1_784_748}
REPORT_ONLY_SETS = {"i294_l2"}
NEW_ROAD = "i294_l1"
L1_PROBE_MD5 = "a9f2f0c1249446350e99aafe2bd07212"
L1_PROBE_FILE = "l1_probe.csv"
PROTOCOL = "docs/research/protocols/confirmatory_1.md"


# ---------------------------------------------------------------- basics
def d_safe(b_hat, v, dt=0.01):
    """screen1.d_safe with the grid ending at the ego's stop time: identical for b_hat > 0 (after the ego
    stops the gap only shrinks), finite at b_hat = 0, memory independent of b_hat."""
    b_hat = np.atleast_1d(np.asarray(b_hat, float))
    v = np.broadcast_to(np.asarray(v, float), b_hat.shape)
    out = np.empty(b_hat.shape)
    if b_hat.size == 0:
        return out
    n = int(np.ceil((s1.RHO + (v + s1.A_ACC * s1.RHO) / s1.B_MIN).max() / dt)) + 2
    t = np.arange(n) * dt
    for s in range(0, b_hat.size, 4096):
        bh, vv = b_hat[s:s + 4096, None], v[s:s + 4096, None]
        v1 = vv + s1.A_ACC * s1.RHO
        x1 = vv * s1.RHO + 0.5 * s1.A_ACC * s1.RHO ** 2
        tb = np.clip(t - s1.RHO, 0.0, v1 / s1.B_MIN)
        xe = np.where(t <= s1.RHO, vv * t + 0.5 * s1.A_ACC * t ** 2, x1 + v1 * tb - 0.5 * s1.B_MIN * tb ** 2)
        with np.errstate(divide="ignore"):
            tstop = np.where(bh > 0, vv / np.where(bh > 0, bh, 1.0), np.inf)
        tl = np.minimum(t, tstop)
        xl = vv * tl - 0.5 * bh * tl ** 2
        out[s:s + 4096] = np.maximum((xe - xl).max(axis=1), 0.0)
    return out


def req_gap(b_hat, v):
    return d_safe(b_hat, v) + s1.S0


def qstat(x, alpha=ALPHA):
    """Order-statistic quantile: the ceil((1 - alpha)(n + 1))-th smallest (capped at n)."""
    x = np.sort(np.asarray(x, float))
    if len(x) == 0:
        return float("nan")
    k = min(len(x), math.ceil((1 - alpha) * (len(x) + 1)))
    return float(x[k - 1])


def _known(gt, known):
    return np.asarray(gt) + DELAY if known is None else np.maximum(np.asarray(known), np.asarray(gt) + DELAY)


def track(gt, scores, q0, c, floor=FLOOR, known=None):
    """Batch-normalised tracker: q <- max(floor, q + ETA/c * sum(miss - ALPHA)) once per second over the
    outcomes that became known in that second. Returns q_used per window (input order)."""
    kn = _known(gt, known)
    order = np.argsort(gt, kind="stable")
    g, sc = np.asarray(gt)[order], np.asarray(scores, float)[order]
    tick_of = (kn[order] + TICK - 1) // TICK * TICK
    by_tick = np.argsort(tick_of, kind="stable")        # outcomes in the order they become known
    q, used, j, n = float(max(floor, q0)), np.full(len(g), np.nan), 0, len(g)
    for k in range(n):
        now = g[k] // TICK * TICK
        while j < n and tick_of[by_tick[j]] <= now:
            t0, acc = tick_of[by_tick[j]], 0.0
            while j < n and tick_of[by_tick[j]] == t0:
                i = by_tick[j]
                acc += (sc[i] > used[i]) - ALPHA      # known => its start is earlier, so used[i] is set
                j += 1
            q = max(floor, q + ETA / c * acc)
        used[k] = q
    out = np.empty(n); out[order] = used
    return out


def placebo(gt, scores, q0, c, seed, floor=FLOOR, known=None):
    """O's rule on O's timeline (same slots and known times), windows' scores fed in a random order.
    Returns, per original window, the threshold of the slot it landed in."""
    rng = np.random.default_rng(seed)
    n = len(gt)
    perm = rng.permutation(n)                       # slot i receives window perm[i]
    order = np.argsort(gt, kind="stable")           # slots in time order
    slot_scores = np.empty(n)
    slot_scores[order] = np.asarray(scores, float)[perm]
    q_slot = track(gt, slot_scores, q0, c, floor, known)
    q_win = np.empty(n)
    q_win[perm] = q_slot[order]
    return q_win


def freeze_time(gt, n_w=N_W, known=None):
    """Time at which all of the first n_w windows' outcomes are known (None if <= n_w windows)."""
    if len(gt) <= n_w:
        return None
    order = np.argsort(gt, kind="stable")
    return int(_known(gt, known)[order[:n_w]].max())


def w_arm(gt, scores, F, n_w=N_W, floor=FLOOR, known=None):
    """'Calibrate briefly, then freeze': returns (q per window, freeze time or None)."""
    fr = freeze_time(gt, n_w, known)
    if fr is None:
        return np.full(len(gt), max(floor, F)), None
    first = np.argsort(gt, kind="stable")[:n_w]
    qw = max(floor, qstat(np.asarray(scores)[first]))
    return np.where(np.asarray(gt) > fr, qw, max(floor, F)), fr


def comparison_mask(gt, n_w=N_W, known=None):
    """Windows starting after W froze (all windows if W = F). Uses times only (Stage 1 safe)."""
    fr = freeze_time(gt, n_w, known)
    return np.ones(len(gt), bool) if fr is None else np.asarray(gt) > fr


def c_per_regime(fit_windows):
    """90th percentile of outcomes per non-empty second, fitting units pooled, per regime (counts only)."""
    out = {}
    for r, g in fit_windows.groupby("regime"):
        counts = []
        for _, u in g.groupby(["dataset", "unit"]):
            ticks = (_known(u.gtime.to_numpy(), u.known.to_numpy()) + TICK - 1) // TICK
            counts.append(np.unique(ticks, return_counts=True)[1])
        allc = np.concatenate(counts) if counts else np.array([1])
        out[r] = float(np.percentile(allc, C_PCT))
    return out


# ---------------------------------------------------------------- data
def load(path, dataset):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    if "run_index" not in df:
        df["run_index"] = 0
    flag = np.zeros(len(df), bool)
    for col in ("acc", "av"):
        if col in df:
            flag |= df[col].astype(str).str.strip().str.lower().eq("yes").to_numpy()
    if dataset == "i395" and "type_most_common" in df:
        flag |= pd.to_numeric(df.type_most_common, errors="coerce").eq(4).to_numpy()
    df["test_row"] = flag
    df = df[["run_index", "id", "time", "xloc_kf", "yloc_kf", "lane_kf", "speed_kf", "test_row"]]
    n0 = len(df)
    df = df.drop_duplicates()
    df["step"] = np.rint(df.time.to_numpy() * 10).astype(np.int64)
    key = ["run_index", "id", "step"]
    n_keydup = int(df.duplicated(key).sum())
    df = df.drop_duplicates(key).sort_values(key, kind="stable").reset_index(drop=True)
    test_veh = set(map(tuple, df.loc[df.test_row, ["run_index", "id"]].drop_duplicates().to_numpy().tolist()))
    return df, {"rows": n0, "exact_dups": n0 - len(df) - n_keydup, "key_dups_dropped": n_keydup,
                "test_vehicles": len(test_veh), "nan_speed_rows": int(df.speed_kf.isna().sum())}, test_veh


def direction_consistency(df):
    """Report-only guard: per (run, lane), the share of tracks whose start->end displacement points along
    the lane's mean travel direction (a frame that moves with the camera would show low shares)."""
    g = df.groupby(["run_index", "lane_kf", "id"])[["xloc_kf", "yloc_kf"]].agg(["first", "last"])
    d = np.c_[g[("xloc_kf", "last")] - g[("xloc_kf", "first")], g[("yloc_kf", "last")] - g[("yloc_kf", "first")]]
    n = np.linalg.norm(d, axis=1, keepdims=True)
    u = np.where(n > 0, d / np.maximum(n, 1e-9), 0.0)
    t = pd.DataFrame(u, index=g.index, columns=["ux", "uy"]).reset_index()
    m = t.groupby(["run_index", "lane_kf"])[["ux", "uy"]].transform("sum")
    dot = t.ux * m.ux + t.uy * m.uy
    sh = (dot > 0).groupby([t.run_index, t.lane_kf]).mean()
    return {f"{int(r)}/{l:g}": float(v) for (r, l), v in sh.items()}


def window_meta(df, lead, test_veh, dataset):
    """Stage 1: window metadata (no scores) plus the smoothed speed segment kept for Stage 2."""
    is_leader = set(zip(df.run_index.to_numpy()[lead >= 0], df.step.to_numpy()[lead >= 0], lead[lead >= 0]))
    recs, segs = [], []
    for (run, vid), g in df.groupby(["run_index", "id"], sort=False):
        st = g.step.to_numpy(); v_raw = g.speed_kf.to_numpy(float); lane = g.lane_kf.to_numpy(float)
        cut = np.flatnonzero(np.diff(st) > 2) + 1
        for a, b in zip(np.r_[0, cut], np.r_[cut, len(st)]):
            tt, vr, ln = st[a:b], v_raw[a:b], lane[a:b]
            if len(tt) < s1.HIST + s1.WIN + s1.LOOK:
                continue
            vs = pd.Series(vr).rolling(11, center=True, min_periods=11).mean().to_numpy()
            for k in range(s1.HIST, len(tt) - s1.WIN - s1.LOOK + 1, s1.WIN):
                if (run, tt[k], vid) not in is_leader:
                    continue
                seg = vs[k:k + s1.WIN + s1.LOOK]
                if np.isnan(seg).any():
                    continue
                hist = vr[k - s1.HIST:k]
                reg = "R1" if hist.min() < 2.0 else ("R2" if hist.mean() < 10.0 else "R3")
                unit = -1 if (np.isfinite(ln[k]) and ln[k] < 0) else 1
                last = tt[k + s1.WIN + s1.LOOK - 1 + 5]  # exists: the centred mean there is not NaN
                g0 = int(run) * RUN_SPAN
                recs.append((dataset, int(run), int(vid), int(tt[k]), g0 + int(tt[k]), g0 + int(last) + 1, reg,
                             unit, (int(run), int(vid)) in test_veh, float(vs[k])))
                segs.append(seg.astype(np.float64))
    W = pd.DataFrame(recs, columns=["dataset", "run", "id", "step", "gtime", "known", "regime", "unit", "test", "v0"])
    return W, (np.stack(segs) if segs else np.zeros((0, s1.WIN + s1.LOOK)))


def scores(segs):
    """Stage 2: screen score and clip flag from the stored segments."""
    segs = np.asarray(segs, float)
    if len(segs) == 0:
        return np.zeros(0), np.zeros(0, bool)
    d1 = (segs[:, :s1.WIN] - segs[:, 10:s1.WIN + 10]).max(axis=1)
    d2 = ((segs[:, :s1.WIN] - segs[:, 20:s1.WIN + 20]) / 2.0).max(axis=1)
    raw = np.maximum(d1, d2)
    return np.clip(raw, 0, s1.CLIP), raw >= s1.CLIP


def time_order(W):
    """Protocol order: run, start, vehicle id."""
    return np.lexsort((W.id.to_numpy(), W.step.to_numpy(), W.run.to_numpy()))


# ---------------------------------------------------------------- statistics
def tmult(G, level_two_sided=None, one_sided=None):
    if one_sided is not None:
        return stats.t.ppf(one_sided, G - 1) * math.sqrt(G / (G - 1))
    return stats.t.ppf(1 - (1 - level_two_sided) / 2, G - 1) * math.sqrt(G / (G - 1))


def boot_idx(G, seed=SEED_BOOT, B=None):
    return np.random.default_rng(seed).integers(0, G, size=(B_BOOT if B is None else B, G))


def block_sums(blocks, *cols):
    ub, inv = np.unique(blocks, return_inverse=True)
    return [np.bincount(inv, np.asarray(c, float), len(ub)) for c in cols]


def miss_bounds(miss, blocks, J, idx=None, cp=True):
    """A1 upper bound (one-sided 95 %: max of t-scaled block bootstrap and Clopper-Pearson) and the two
    lower ends used for 'clearly invalid' (two-sided 1 - 0.05/J). cp=False (placebo): bootstrap only."""
    miss = np.asarray(miss, float)
    n = len(miss); k = miss.sum(); p = k / n
    sm, sn = block_sums(blocks, miss, np.ones(n))
    G = len(sm)
    if idx is None or idx.shape[1] != G:
        idx = boot_idx(G)
    bs = sm[idx].sum(1) / sn[idx].sum(1)
    sd = bs.std(ddof=1)
    ub_boot = p + tmult(G, one_sided=0.95) * sd
    lvl = 1 - 0.05 / max(J, 1)
    lo_boot = p - tmult(G, level_two_sided=lvl) * sd
    out = {"p": float(p), "n": int(n), "G": int(G), "ub_boot": float(ub_boot), "lo_boot": float(lo_boot),
           "pct95": [float(x) for x in np.percentile(bs, [2.5, 97.5])]}
    if not cp:
        return out | {"ub": float(ub_boot), "ub_cp": None, "lo_cp": None}
    ki = int(round(k))
    ub_cp = stats.beta.ppf(0.95, ki + 1, n - ki) if ki < n else 1.0
    lo_cp = stats.beta.ppf((1 - lvl) / 2, ki, n - ki + 1) if ki > 0 else 0.0
    return out | {"ub": float(max(ub_boot, ub_cp)), "ub_cp": float(ub_cp), "lo_cp": float(lo_cp)}


def a1_valid(b):
    return b["ub"] <= LIMIT


def clearly_invalid(b):
    return b["lo_boot"] > LIMIT and b["lo_cp"] is not None and b["lo_cp"] > LIMIT


def efficiency(dX, dY, blocks, J, idx=None):
    """E(X, Y) = 1 - mean(dX)/mean(dY), paired; t-scaled block bootstrap CIs."""
    sx, sy = block_sums(blocks, dX, dY)
    G = len(sx)
    if idx is None or idx.shape[1] != G:
        idx = boot_idx(G)
    E = 1 - sx.sum() / sy.sum()
    bs = 1 - sx[idx].sum(1) / sy[idx].sum(1)
    sd = bs.std(ddof=1)
    mB = tmult(G, level_two_sided=1 - 0.05 / max(J, 1))
    m95 = tmult(G, level_two_sided=0.95)
    return {"E": float(E), "ciB": [float(E - mB * sd), float(E + mB * sd)],
            "ci95": [float(E - m95 * sd), float(E + m95 * sd)], "pct95": [float(x) for x in np.percentile(bs, [2.5, 97.5])]}


def beats(e):
    return e["E"] >= E_BEAT and e["ciB"][0] > 0


def power_a1(n, G, p=ALPHA, deff=DEFF):
    """§5: probability that a threshold exactly at its target quantile passes A1 (normal approximation
    with design effect, t-scaled bootstrap bound and Clopper-Pearson)."""
    if n < 2 or G < 2:
        return 0.0
    sd = math.sqrt(deff * p * (1 - p) / n)
    ks = np.arange(0, min(n, int(n * 0.3) + 1))
    w = stats.norm.cdf((ks + 0.5) / n, p, sd) - stats.norm.cdf((ks - 0.5) / n, p, sd)
    ph = ks / n
    cp = stats.beta.ppf(0.95, ks + 1, n - ks)
    bs = ph + tmult(G, one_sided=0.95) * np.sqrt(deff * ph * (1 - ph) / n)
    return float((w * (np.maximum(cp, bs) <= LIMIT)).sum())


def max_run(b):
    best = cur = 0
    for x in np.asarray(b, bool):
        cur = cur + 1 if x else 0
        best = max(best, cur)
    return best


# ---------------------------------------------------------------- stage 1
def stage1(Wc, fitW, rows_seen):
    """Counts only. Returns the gating decision, J, c and the power figure; never looks at scores."""
    out = {"rows": rows_seen, "rows_expected": ROWS}
    out["rows_ok"] = all(rows_seen.get(k) == v for k, v in ROWS.items())
    out["c"] = c_per_regime(fitW)
    cells = []
    for (ds, reg), g in Wc.groupby(["dataset", "regime"]):
        n_test = int(g.test.sum())
        g = g[~g.test]
        cm = np.zeros(len(g), bool)
        for _, u in g.groupby("unit"):
            cm[g.index.get_indexer(u.index)] = comparison_mask(u.gtime.to_numpy(), N_W, u.known.to_numpy())
        blocks = (g.run.to_numpy() * 10**6 + g.step.to_numpy() // BLOCK)[cm]
        n_cmp, n_blk = int(cm.sum()), int(len(np.unique(blocks)))
        gated = reg in ("R1", "R2") and ds not in REPORT_ONLY_SETS and n_cmp >= MIN_CMP and n_blk >= MIN_BLOCKS
        cells.append({"dataset": ds, "regime": reg, "n_all": int(len(g)), "n_cmp": n_cmp, "blocks_cmp": n_blk,
                      "test_windows_excluded": n_test, "gated": bool(gated),
                      "power_a1": power_a1(n_cmp, n_blk) if n_blk >= 2 else 0.0})
    out["cells"] = cells
    out["J"] = sum(c["gated"] for c in cells)
    out["power_all_gated"] = float(np.prod([c["power_a1"] for c in cells if c["gated"]])) if out["J"] else 0.0
    out["stop_data"] = (not out["rows_ok"]) or out["J"] == 0
    return out


# ---------------------------------------------------------------- stage 2
def arms_for_unit(u, F, c, floor):
    gt, s, kn = u.gtime.to_numpy(), u.s.to_numpy(), u.known.to_numpy()
    qO = track(gt, s, F, c, floor, kn)
    qW, _ = w_arm(gt, s, F, N_W, floor, kn)
    qW1k, _ = w_arm(gt, s, F, N_W_REPORT, floor, kn)
    qP = np.stack([placebo(gt, s, F, c, sd, floor, kn) for sd in SEEDS_P])
    return qO, qW, qW1k, qP


def stage2(Wc, fitW, st1, include_test=False, floor=FLOOR):
    """Scores are already in Wc.s / fitW.s here. Returns per-cell results and the outcome."""
    J = st1["J"]; c = st1["c"]
    fw = fitW if include_test else fitW[~fitW.test]
    F = {r: max(floor, qstat(g.s)) for r, g in fw.groupby("regime")}
    F_single = {ds: {r: max(floor, qstat(g.s)) for r, g in x.groupby("regime")} for ds, x in fw.groupby("dataset")}
    gated = {(x["dataset"], x["regime"]) for x in st1["cells"] if x["gated"]}
    W = Wc if include_test else Wc[~Wc.test]
    res = {"F": F, "F_single_site": F_single, "cells": []}
    for (ds, reg), g in W.groupby(["dataset", "regime"]):
        g = g.iloc[time_order(g)].copy()
        n = len(g)
        A = {k: np.full(n, np.nan) for k in ("qO", "qW", "qW1k")}
        M = {k: np.zeros(n, bool) for k in ("cmp", "cmp1k")}
        qP_all = np.full((len(SEEDS_P), n), np.nan)
        pos = {ix: i for i, ix in enumerate(g.index)}
        Fr = F.get(reg, floor)
        for _, u in g.groupby("unit"):
            qO, qW, qW1k, qP = arms_for_unit(u, Fr, c.get(reg, 1.0), floor)
            ii = np.array([pos[ix] for ix in u.index])
            A["qO"][ii], A["qW"][ii], A["qW1k"][ii] = qO, qW, qW1k
            M["cmp"][ii] = comparison_mask(u.gtime.to_numpy(), N_W, u.known.to_numpy())
            M["cmp1k"][ii] = comparison_mask(u.gtime.to_numpy(), N_W_REPORT, u.known.to_numpy())
            qP_all[:, ii] = qP
        for k, x in (A | M).items():
            g[k] = x
        assert not np.isnan(A["qO"]).any()
        cmp = M["cmp"]
        gc = g[cmp]
        s, v = gc.s.to_numpy(), gc.v0.to_numpy()
        blocks = gc.run.to_numpy() * 10**6 + gc.step.to_numpy() // BLOCK
        cell = {"dataset": ds, "regime": reg, "gated": (ds, reg) in gated, "n_all": n, "n_cmp": int(cmp.sum()),
                "clip_share": float(g.clipped.mean())}
        if cmp.sum() < 2 or len(np.unique(blocks)) < 2:
            res["cells"].append(cell | {"status": "too few"}); continue
        idx = boot_idx(len(np.unique(blocks)))
        qH = max(floor, qstat(s))
        q = {"F": np.full(len(gc), Fr), "W": gc.qW.to_numpy(), "O": gc.qO.to_numpy(), "H": np.full(len(gc), qH)}
        d = {k: req_gap(x, v) for k, x in q.items()}
        miss = {k: (s > x).astype(float) for k, x in q.items()}
        qPc = qP_all[:, cmp]
        miss["P"] = (s[None, :] > qPc).mean(0)
        d["P"] = np.mean([req_gap(qPc[i], v) for i in range(len(SEEDS_P))], axis=0)
        bounds = {k: miss_bounds(miss[k], blocks, J, idx, cp=(k != "P")) for k in miss}
        ball = g.run.to_numpy() * 10**6 + g.step.to_numpy() // BLOCK
        bounds["O_all"] = miss_bounds((g.s.to_numpy() > g.qO.to_numpy()).astype(float), ball, J)
        E = {f"O_vs_{k}": efficiency(d["O"], d[k], blocks, J, idx) for k in ("F", "W", "P")}
        E |= {"H_vs_F": efficiency(d["H"], d["F"], blocks, J, idx), "H_vs_W": efficiency(d["H"], d["W"], blocks, J, idx)}
        validO = a1_valid(bounds["O"]) and a1_valid(bounds["O_all"])
        invO = clearly_invalid(bounds["O"]) or clearly_invalid(bounds["O_all"])
        win = validO and all(clearly_invalid(bounds[x]) or beats(E[f"O_vs_{x}"]) for x in ("F", "W"))
        valid_opp = [x for x in ("F", "W") if a1_valid(bounds[x])]
        worse, harm_ne = False, False
        if valid_opp:
            opp = min(valid_opp, key=lambda x: d[x].mean())
            ci = E[f"O_vs_{opp}"]["ci95"]
            worse = ci[1] < -HARM
            harm_ne = (not worse) and ci[0] < -HARM
        share = None
        if a1_valid(bounds["F"]) and E["H_vs_F"]["E"] >= E_BEAT:
            share = E["O_vs_F"]["E"] / E["H_vs_F"]["E"]
        # report-only: W with N = 1,000, judged on the windows after its own freeze
        w1k = None
        m1k = M["cmp1k"]
        if m1k.sum() > 1:
            g1 = g[m1k]
            b1k = g1.run.to_numpy() * 10**6 + g1.step.to_numpy() // BLOCK
            if len(np.unique(b1k)) > 1:
                s1k, v1k = g1.s.to_numpy(), g1.v0.to_numpy()
                w1k = {"n": int(m1k.sum()),
                       "bounds_W1000": miss_bounds((s1k > g1.qW1k.to_numpy()).astype(float), b1k, J),
                       "bounds_O": miss_bounds((s1k > g1.qO.to_numpy()).astype(float), b1k, J),
                       "E_O_vs_W1000": efficiency(req_gap(g1.qO.to_numpy(), v1k), req_gap(g1.qW1k.to_numpy(), v1k), b1k, J)}
        runs = {k: int(max_run(miss[k] > 0.5)) for k in ("F", "W", "O", "H")}  # gc is in time order
        cell |= {"status": "gated" if cell["gated"] else "report-only", "q": {"F": Fr, "H": qH,
                 "O_median": float(np.median(q["O"])), "W_frozen": float(np.median(q["W"]))},
                 "floor_bound": bool(np.mean(g.qO.to_numpy() <= floor + 1e-12) > 0.5),
                 "mean_gap": {k: float(np.mean(x)) for k, x in d.items()}, "bounds": bounds, "E": E,
                 "headroom_share_O_of_H_vs_F": share,
                 "validO": bool(validO), "clearly_invalidO": bool(invO), "win": bool(win),
                 "beats_P": bool(beats(E["O_vs_P"])), "clearly_worse": bool(worse), "harm_not_excluded": bool(harm_ne),
                 "W1000_report": w1k, "longest_miss_run": runs}
        res["cells"].append(cell)
    res["outcome"] = decide(res["cells"], st1)
    return res


def decide(cells, st1):
    """Outcome table (§6), first match wins."""
    if st1["stop_data"]:
        return {"outcome": "STOP-data"}
    name = lambda c: f'{c["dataset"]}/{c["regime"]}'
    g = [c for c in cells if c.get("gated") and c.get("status") == "gated"]
    eligible = [c for c in g if c["clip_share"] <= MAX_CLIP]
    lists = {"harm_not_excluded": [name(c) for c in eligible if c.get("harm_not_excluded")],
             "floor_bound": [name(c) for c in eligible if c.get("floor_bound")],
             "report_only": [name(c) for c in cells if c not in eligible]}
    if any(c["clearly_invalidO"] for c in eligible):
        return {"outcome": "KILL"} | lists
    if not eligible or not all(c["validO"] for c in eligible):
        return {"outcome": "INCONCLUSIVE"} | lists
    wins = [c for c in eligible if c["win"]]
    if not wins or any(c["clearly_worse"] for c in eligible):
        return {"outcome": "VALID-ONLY", "clearly_worse": [name(c) for c in eligible if c["clearly_worse"]]} | lists
    beats_list = [c["E"][f"O_vs_{x}"] for c in wins for x in ("F", "W") if beats(c["E"][f"O_vs_{x}"])]
    x = min(beats_list, key=lambda e: e["E"]) if beats_list else None
    kind = "PASS, new road" if any(c["dataset"] == NEW_ROAD for c in wins) else "PASS, same road"
    return {"outcome": kind, "x": x, "wins": [name(c) for c in wins],
            "secondary_tracking": any(c["beats_P"] for c in eligible)} | lists


# ---------------------------------------------------------------- run
def build(data_dir, sets):
    Ws, segs, info = [], [], {}
    for ds, fn in sets.items():
        df, inf, tv = load(f"{data_dir}/{fn}", ds)
        lead = sb.leaders(df)
        W, sg = window_meta(df, lead, tv, ds)
        Ws.append(W); segs.append(sg)
        info[ds] = inf | {"matched_leader_share": float((lead >= 0).mean()), "windows": int(len(W)),
                          "test_windows": int(W.test.sum()),
                          "windows_known_later_than_10_5_s": int((W.known > W.gtime + DELAY).sum()),
                          "direction_consistency": direction_consistency(df)}
    W = pd.concat(Ws, ignore_index=True)
    S = np.concatenate(segs) if segs else np.zeros((0, s1.WIN + s1.LOOK))
    o = np.lexsort((W.id.to_numpy(), W.step.to_numpy(), W.run.to_numpy(), W.dataset.to_numpy()))
    return W.iloc[o].reset_index(drop=True), S[o], info


def l1_probe(path):
    """MD5 of the re-fetched probe and its (run_index, id) pairs (used only on a match)."""
    try:
        raw = open(path, "rb").read()
    except OSError as e:
        return {"available": False, "error": str(e)}, set()
    md5 = hashlib.md5(raw).hexdigest()
    p = pd.read_csv(path)
    p.columns = [c.strip().lower() for c in p.columns]
    pairs = set(zip(pd.to_numeric(p.run_index).astype(int), pd.to_numeric(p.id).astype(int)))
    return {"available": True, "md5": md5, "match": md5 == L1_PROBE_MD5, "rows": int(len(p)), "pairs": len(pairs)}, pairs


def records(data_dir):
    sha = hashlib.sha256(open(PROTOCOL, "rb").read()).hexdigest()
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    except OSError:
        commit = None
    md5 = {}
    for fn in list(FIT.values()) + list(CONF.values()):
        h = hashlib.md5()
        with open(f"{data_dir}/{fn}", "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        md5[fn] = h.hexdigest()
    return {"protocol_sha256": sha, "commit": commit, "csv_md5": md5,
            "seeds": {"bootstrap": SEED_BOOT, "placebo": SEEDS_P}, "B": B_BOOT}


def main(data_dir, out_dir):
    rec = records(data_dir)
    fitW, fitS, fit_info = build(data_dir, FIT)
    Wc, segC, conf_info = build(data_dir, CONF)
    st1 = stage1(Wc, fitW[~fitW.test], {k: conf_info[k]["rows"] for k in CONF})
    st1["data"] = {"fit": fit_info, "conf": conf_info}
    probe_info, probe_pairs = l1_probe(f"{data_dir}/{L1_PROBE_FILE}")
    st1["l1_probe"] = probe_info
    st1["records"] = rec
    with open(f"{out_dir}/stage1.json", "w") as f:
        json.dump(st1, f, indent=1, default=str)
    res = {"interpretations": __doc__, "records": rec, "stage1": st1}

    def write():
        with open(f"{out_dir}/result.json", "w") as f:
            json.dump(res, f, indent=1, default=str)

    if st1["stop_data"]:
        res["main"] = {"outcome": {"outcome": "STOP-data"}}
        write(); print("STOP-data"); return
    fitW["s"], fitW["clipped"] = scores(fitS)
    Wc["s"], Wc["clipped"] = scores(segC)
    res["main"] = stage2(Wc, fitW, st1)
    write()                                   # the decisive result is on disk before any report row
    print(res["main"]["outcome"]["outcome"], flush=True)
    rows = {"sensitivity_test_vehicles_scored": lambda: stage2(Wc, fitW, st1, include_test=True),
            "report_floor0": lambda: stage2(Wc, fitW, st1, floor=0.0)}
    if probe_info.get("match"):
        keep = ~((Wc.dataset == NEW_ROAD) & pd.Series(list(zip(Wc.run, Wc.id))).isin(probe_pairs).to_numpy())
        rows["sensitivity_l1_probe_dropped"] = lambda: stage2(Wc[keep], fitW, st1)
    else:
        res["sensitivity_l1_probe_dropped"] = {"skipped": "probe MD5 did not match or probe unavailable", "probe": probe_info}
    for name, fn in rows.items():
        try:
            r = fn()
            res[name] = {"outcome": r["outcome"], "cells": r["cells"]}
        except Exception as e:                # report-only rows never take the main result down
            res[name] = {"error": repr(e)}
        write()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
