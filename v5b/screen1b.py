"""Screen #1b (docs/research/protocols/screen_1b.md): screen #1 on fresh TGSIM data.

Reuses screen #1's score, regimes, d_safe, arms and gates unchanged; adds leader reconstruction and the
batch-normalised tracker. Interpretations fixed before data (logged in the result):
- runs are processed in run_index order on one time axis (run * 1e7 + step), so a site's tracker
  carries over between runs; blocks never cross runs;
- a tick is every 10 steps (1 s) on that axis; a window uses q after the last tick <= its start;
- c_r is rounded to the nearest integer >= 1 for the placebo's batch size.
"""
from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from v5b import screen1 as s1

SITES = ("i90_94_stationary", "i395")
FILES = {"i90_94_stationary": "tgsim_9uas-hf8b.csv", "i395": "tgsim_97n2-kuqi.csv"}
RUN_SPAN = 10_000_000            # steps between runs on the common axis
TICK = 10                        # steps per tracker update (1 s)
MAX_LEAD_GAP = 150.0             # m
DELAY = s1.WIN + s1.LOOK         # steps until a window's outcome is known
BLOCK = s1.BLOCK_MS // s1.DT_MS  # 2 min in steps


# ---------------------------------------------------------------- data + leaders
def load(path):
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    if "run_index" not in df:
        df["run_index"] = 0
    df = df[["run_index", "id", "time", "xloc_kf", "yloc_kf", "lane_kf", "speed_kf"]]
    n0 = len(df)
    df = df.drop_duplicates()
    n_exact = n0 - len(df)
    df["step"] = np.rint(df.time.to_numpy() * 10).astype(np.int64)
    key = ["run_index", "id", "step"]
    n_keydup = int(df.duplicated(key).sum())
    df = df.drop_duplicates(key).sort_values(key, kind="stable").reset_index(drop=True)
    return df, {"rows": n0, "exact_dups": n_exact, "key_dups_dropped": n_keydup}


def leaders(df):
    """Leader id per row (or -1): nearest vehicle ahead in the same run and lane at the same step."""
    g = df.groupby(["run_index", "id"], sort=False)
    first, last = g[["xloc_kf", "yloc_kf"]].transform("first"), g[["xloc_kf", "yloc_kf"]].transform("last")
    d = (last - first).to_numpy()
    n = np.linalg.norm(d, axis=1)
    unit = np.where(n[:, None] > 0, d / np.maximum(n, 1e-9)[:, None], 0.0)
    tmp = pd.DataFrame({"run_index": df.run_index, "lane_kf": df.lane_kf, "id": df.id, "ux": unit[:, 0], "uy": unit[:, 1]})
    per_track = tmp.drop_duplicates(["run_index", "lane_kf", "id"])
    u = per_track.groupby(["run_index", "lane_kf"])[["ux", "uy"]].sum()
    u = u.div(np.hypot(u.ux, u.uy).replace(0, np.nan), axis=0)
    uu = u.reindex(pd.MultiIndex.from_arrays([df.run_index, df.lane_kf])).to_numpy()
    s = df.xloc_kf.to_numpy() * uu[:, 0] + df.yloc_kf.to_numpy() * uu[:, 1]
    w = pd.DataFrame({"run_index": df.run_index.to_numpy(), "lane_kf": df.lane_kf.to_numpy(),
                      "step": df.step.to_numpy(), "s": s, "id": df.id.to_numpy(), "row": np.arange(len(df))})
    w = w[np.isfinite(w.s)].sort_values(["run_index", "lane_kf", "step", "s"], kind="stable")
    same = ((w.run_index.shift(-1) == w.run_index) & (w.lane_kf.shift(-1) == w.lane_kf)
            & (w.step.shift(-1) == w.step)).to_numpy()
    gap = (w.s.shift(-1) - w.s).to_numpy()
    ok = same & (gap > 0) & (gap <= MAX_LEAD_GAP)
    lead = np.full(len(df), -1, dtype=np.int64)
    lead[w.row.to_numpy()[ok]] = w.id.shift(-1).to_numpy()[ok].astype(np.int64)
    return lead


