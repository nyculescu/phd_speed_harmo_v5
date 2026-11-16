"""B0 reader (docs/research/protocols/b0_merge_stops.md v1, V541): plant against NGSIM stops before merging. Laptop only, stored data.

usage: b0_read.py stage_a CSV VV_DIR OUT_DIR
       b0_read.py stage_b CSV VV_DIR OUT_DIR      (needs OUT_DIR/stage_a.json, read once)

Field extraction (read, segments, smooth, period, merge_frames) is copied from docs/research/vv/ngsim_merges.py (branch vv/merge,
6e96988) so the merge frames are V4's. Choices the protocol leaves open, fixed here before data:
- the "none" band (no vehicle within 200 m) joins the 20+ band when it is too small;
- the stage A stop rule reads "the power table gives under 0.5": a site is uninformative when both powers are under 0.5 at every
  grid value of f;
- power model: field blocks beta-binomial with design effect 3 at the mean block size, plant share known with the same design
  effect over its mergers; censoring at the site's censored share c taken at its worst (f_hi = f + c(1 - f), f_lo = f(1 - c));
- plant follower and leader count only within 200 m (`sumo_dist`), field ones within 200 m net gap;
- field blocks: (period, floor(minutes since the period start / block)).
"""
import argparse
import datetime as dt
import gzip
import json
import sys
from pathlib import Path

import numpy as np

FT = 0.3048
COLS = ["Vehicle_ID", "Frame_ID", "Global_Time", "Local_X", "Local_Y", "v_length", "v_Vel", "Lane_ID", "Location"]
SITES = {"us-101": {"ramp": 7, "aux": 6, "target": 5}, "i-80": {"ramp": 7, "target": 6}}
TZ = dt.timezone(dt.timedelta(hours=-7))     # Pacific daylight time [VERIFY]
PERIODS = {"us-101": [(7, 0), (8, 5), (8, 20), (9, 0)], "i-80": [(15, 0), (16, 30), (17, 15), (18, 0)]}
SMOOTH = 10     # frames (0.1 s each)

WIN_S = 10.0
EDGE_S = 0.6     # the centred 1-s mean halves speeds this close to a trajectory's ends
RANGE_M = 200.0
WARM_S, HIST_S = 300.0, 10.0
BANDS = ["<5", "5-10", "10-15", "15-20", "20+", "none"]
TOWARD = {"<5": "5-10", "5-10": "10-15", "15-20": "10-15", "20+": "15-20", "none": "20+"}
MIN_PLANT, MIN_FIELD = 20, 10
POOLED_MAX = 0.20
THR_PLANT, THR_FIELD = 1.0, (1.0, 2.0)
BLOCKS_MIN = (1, 2, 5)
B, RNG = 20_000, 20261116
F_GRID = (0.01, 0.05, 0.10, 0.20, 0.30, 0.50)
DEFF = 3.0
NOT_MORE_PTS, NOT_MORE_RATIO = 5.0, 1.5


def band(speed):
    if speed is None:
        return "none"
    for b, hi in zip(BANDS, (5, 10, 15, 20)):
        if speed < hi:
            return b
    return "20+"


# Field

def read(csv: Path):
    import pandas as pd
    parts = []
    for ch in pd.read_csv(csv, usecols=COLS, chunksize=2_000_000):
        parts.append(ch[ch["Location"].isin(tuple(SITES))])
    d = pd.concat(parts, ignore_index=True).drop_duplicates()
    return d.sort_values(["Location", "Vehicle_ID", "Global_Time"]).reset_index(drop=True)


def segments(d):
    gap = d.groupby(["Location", "Vehicle_ID"])["Global_Time"].diff().fillna(0) > 1000
    d = d.copy()
    d["traj"] = gap.groupby([d["Location"], d["Vehicle_ID"]]).cumsum().astype(int)
    return d


