"""Confirmatory protocol #1 (docs/research/protocols/confirmatory_1.md, V84).

Stage 1 uses window metadata only (times, regimes, units: no scores) and fixes c, the gated cells and J.
Stage 2 computes scores and decides the outcome. Interpretations fixed before data (logged in the result):
- direction = sign of lane_kf at the window's start step (the protocol's I-294 rule, applied to every set);
- a cell = dataset x regime, pooling its direction units; blocks = (run, 2-min) and may hold both directions;
- W freezes when its N-th window's outcome is known; comparison windows start strictly after that time;
- O's A1 is required on the comparison windows and on all windows of the cell;
- test vehicles: a (run, id) with any acc/av row equal to "yes" (any case), or I-395 type_most_common = 4.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys

import numpy as np
import pandas as pd
from scipy import stats

from v5b import screen1 as s1
from v5b import screen1b as sb

ALPHA, LIMIT, ETA = 0.04, 0.075, 0.5
FLOOR = 1.0
DELAY = s1.WIN + s1.LOOK + 5          # outcome known at window end + 2.5 s (steps of 0.1 s)
TICK, RUN_SPAN, BLOCK = 10, sb.RUN_SPAN, 1200
N_W, N_W_REPORT = 300, 1000
MIN_CMP, MIN_BLOCKS, MAX_CLIP = 1000, 10, 0.05
E_BEAT, HARM = 0.03, 0.05
B_BOOT, SEED_BOOT = 10_000, 7_420_200
SEEDS_P = list(range(7_420_201, 7_420_221))
C_PCT = 90
FIT = {"i90_94_stationary": "tgsim_9uas-hf8b.csv", "i395": "tgsim_97n2-kuqi.csv"}
CONF = {"i294_l1": "tgsim_7zjf-a4zf.csv", "i294_l2": "tgsim_tpsq-zrwa.csv", "i90_94_moving": "tgsim_6a6e-vfvi.csv"}
ROWS = {"i294_l1": 1_024_281, "i294_l2": 137_928, "i90_94_moving": 1_784_748}
REPORT_ONLY_SETS = {"i294_l2"}
NEW_ROAD = "i294_l1"
L1_PROBE_MD5 = "a9f2f0c1249446350e99aafe2bd07212"


# ---------------------------------------------------------------- basics
def qstat(x, alpha=ALPHA):
    """Order-statistic quantile: the ceil((1 - alpha)(n + 1))-th smallest (capped at n)."""
    x = np.sort(np.asarray(x, float))
    if len(x) == 0:
        return float("nan")
    k = min(len(x), math.ceil((1 - alpha) * (len(x) + 1)))
    return float(x[k - 1])


def track(gt, scores, q0, c, floor=FLOOR):
    """Batch-normalised tracker: q <- max(floor, q + ETA/c * sum(miss - ALPHA)) once per second over the
    outcomes known in that second (known = start + DELAY). Returns q_used per window (input order) and the
    tick schedule (for the placebo)."""
    order = np.argsort(gt, kind="stable")
    g, sc = np.asarray(gt)[order], np.asarray(scores, float)[order]
    tick_of = (g + DELAY + TICK - 1) // TICK * TICK
    q, used, j, n = float(max(floor, q0)), np.empty(len(g)), 0, len(g)
    for k in range(n):
        now = g[k] // TICK * TICK
        while j < k and tick_of[j] <= now:
            t0, acc = tick_of[j], 0.0
            while j < k and tick_of[j] == t0:
                acc += (sc[j] > used[j]) - ALPHA
                j += 1
            q = max(floor, q + ETA / c * acc)
        used[k] = q
    out = np.empty(n); out[order] = used
    return out


def placebo(gt, scores, q0, c, seed, floor=FLOOR):
    """O's rule on O's timeline (same slots), windows' scores fed in a random order. Returns, per original
    window, the threshold its score met (so miss = s > q, gap = d(q, its own speed))."""
    rng = np.random.default_rng(seed)
    n = len(gt)
    perm = rng.permutation(n)                       # slot i receives window perm[i]
    order = np.argsort(gt, kind="stable")           # slots in time order
    slot_scores = np.empty(n)
    slot_scores[order] = np.asarray(scores, float)[perm]
    q_slot = track(gt, slot_scores, q0, c, floor)   # q used at each slot
    q_win = np.empty(n)
    q_win[perm] = q_slot[order]
    return q_win


def w_arm(gt, scores, F, n_w=N_W, floor=FLOOR):
    """'Calibrate briefly, then freeze': returns (q per window, freeze time or None)."""
    order = np.argsort(gt, kind="stable")
    if len(gt) <= n_w:
        return np.full(len(gt), max(floor, F)), None
    first = order[:n_w]
    freeze = int(np.asarray(gt)[order[n_w - 1]]) + DELAY
    qw = max(floor, qstat(np.asarray(scores)[first]))
    q = np.where(np.asarray(gt) > freeze, qw, max(floor, F))
    return q, freeze


def comparison_mask(gt, n_w=N_W):
    """Windows starting after W froze (all windows if W = F). Uses times only (Stage 1 safe)."""
    gt = np.asarray(gt)
    if len(gt) <= n_w:
        return np.ones(len(gt), bool)
    freeze = int(np.sort(gt, kind="stable")[n_w - 1]) + DELAY
    return gt > freeze


def c_per_regime(fit_windows):
    """90th percentile of outcomes per non-empty second, fitting units pooled, per regime (counts only)."""
    out = {}
    for r, g in fit_windows.groupby("regime"):
        counts = []
        for _, u in g.groupby(["dataset", "unit"]):
            ticks = (u.gtime.to_numpy() + DELAY + TICK - 1) // TICK
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
                "test_vehicles": len(test_veh)}, test_veh


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
                recs.append((dataset, int(run), int(vid), int(tt[k]), int(run) * RUN_SPAN + int(tt[k]), reg,
                             unit, (int(run), int(vid)) in test_veh, float(vs[k])))
                segs.append(seg.astype(np.float32))
    W = pd.DataFrame(recs, columns=["dataset", "run", "id", "step", "gtime", "regime", "unit", "test", "v0"])
    return W, (np.stack(segs) if segs else np.zeros((0, s1.WIN + s1.LOOK), np.float32))


def scores(segs):
    """Stage 2: screen score and clip flag from the stored segments."""
    segs = np.asarray(segs, float)
    if len(segs) == 0:
        return np.zeros(0), np.zeros(0, bool)
    d1 = (segs[:, :s1.WIN] - segs[:, 10:s1.WIN + 10]).max(axis=1)
    d2 = ((segs[:, :s1.WIN] - segs[:, 20:s1.WIN + 20]) / 2.0).max(axis=1)
    raw = np.maximum(d1, d2)
    return np.clip(raw, 0, s1.CLIP), raw >= s1.CLIP


def order_windows(W):
    return W.sort_values(["run", "step", "id"], kind="stable").reset_index(drop=True)


# ---------------------------------------------------------------- statistics
def tmult(G, level_two_sided=None, one_sided=None):
    if one_sided is not None:
        return stats.t.ppf(one_sided, G - 1) * math.sqrt(G / (G - 1))
    return stats.t.ppf(1 - (1 - level_two_sided) / 2, G - 1) * math.sqrt(G / (G - 1))


def boot_idx(G, seed=SEED_BOOT, B=B_BOOT):
    return np.random.default_rng(seed).integers(0, G, size=(B, G))


def block_sums(blocks, *cols):
    ub, inv = np.unique(blocks, return_inverse=True)
    return [np.bincount(inv, np.asarray(c, float), len(ub)) for c in cols]


def miss_bounds(miss, blocks, J, idx=None):
    """A1 upper bound (one-sided 95 %: max of t-scaled block bootstrap and Clopper-Pearson) and the two
    lower ends used for 'clearly invalid' (two-sided 1 - 0.05/J). miss may be fractional (placebo)."""
    miss = np.asarray(miss, float)
    n = len(miss); k = miss.sum(); p = k / n
    sm, sn = block_sums(blocks, miss, np.ones(n))
    G = len(sm)
    if idx is None or idx.shape[1] != G:
        idx = boot_idx(G)
    bs = sm[idx].sum(1) / sn[idx].sum(1)
    sd = bs.std(ddof=1)
    ub_boot = p + tmult(G, one_sided=0.95) * sd
    ki = int(round(k))
    ub_cp = stats.beta.ppf(0.95, ki + 1, n - ki) if ki < n else 1.0
    lvl = 1 - 0.05 / max(J, 1)
    lo_boot = p - tmult(G, level_two_sided=lvl) * sd
    lo_cp = stats.beta.ppf((1 - lvl) / 2, ki, n - ki + 1) if ki > 0 else 0.0
    return {"p": float(p), "n": int(n), "G": int(G), "ub_boot": float(ub_boot), "ub_cp": float(ub_cp),
            "ub": float(max(ub_boot, ub_cp)), "lo_boot": float(lo_boot), "lo_cp": float(lo_cp),
            "pct95": [float(x) for x in np.percentile(bs, [2.5, 97.5])]}


def a1_valid(b):
    return b["ub"] <= LIMIT


def clearly_invalid(b):
    return b["lo_boot"] > LIMIT and b["lo_cp"] > LIMIT


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


# ---------------------------------------------------------------- stage 1
def stage1(Wc, fitW, rows_seen):
    """Counts only. Returns the gating decision, J and c; never looks at scores."""
    out = {"rows": rows_seen, "rows_expected": ROWS}
    out["rows_ok"] = all(rows_seen.get(k) == v for k, v in ROWS.items())
    out["c"] = c_per_regime(fitW)
    cells = []
    for (ds, reg), g in Wc[~Wc.test].groupby(["dataset", "regime"]):
        cm = np.zeros(len(g), bool)
        for _, u in g.groupby("unit"):
            cm[g.index.get_indexer(u.index)] = comparison_mask(u.gtime.to_numpy())
        blocks = (g.run.to_numpy() * 10**6 + g.step.to_numpy() // BLOCK)[cm]
        n_cmp, n_blk = int(cm.sum()), int(len(np.unique(blocks)))
        gated = reg in ("R1", "R2") and ds not in REPORT_ONLY_SETS and n_cmp >= MIN_CMP and n_blk >= MIN_BLOCKS
        cells.append({"dataset": ds, "regime": reg, "n_all": int(len(g)), "n_cmp": n_cmp, "blocks_cmp": n_blk,
                      "gated": bool(gated)})
    out["cells"] = cells
    out["J"] = sum(c["gated"] for c in cells)
    out["stop_data"] = (not out["rows_ok"]) or out["J"] == 0
    return out


# ---------------------------------------------------------------- stage 2
def arms_for_unit(u, F, c, floor):
    gt, s = u.gtime.to_numpy(), u.s.to_numpy()
    qO = track(gt, s, F, c, floor)
    qW, _ = w_arm(gt, s, F, N_W, floor)
    qW1k, fr1k = w_arm(gt, s, F, N_W_REPORT, floor)
    qP = np.stack([placebo(gt, s, F, c, sd, floor) for sd in SEEDS_P])
    return qO, qW, qW1k, fr1k, qP


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
        g = g.copy()
        n = len(g)
        A = {k: np.full(n, np.nan) for k in ("qO", "qW", "qW1k")}
        M = {k: np.zeros(n, bool) for k in ("cmp", "cmp1k")}
        qP_all = np.full((len(SEEDS_P), n), np.nan)
        pos = {ix: i for i, ix in enumerate(g.index)}
        Fr = F.get(reg, floor)
        for _, u in g.groupby("unit"):
            u = u.sort_values(["run", "step", "id"], kind="stable")
            qO, qW, qW1k, fr1k, qP = arms_for_unit(u, Fr, c.get(reg, 1.0), floor)
            ii = np.array([pos[ix] for ix in u.index])
            A["qO"][ii], A["qW"][ii], A["qW1k"][ii] = qO, qW, qW1k
            M["cmp"][ii] = comparison_mask(u.gtime.to_numpy(), N_W)
            M["cmp1k"][ii] = comparison_mask(u.gtime.to_numpy(), N_W_REPORT)
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
        d = {k: s1.req_gap(x, v) for k, x in q.items()}
        miss = {k: (s > x).astype(float) for k, x in q.items()}
        qPc = qP_all[:, cmp]
        miss["P"] = (s[None, :] > qPc).mean(0)
        d["P"] = np.mean([s1.req_gap(qPc[i], v) for i in range(len(SEEDS_P))], axis=0)
        bounds = {k: miss_bounds(miss[k], blocks, J, idx) for k in miss}
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
        # report-only rows
        gc1k = g[g.cmp1k.to_numpy().astype(bool)]
        w1k = None
        if len(gc1k) > 1:
            b1k = gc1k.run.to_numpy() * 10**6 + gc1k.step.to_numpy() // BLOCK
            if len(np.unique(b1k)) > 1:
                w1k = efficiency(s1.req_gap(gc1k.qO.to_numpy(), gc1k.v0.to_numpy()),
                                 s1.req_gap(gc1k.qW1k.to_numpy(), gc1k.v0.to_numpy()), b1k, J)
        runs = {k: int(max_run(miss[k] > 0.5)) for k in ("F", "W", "O", "H")}
        cell |= {"status": "gated" if cell["gated"] else "report-only", "q": {"F": Fr, "H": qH,
                 "O_median": float(np.median(q["O"])), "W_frozen": float(np.median(q["W"]))},
                 "floor_bound": bool(np.mean(g.qO.to_numpy() <= floor + 1e-12) > 0.5),
                 "mean_gap": {k: float(np.mean(x)) for k, x in d.items()}, "bounds": bounds, "E": E,
                 "validO": bool(validO), "clearly_invalidO": bool(invO), "win": bool(win),
                 "beats_P": bool(beats(E["O_vs_P"])), "clearly_worse": bool(worse), "harm_not_excluded": bool(harm_ne),
                 "W1000_report": w1k, "longest_miss_run": runs}
        res["cells"].append(cell)
    res["outcome"] = decide(res["cells"], st1)
    return res


def max_run(b):
    best = cur = 0
    for x in np.asarray(b, bool):
        cur = cur + 1 if x else 0
        best = max(best, cur)
    return best


def decide(cells, st1):
    """Outcome table (§6), first match wins."""
    if st1["stop_data"]:
        return {"outcome": "STOP-data"}
    g = [c for c in cells if c.get("gated") and c.get("status") == "gated"]
    eligible = [c for c in g if c["clip_share"] <= MAX_CLIP]
    if any(c["clearly_invalidO"] for c in eligible):
        return {"outcome": "KILL"}
    if not eligible or not all(c["validO"] for c in eligible):
        return {"outcome": "INCONCLUSIVE"}
    wins = [c for c in eligible if c["win"]]
    if not wins or any(c["clearly_worse"] for c in eligible):
        return {"outcome": "VALID-ONLY", "clearly_worse": [f'{c["dataset"]}/{c["regime"]}' for c in eligible if c["clearly_worse"]]}
    beats_list = []
    for c in wins:
        for x in ("F", "W"):
            if beats(c["E"][f"O_vs_{x}"]):
                beats_list.append(c["E"][f"O_vs_{x}"])
    x = min(beats_list, key=lambda e: e["E"]) if beats_list else None
    kind = "PASS, new road" if any(c["dataset"] == NEW_ROAD for c in wins) else "PASS, same road"
    return {"outcome": kind, "x": x, "wins": [f'{c["dataset"]}/{c["regime"]}' for c in wins],
            "secondary_tracking": any(c["beats_P"] for c in eligible),
            "harm_not_excluded": [f'{c["dataset"]}/{c["regime"]}' for c in eligible if c["harm_not_excluded"]],
            "floor_bound": [f'{c["dataset"]}/{c["regime"]}' for c in eligible if c["floor_bound"]],
            "report_only_clipped": [f'{c["dataset"]}/{c["regime"]}' for c in g if c["clip_share"] > MAX_CLIP]}


# ---------------------------------------------------------------- run
def build(data_dir, sets):
    Ws, segs, info = [], [], {}
    for ds, fn in sets.items():
        df, inf, tv = load(f"{data_dir}/{fn}", ds)
        lead = sb.leaders(df)
        W, sg = window_meta(df, lead, tv, ds)
        Ws.append(W); segs.append(sg)
        info[ds] = inf | {"matched_leader_share": float((lead >= 0).mean()), "windows": int(len(W)),
                          "test_windows": int(W.test.sum())}
    W = pd.concat(Ws, ignore_index=True)
    return W, np.concatenate(segs) if segs else np.zeros((0, 100)), info


def l1_probe_md5(path, n=20_000):
    h1, h2 = hashlib.md5(), hashlib.md5()
    with open(path, "rb") as f:
        lines = [f.readline() for _ in range(n + 1)]
    h1.update(b"".join(lines)); h2.update(b"".join(lines[1:]))
    return {"with_header": h1.hexdigest(), "rows_only": h2.hexdigest(),
            "match": L1_PROBE_MD5 in (h1.hexdigest(), h2.hexdigest())}


def main(data_dir, out_dir):
    fitW, fitS, fit_info = build(data_dir, FIT)
    Wc, segC, conf_info = build(data_dir, CONF)
    st1 = stage1(Wc, fitW[~fitW.test], {k: conf_info[k]["rows"] for k in CONF})
    st1["data"] = {"fit": fit_info, "conf": conf_info}
    st1["l1_probe"] = l1_probe_md5(f"{data_dir}/{CONF['i294_l1']}")
    json.dump(st1, open(f"{out_dir}/stage1.json", "w"), indent=1, default=str)
    if st1["stop_data"]:
        json.dump({"outcome": {"outcome": "STOP-data"}, "stage1": st1}, open(f"{out_dir}/result.json", "w"), indent=1, default=str)
        print("STOP-data"); return
    fitW["s"], fitW["clipped"] = scores(fitS)
    Wc["s"], Wc["clipped"] = scores(segC)
    main_res = stage2(Wc, fitW, st1)
    sens_test = stage2(Wc, fitW, st1, include_test=True)
    sens_floor0 = stage2(Wc, fitW, st1, floor=0.0)
    res = {"interpretations": __doc__, "stage1": st1, "main": main_res,
           "sensitivity_test_vehicles_scored": {"outcome": sens_test["outcome"], "cells": sens_test["cells"]},
           "report_floor0": {"outcome": sens_floor0["outcome"], "cells": sens_floor0["cells"]}}
    json.dump(res, open(f"{out_dir}/result.json", "w"), indent=1, default=str)
    print(main_res["outcome"]["outcome"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