def windows(df, lead):
    """Screen #1 windows on TGSIM: one row per 8-s window of a vehicle that is someone's leader at the start."""
    is_leader = set(zip(df.run_index.to_numpy()[lead >= 0], df.step.to_numpy()[lead >= 0], lead[lead >= 0]))
    recs = []
    for (run, vid), g in df.groupby(["run_index", "id"], sort=False):
        st = g.step.to_numpy()
        v_raw = g.speed_kf.to_numpy(float)
        cut = np.flatnonzero(np.diff(st) > 2) + 1
        for a, b in zip(np.r_[0, cut], np.r_[cut, len(st)]):
            tt, vr = st[a:b], v_raw[a:b]
            if len(tt) < s1.HIST + s1.WIN + s1.LOOK:
                continue
            vs = pd.Series(vr).rolling(11, center=True, min_periods=11).mean().to_numpy()
            for k in range(s1.HIST, len(tt) - s1.WIN - s1.LOOK + 1, s1.WIN):
                if (run, tt[k], vid) not in is_leader:
                    continue
                seg = vs[k:k + s1.WIN + s1.LOOK]
                if np.isnan(seg).any():
                    continue
                raw = max((seg[:s1.WIN] - seg[10:s1.WIN + 10]).max(), ((seg[:s1.WIN] - seg[20:s1.WIN + 20]) / 2.0).max())
                hist = vr[k - s1.HIST:k]
                reg = "R1" if hist.min() < 2.0 else ("R2" if hist.mean() < 10.0 else "R3")
                recs.append((int(run), int(tt[k]), int(run) * RUN_SPAN + int(tt[k]), reg,
                             float(np.clip(raw, 0, s1.CLIP)), bool(raw >= s1.CLIP), float(vs[k])))
    return pd.DataFrame(recs, columns=["run", "step", "gtime", "regime", "s", "clipped", "v0"])


# ---------------------------------------------------------------- batch-normalised tracker
def c_regime(gt):
    """Median number of outcomes per non-empty 1-s tick (counts only)."""
    ticks = (np.asarray(gt) + DELAY + TICK - 1) // TICK
    _, cnt = np.unique(ticks, return_counts=True)
    return float(np.median(cnt)) if len(cnt) else 1.0


def track_batched(gt, scores, q0, c):
    order = np.argsort(gt, kind="stable")
    g, sc = np.asarray(gt)[order], np.asarray(scores)[order]
    tick_of = (g + DELAY + TICK - 1) // TICK * TICK      # first tick at or after the outcome is known
    q, used, j, n = float(q0), np.empty(len(g)), 0, len(g)
    for k in range(n):
        now = g[k] // TICK * TICK                        # last tick <= start
        while j < k and tick_of[j] <= now:
            t0, acc = tick_of[j], 0.0
            while j < k and tick_of[j] == t0:
                acc += (sc[j] > used[j]) - s1.ALPHA
                j += 1
            q = max(s1.Q_FLOOR, q + s1.ETA / c * acc)
        used[k] = q
    out = np.empty(n); out[order] = used
    return out


def track_placebo(scores_perm, q0, c):
    b = max(1, int(round(c)))
    q, used = float(q0), np.empty(len(scores_perm))
    for a in range(0, len(scores_perm), b):
        used[a:a + b] = q
        q = max(s1.Q_FLOOR, q + s1.ETA / c * float(((scores_perm[a:a + b] > q) - s1.ALPHA).sum()))
    return used