def smooth(d):
    d = d.copy()
    g = d.groupby(["Location", "Vehicle_ID", "traj"])
    for c in ("Local_X", "Local_Y"):
        d[c + "_s"] = g[c].transform(lambda x: x.rolling(SMOOTH, center=True, min_periods=1).mean()) * FT
    t = d["Global_Time"] / 1000.0
    dy = g["Local_Y_s"].diff()
    dtt = g["Global_Time"].diff() / 1000.0
    v = (dy / dtt).where(dtt > 0)
    d["v_s"] = v.groupby([d["Location"], d["Vehicle_ID"], d["traj"]]).transform(lambda x: x.bfill().ffill())
    d["len_m"] = d["v_length"] * FT
    d["t"] = t
    return d.reset_index(drop=True)


def period(site: str, t_ms: float) -> int:
    h = dt.datetime.fromtimestamp(t_ms / 1000.0, TZ)
    x = (h.hour, h.minute)
    edges = PERIODS[site]
    for i in range(3):
        if edges[i] <= x < edges[i + 1]:
            return i
    return -1


def period_start_ms(site: str, p: int, t_ms: float) -> float:
    h = dt.datetime.fromtimestamp(t_ms / 1000.0, TZ)
    hh, mm = PERIODS[site][p]
    return h.replace(hour=hh, minute=mm, second=0, microsecond=0).timestamp() * 1000.0


def merge_frames(site: str, d) -> list:
    s = SITES[site]
    out = []
    dd = d[d["Location"] == site]
    if site == "i-80":
        x6 = dd.loc[dd["Lane_ID"] == s["target"], "Local_X"].median() * FT
        x7 = dd.loc[dd["Lane_ID"] == s["ramp"], "Local_X"].median() * FT
        line, side = 0.5 * (x6 + x7), np.sign(x6 - x7)
    for (vid, tr), g in dd.groupby(["Vehicle_ID", "traj"]):
        if g["Lane_ID"].iloc[0] != s["ramp"]:
            continue
        if site == "us-101":
            lane = g["Lane_ID"].to_numpy()
            hit = np.nonzero((lane[1:] == s["target"]) & (lane[:-1] == s["aux"]))[0]
            if len(hit):
                out.append((site, vid, tr, float(g["Global_Time"].iloc[hit[0] + 1])))
        else:
            past = side * (g["Local_X_s"].to_numpy() - line) > 0
            t = g["Global_Time"].to_numpy()
            for i in np.nonzero(past)[0]:
                j = np.searchsorted(t, t[i] + 1000.0)
                if j <= len(t) and past[i:j].all():
                    out.append((site, vid, tr, float(t[i])))
                    break
    return out


def history(t: np.ndarray, v: np.ndarray, t_merge: float) -> dict:
    """Speeds of one trajectory in the WIN_S before its merge frame, edge samples dropped; t in s."""
    ok = (t >= t[0] + EDGE_S - 1e-9) & (t <= t[-1] - EDGE_S + 1e-9)
    w = ok & (t >= t_merge - WIN_S - 1e-9) & (t < t_merge - 1e-9)
    first = t[ok][0] if ok.any() else t_merge
    return {"speeds": v[w], "times": t[w], "censored": bool(first > t_merge - WIN_S + 0.1 + 1e-9), "hist_s": float(t_merge - first)}


def neighbours(site: str, tl, y: float, length: float, vid) -> tuple:
    """Speeds of the nearest target-lane leader and follower within RANGE_M (net gap), or None."""
    lead = fol = None
    if tl is not None:
        other = tl[tl["Vehicle_ID"] != vid]
        ahead = other[other["Local_Y_s"] > y]
        if len(ahead):
            a = ahead.loc[ahead["Local_Y_s"].idxmin()]
            if a["Local_Y_s"] - a["len_m"] - y <= RANGE_M:
                lead = float(a["v_s"])
        behind = other[other["Local_Y_s"] < y]
        if len(behind):
            f = behind.loc[behind["Local_Y_s"].idxmax()]
            if y - length - f["Local_Y_s"] <= RANGE_M:
                fol = float(f["v_s"])
    return lead, fol