# ---------------------------------------------------------------- evaluation (screen #1 rules)
def evaluate(W):
    rng = np.random.default_rng(s1.SEED)
    res = {"cells": [], "interpretations": __doc__}
    F = {s: W[W.site == s].groupby("regime").s.quantile(1 - s1.ALPHA).to_dict() for s in SITES}
    C = {s: {r: c_regime(W[(W.site == s) & (W.regime == r)].gtime.to_numpy()) for r in ("R1", "R2", "R3")} for s in SITES}
    res["c_r"] = C
    for fit, ev in ((SITES[0], SITES[1]), (SITES[1], SITES[0])):
        E = W[W.site == ev]
        for reg in ("R1", "R2", "R3"):
            c = E[E.regime == reg].sort_values("gtime", kind="stable")
            cell = {"fit": fit, "eval": ev, "regime": reg, "n": int(len(c))}
            if reg not in F[fit] or len(c) == 0:
                res["cells"].append(cell | {"status": "empty"}); continue
            s, v, gt = c.s.to_numpy(), c.v0.to_numpy(), c.gtime.to_numpy()
            cr = C[fit][reg]
            qF = np.full(len(c), F[fit][reg])
            qO = track_batched(gt, s, F[fit][reg], cr)
            qH = np.full(len(c), np.quantile(s, 1 - s1.ALPHA))
            perm = rng.permutation(len(c))
            qP = np.empty(len(c)); qP[perm] = track_placebo(s[perm], F[fit][reg], cr)
            arms = (("F", qF), ("O", qO), ("H", qH), ("P", qP))
            d = {k: s1.req_gap(q, v) for k, q in arms}
            miss = {k: float((s > q).mean()) for k, q in arms}
            blocks = c.run.to_numpy() * 10**6 + c.step.to_numpy() // BLOCK
            ub, inv = np.unique(blocks, return_inverse=True)
            sums = {k: np.bincount(inv, d[k], len(ub)) for k in d}
            ratio = lambda a, b, idx=slice(None): 1 - sums[a][idx].sum() / sums[b][idx].sum()
            boot = np.array([ratio("O", "F", rng.integers(0, len(ub), len(ub))) for _ in range(s1.B_BOOT)])
            lo, hi = np.percentile(boot, [2.5, 97.5])
            clip_share = float(c.clipped.mean())
            gated = reg in s1.GATED and len(c) >= s1.MIN_WINDOWS and clip_share <= s1.MAX_CLIP_SHARE
            validO, validF = miss["O"] <= s1.ALPHA + s1.DELTA, miss["F"] <= s1.ALPHA + s1.DELTA
            Eo = ratio("O", "F")
            win = gated and validO and ((not validF) or (Eo >= s1.E_MIN and lo > 0))
            cell |= {"status": "gated" if gated else "report-only", "n_blocks": int(len(ub)), "c_r": cr,
                     "clip_share": clip_share, "miss": miss, "qF": float(F[fit][reg]), "qH": float(qH[0]),
                     "qO_median": float(np.median(qO)), "qO_p10_p90": [float(x) for x in np.percentile(qO, [10, 90])],
                     "mean_gap_m": {k: float(d[k].mean()) for k in d}, "E_O_vs_F": float(Eo),
                     "E_CI95": [float(lo), float(hi)], "E_H_vs_F": float(ratio("H", "F")), "E_P_vs_F": float(ratio("P", "F")),
                     "validO": bool(validO), "validF": bool(validF), "WIN": bool(win),
                     "win_basis": ("a: F invalid" if (win and not validF) else ("b: efficiency" if win else ""))}
            res["cells"].append(cell)
    g = [c for c in res["cells"] if c.get("status") == "gated"]
    res["outcome"] = "STOP (data)" if not g else ("CONTINUE" if any(c["WIN"] for c in g) else "STOP")
    return res


def main(data_dir, out):
    parts, info = [], {}
    for site in SITES:
        df, inf = load(f"{data_dir}/{FILES[site]}")
        lead = leaders(df)
        W = windows(df, lead)
        W["site"] = site
        parts.append(W)
        info[site] = inf | {"rows_with_leader": int((lead >= 0).sum()), "windows": W.groupby("regime").size().to_dict(),
                            "runs": sorted(int(r) for r in df.run_index.unique())}
    res = evaluate(pd.concat(parts, ignore_index=True))
    res["data"] = info
    with open(out, "w") as f:
        json.dump(res, f, indent=1, default=str)
    print(res["outcome"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