def field_mergers(csv: Path) -> dict:
    d = smooth(segments(read(csv)))
    out = {}
    for site in SITES:
        s = SITES[site]
        ds = d[d["Location"] == site]
        by_t = {k: g for k, g in ds[ds["Lane_ID"] == s["target"]].groupby("Global_Time")}
        trajs = {k: g for k, g in ds.groupby(["Vehicle_ID", "traj"])}
        recs = []
        for _, vid, tr, tm in merge_frames(site, d):
            g = trajs[(vid, tr)]
            t, v = g["t"].to_numpy(), g["v_s"].to_numpy()
            row = g[g["Global_Time"] == tm].iloc[0]
            lead, fol = neighbours(site, by_t.get(tm), float(row["Local_Y_s"]), float(row["len_m"]), vid)
            ramp = g[g["Lane_ID"] == s["ramp"]]
            p = period(site, tm)
            recs.append({"vid": int(vid), "t_ms": tm, "period": p,
                         "block_min": None if p < 0 else (tm - period_start_ms(site, p, tm)) / 60000.0,
                         "lead": lead, "fol": fol, "hist": history(t, v, tm / 1000.0),
                         "dist_from_ramp_m": float(row["Local_Y_s"] - ramp["Local_Y_s"].iloc[0]) if len(ramp) else None})
        out[site] = recs
    return out


# Plant

def plant_mergers(vv_dir: Path) -> dict:
    """First merge record per vehicle in each L300|nc run, merges in the first HIST_S after warm-up dropped."""
    out, stats = [], {"files": 0, "repeat": 0, "early": 0, "records": 0}
    for f in sorted(vv_dir.glob("L300__nc__5300__*.json.gz")):
        seed = int(f.name.split("__")[-1].split(".")[0])
        d = json.load(gzip.open(f, "rt"))
        stats["files"] += 1
        seen = set()
        stand = {x: set(c) for x, c in d["stand"].items()}
        for m in sorted(d["merges"], key=lambda r: r["t"]):
            stats["records"] += 1
            assert m["t"] > WARM_S
            if m["v"] in seen:
                stats["repeat"] += 1
                continue
            seen.add(m["v"])
            if m["t"] < WARM_S + HIST_S:
                stats["early"] += 1
                continue
            near = lambda k: m[k]["speed"] if m.get(k) and m[k]["sumo_dist"] <= RANGE_M else None
            out.append({"seed": seed, "type": m["type"], "lane0": m["lane0"], "pos0": m["pos0"], "min10": m["min_speed_10s"],
                        "lead": near("lead"), "fol": near("lag"),
                        "fol_type": (m["lag"]["type"] if m.get("lag") else None), "stood_end": m["v"] in stand.get(m["lane0"], ())})
    return {"recs": out, "stats": stats}


def human(r) -> bool:
    return r["type"] in ("car", "truck")


# Stage A

def pooling(plant_n: dict, field_n: dict) -> dict:
    """Band -> pooled group; small bands join their neighbour towards 10-15 until every group passes."""
    group = {b: b for b in BANDS}

    def sizes():
        pn, fn = {}, {}
        for b in BANDS:
            pn[group[b]] = pn.get(group[b], 0) + plant_n.get(b, 0)
            fn[group[b]] = fn.get(group[b], 0) + field_n.get(b, 0)
        return pn, fn

    for _ in range(len(BANDS)):
        pn, fn = sizes()
        small = [g for g in pn if g != "10-15" and (pn[g] < MIN_PLANT or fn[g] < MIN_FIELD)]
        if not small:
            break
        g = small[0]
        tgt = TOWARD[g]
        for b in BANDS:
            if group[b] == g:
                group[b] = group[tgt]
    return group


def power(n_field: int, n_blocks: int, c: float, n_plant: int, rng) -> dict:
    """P(MORE) at a true difference of +10 points and P(NOT MORE) at 0, per f in F_GRID (model in the module docstring)."""
    m = max(n_field / max(n_blocks, 1), 1.0)
    icc = (DEFF - 1.0) / (m - 1.0) if m > 1 else 0.0
    sizes = np.full(n_blocks, n_field // n_blocks)
    sizes[: n_field - sizes.sum()] += 1
    out = {}
    for f in F_GRID:
        res = {}
        for delta, key in ((0.10, "more_at_+10"), (0.0, "not_more_at_0")):
            hits, reps = 0, 300
            for _ in range(reps):
                pf = rng.beta(f * (1 / icc - 1), (1 - f) * (1 / icc - 1), n_blocks) if 0 < icc < 1 else np.full(n_blocks, f)
                k = rng.binomial(sizes, pf)
                fp = min(f + delta, 1.0)
                plant = rng.normal(fp, np.sqrt(DEFF * fp * (1 - fp) / n_plant))
                idx = rng.integers(0, n_blocks, (400, n_blocks))
                fb = k[idx].sum(1) / sizes[idx].sum(1)
                pb = rng.normal(plant, np.sqrt(DEFF * fp * (1 - fp) / n_plant), 400)
                if key == "more_at_+10":
                    fhi = fb + c * (1 - fb)
                    hits += np.percentile(100 * (pb - fhi), 2.5) > 0
                else:
                    flo = fb * (1 - c)
                    up = np.percentile(100 * (pb - flo), 97.5)
                    ratio = np.percentile(pb / np.maximum(flo, 1e-9), 97.5)
                    hits += (up <= NOT_MORE_PTS) and (ratio <= NOT_MORE_RATIO)
            res[key] = hits / reps
        out[f"{f:g}"] = res
    return out


def stage_a(csv: Path, vv_dir: Path, out_dir: Path) -> dict:
    fm, pm = field_mergers(csv), plant_mergers(vv_dir)
    ph = [r for r in pm["recs"] if human(r)]
    res = {"plant": {"stats": pm["stats"], "human_mergers": len(ph), "alks_mergers": len(pm["recs"]) - len(ph)}, "sites": {}}
    rng = np.random.default_rng(RNG)
    stop = []
    for site, recs in fm.items():
        out = {"mergers": len(recs), "outside_periods": sum(r["period"] < 0 for r in recs),
               "censored_share": float(np.mean([r["hist"]["censored"] for r in recs])) if recs else None,
               "hist_s_quartiles": np.percentile([r["hist"]["hist_s"] for r in recs], (25, 50, 75)).round(2).tolist() if recs else None,
               "blocks": {}, "bandings": {}}
        for bm in BLOCKS_MIN:
            out["blocks"][str(bm)] = {str(p): len({int(r["block_min"] // bm) for r in recs if r["period"] == p}) for p in range(3)}
        for key in ("lead", "fol"):
            pn = {b: sum(band(r[key]) == b for r in ph) for b in BANDS}
            fn = {b: sum(band(r[key]) == b for r in recs) for b in BANDS}
            med = lambda rs: {b: (float(np.median([r[key] for r in rs if band(r[key]) == b])) if b != "none" and any(band(r[key]) == b for r in rs) else None) for b in BANDS}
            grp = pooling(pn, fn)
            pooled_w = sum(fn[b] for b in BANDS if grp[b] != b or any(grp[o] == b and o != b for o in BANDS)) / max(len(recs), 1)
            out["bandings"][key] = {"plant_n": pn, "field_n": fn, "plant_median": med(ph), "field_median": med(recs),
                                    "groups": grp, "pooled_weight": pooled_w, "comparable": pooled_w <= POOLED_MAX}
        nb = out["blocks"]["2"]
        pw = power(len(recs), max(sum(nb.values()), 1), out["censored_share"] or 0.0, len(ph), rng)
        out["power"] = pw
        out["informative"] = any(v["more_at_+10"] >= 0.5 or v["not_more_at_0"] >= 0.5 for v in pw.values())
        stop.append(not out["informative"])
        res["sites"][site] = out
    res["NOT_INFORMATIVE"] = any(stop)
    res["MIXED_AT_MOST"] = any(not b["comparable"] for s in res["sites"].values() for b in s["bandings"].values())
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "stage_a.json").write_text(json.dumps(res, indent=1))
    return res


# Stage B

def field_stop(r, thr: float, upper: bool) -> bool:
    sp = r["hist"]["speeds"]
    seen = bool(len(sp)) and float(np.min(sp)) < thr
    return seen or (upper and r["hist"]["censored"])


def plant_counts(ph: list, key: str, grp: dict) -> tuple:
    """Per seed and pooled group: mergers and stops; arrays (seeds, groups)."""
    seeds = sorted({r["seed"] for r in ph})
    gs = sorted(set(grp.values()), key=BANDS.index)
    si, gi = {s: i for i, s in enumerate(seeds)}, {g: i for i, g in enumerate(gs)}
    n, k = np.zeros((len(seeds), len(gs))), np.zeros((len(seeds), len(gs)))
    for r in ph:
        a, b = si[r["seed"]], gi[grp[band(r[key])]]
        n[a, b] += 1
        k[a, b] += r["min10"] < THR_PLANT
    return n, k, gs


def field_counts(recs: list, key: str, grp: dict, gs: list, bm: int, thr: float) -> tuple:
    """Per block and pooled group: mergers, stops (lower and upper bound); and each block's period."""
    gi = {g: i for i, g in enumerate(gs)}
    blocks = sorted({(r["period"], int(r["block_min"] // bm)) for r in recs if r["period"] >= 0})
    bi = {b: i for i, b in enumerate(blocks)}
    n, lo, hi = (np.zeros((len(blocks), len(gs))) for _ in range(3))
    for r in recs:
        if r["period"] < 0:
            continue
        j, g = bi[(r["period"], int(r["block_min"] // bm))], gi[grp[band(r[key])]]
        n[j, g] += 1
        lo[j, g] += field_stop(r, thr, False)
        hi[j, g] += field_stop(r, thr, True)
    return n, lo, hi, np.array([b[0] for b in blocks])


def resample_blocks(per: np.ndarray, rng, reps: int) -> np.ndarray:
    """Block indices resampled within each period: (reps, n_blocks)."""
    cols = []
    for p in sorted(set(per)):
        ix = np.nonzero(per == p)[0]
        cols.append(ix[rng.integers(0, len(ix), (reps, len(ix)))])
    return np.concatenate(cols, axis=1)


def compare(pn, pk, fn, flo, fhi, fper, rng) -> dict:
    """D (points) and ratio with f_lo and f_hi: point and 95 % percentile interval."""
    ns = pn.shape[0]

    def stat(pn_, pk_, fn_, flo_, fhi_):
        p = pk_.sum(-2) / np.maximum(pn_.sum(-2), 1)
        w = fn_.sum(-2) / np.maximum(fn_.sum((-2, -1))[..., None], 1)
        std = (w * p).sum(-1)
        tot = np.maximum(fn_.sum((-2, -1)), 1)
        f_lo, f_hi = flo_.sum((-2, -1)) / tot, fhi_.sum((-2, -1)) / tot
        return {"D_lo": 100 * (std - f_lo), "D_hi": 100 * (std - f_hi), "R_lo": std / np.maximum(f_lo, 1e-9),
                "R_hi": std / np.maximum(f_hi, 1e-9), "plant": 100 * std, "f_lo": 100 * f_lo, "f_hi": 100 * f_hi}

    point = {k: float(v) for k, v in stat(pn, pk, fn, flo, fhi).items()}
    acc = {k: [] for k in point}
    for c0 in range(0, B, 2000):
        reps = min(2000, B - c0)
        si = rng.integers(0, ns, (reps, ns))
        bi = resample_blocks(fper, rng, reps)
        s = stat(pn[si], pk[si], fn[bi], flo[bi], fhi[bi])
        for k in acc:
            acc[k].append(s[k])
    out = {}
    for k, v in point.items():
        a = np.concatenate(acc[k])
        out[k] = {"point": v, "lo": float(np.percentile(a, 2.5)), "hi": float(np.percentile(a, 97.5))}
    return out


def stage_b(csv: Path, vv_dir: Path, out_dir: Path) -> dict:
    a = json.loads((out_dir / "stage_a.json").read_text())
    if (out_dir / "stage_b.json").exists():
        raise SystemExit("stage B already read")
    fm, pm = field_mergers(csv), plant_mergers(vv_dir)
    ph = [r for r in pm["recs"] if human(r)]
    rng = np.random.default_rng(RNG)
    res = {"stage_a_not_informative": a["NOT_INFORMATIVE"], "mixed_at_most": a["MIXED_AT_MOST"], "cells": {}, "printed": {}}
    ok_more, ok_not = True, True
    for site, recs in fm.items():
        for key in ("lead", "fol"):
            grp = a["sites"][site]["bandings"][key]["groups"]
            pn, pk, gs = plant_counts(ph, key, grp)
            for thr in THR_FIELD:
                cells = {}
                for bm in BLOCKS_MIN:
                    fn, flo, fhi, fper = field_counts(recs, key, grp, gs, bm, thr)
                    cells[str(bm)] = compare(pn, pk, fn, flo, fhi, fper, rng)
                wide = max(cells, key=lambda k: cells[k]["D_lo"]["hi"] - cells[k]["D_lo"]["lo"] + cells[k]["D_hi"]["hi"] - cells[k]["D_hi"]["lo"])
                c = cells[wide]
                more = c["D_hi"]["lo"] > 0
                notm = c["D_lo"]["hi"] <= NOT_MORE_PTS and c["R_lo"]["hi"] <= NOT_MORE_RATIO
                ok_more &= more
                ok_not &= notm
                res["cells"][f"{site}|{key}|{thr:g}"] = {"by_block": cells, "deciding_block_min": wide, "more": more, "not_more": notm}
    if a["NOT_INFORMATIVE"]:
        reading = "NOT INFORMATIVE"
    elif ok_more and not a["MIXED_AT_MOST"]:
        reading = "MORE"
    elif ok_not and not a["MIXED_AT_MOST"]:
        reading = "NOT MORE"
    else:
        reading = "MIXED"
    res["reading"] = reading
    res["printed"] = printed(fm, pm, ph, a, rng)
    (out_dir / "stage_b.json").write_text(json.dumps(res, indent=1))
    return res


def printed(fm, pm, ph, a, rng) -> dict:
    """Never deciding (protocol §5)."""
    share = lambda rs: (100 * float(np.mean([r["min10"] < THR_PLANT for r in rs])), len(rs)) if rs else (None, 0)
    stoppers = [r for r in ph if r["min10"] < THR_PLANT]
    out = {"plant": {
        "raw_share_human": share(ph),
        "by_merge": {x: share([r for r in ph if r["lane0"] == x]) for x in ("3a_0", "4a_0")},
        "by_follower_type": {t: share([r for r in ph if (r["fol_type"] == "alks") == (t == "alks") and r["fol_type"]]) for t in ("human", "alks")},
        "by_lead_band": {b: share([r for r in ph if band(r["lead"]) == b]) for b in BANDS},
        "alks_mergers": share([r for r in pm["recs"] if not human(r)]),
        "stoppers_in_end_standing_log": 100 * float(np.mean([r["stood_end"] for r in stoppers])) if stoppers else None,
        "merges_in_last_30m": 100 * float(np.mean([r["pos0"] > 294.72 - 30.0 for r in ph])),
        "pos0_quartiles": np.percentile([r["pos0"] for r in ph], (10, 25, 50, 75, 90)).round(1).tolist()}, "field": {}}
    for site, recs in fm.items():
        f = {}
        for thr in THR_FIELD:
            f[f"thr{thr:g}"] = {"f_lo": 100 * float(np.mean([field_stop(r, thr, False) for r in recs])),
                                "f_hi": 100 * float(np.mean([field_stop(r, thr, True) for r in recs])),
                                "by_period": {p: 100 * float(np.mean([field_stop(r, thr, False) for r in recs if r["period"] == p] or [np.nan])) for p in range(3)},
                                "by_lead_band_lo": {b: 100 * float(np.mean([field_stop(r, thr, False) for r in recs if band(r["lead"]) == b] or [np.nan])) for b in BANDS}}
        five = []
        for r in recs:
            h = r["hist"]
            sp = h["speeds"][h["times"] >= (r["t_ms"] / 1000.0) - 5.0 - 1e-9] if len(h["speeds"]) else h["speeds"]
            five.append(bool(len(sp)) and float(np.min(sp)) < 1.0)
        f["window_5s_thr1_lo"] = 100 * float(np.mean(five))
        dist = [r["dist_from_ramp_m"] for r in recs if r["dist_from_ramp_m"] is not None]
        f["dist_from_ramp_quartiles"] = np.percentile(dist, (10, 25, 50, 75, 90)).round(1).tolist() if dist else None
        out["field"][site] = f
    # Field against field: US-101 in the plant's place, I-80 as the field, leader banding with I-80's groups, 2-min blocks.
    grp = a["sites"]["i-80"]["bandings"]["lead"]["groups"]
    gs = sorted(set(grp.values()), key=BANDS.index)
    ref = {}
    for thr in THR_FIELD:
        un, ulo, uhi, uper = field_counts(fm["us-101"], "lead", grp, gs, 2, thr)
        n, lo, hi, per = field_counts(fm["i-80"], "lead", grp, gs, 2, thr)
        ref[f"thr{thr:g}"] = field_ref(un, ulo, uhi, uper, n, lo, hi, per, rng)
    out["field_vs_field_us101_minus_i80"] = ref
    return out


def field_ref(un, ulo, uhi, uper, n, lo, hi, per, rng) -> dict:
    """US-101 in the plant's place: sum_b w_b(I-80) p_b(US-101) - f(I-80), points, 95 % interval over both sites' blocks."""
    def stat(un_, us_, n_, s_):
        p = us_.sum(-2) / np.maximum(un_.sum(-2), 1)
        w = n_.sum(-2) / np.maximum(n_.sum((-2, -1))[..., None], 1)
        return 100 * ((w * p).sum(-1) - s_.sum((-2, -1)) / np.maximum(n_.sum((-2, -1)), 1))
    out = {}
    for tag, us, s in (("lo", ulo, lo), ("hi", uhi, hi)):
        pt = float(stat(un, us, n, s))
        draws = []
        for c0 in range(0, B, 2000):
            reps = min(2000, B - c0)
            bu, bf = resample_blocks(uper, rng, reps), resample_blocks(per, rng, reps)
            draws.append(stat(un[bu], us[bu], n[bf], s[bf]))
        d = np.concatenate(draws)
        out[tag] = {"point": pt, "lo": float(np.percentile(d, 2.5)), "hi": float(np.percentile(d, 97.5))}
    return out


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("stage", choices=("stage_a", "stage_b"))
    ap.add_argument("csv")
    ap.add_argument("vv_dir")
    ap.add_argument("out_dir")
    x = ap.parse_args(argv)
    f = stage_a if x.stage == "stage_a" else stage_b
    res = f(Path(x.csv), Path(x.vv_dir), Path(x.out_dir))
    print(json.dumps({k: v for k, v in res.items() if k in ("NOT_INFORMATIVE", "MIXED_AT_MOST", "reading")}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
