"""V4 (merge_vv.md §2, VV-D5): on-ramp merges in NGSIM US-101 and I-80 against the plant's human merges; descriptive, no verdict.
Committed before the plant's merge log is read. Runs on the laptop (no simulation).

Field rules: exact duplicate rows dropped; trajectories split where a vehicle's samples are more than 1 s apart; positions smoothed
(centred 1-s moving mean) before speeds are taken. Merges: US-101, the first lane 6 -> 5 change of a vehicle first seen on lane 7
(7 -> 6 is the gore renaming); I-80, the first frame a vehicle first seen on lane 7 has its smoothed lateral position past the
lane-7/6 line (the midpoint of the two lanes' median Local_X) and stays there 1 s. At that frame: the target-lane follower is the
nearest vehicle behind on the target lane; net gap = merger's rear - follower's front (Local_Y is the front bumper [VERIFY in the
NGSIM documentation]); lag time gap = net gap / follower speed, for followers above 5 m/s; speed difference = merger - follower.
Lane roles and the site facts are inferred from the data and to be checked against the NGSIM documentation [VERIFY].

usage: ngsim_merges.py field CSV OUT
       ngsim_merges.py plant VV_DIR ROWS OUT          (human merges of the L300|nc runs)"""
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
PERIODS = {"us-101": [(7, 0), (8, 5), (8, 20), (9, 0)], "i-80": [(15, 0), (16, 30), (17, 15), (18, 0)]}     # clock edges, 3 periods each
MIN_FOLLOWER_MS = 5.0
SMOOTH = 10     # frames (0.1 s each)
B, RNG = 4000, 20261115


def read(csv: Path):
    import pandas as pd
    parts = []
    for ch in pd.read_csv(csv, usecols=COLS, chunksize=2_000_000):
        parts.append(ch[ch["Location"].isin(tuple(SITES))])
    d = pd.concat(parts, ignore_index=True).drop_duplicates()
    return d.sort_values(["Location", "Vehicle_ID", "Global_Time"]).reset_index(drop=True)


def segments(d):
    """Trajectory id: a vehicle's samples split where consecutive times are more than 1 s apart."""
    gap = d.groupby(["Location", "Vehicle_ID"])["Global_Time"].diff().fillna(0) > 1000
    d = d.copy()
    d["traj"] = gap.groupby([d["Location"], d["Vehicle_ID"]]).cumsum().astype(int)
    return d


def smooth(d):
    """Smoothed positions in metres and speeds from them, per trajectory."""
    import pandas as pd
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


def merge_frames(site: str, d) -> list:
    """(location, vehicle, traj, Global_Time) of each merge, by the site's rule."""
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


def at_merge(site: str, d, frames: list) -> list:
    """Lag gap and speed difference at each merge frame."""
    s = SITES[site]
    by_t = {k: g for k, g in d[(d["Location"] == site) & (d["Lane_ID"] == s["target"])].groupby("Global_Time")}
    me = d[d["Location"] == site].set_index(["Vehicle_ID", "traj", "Global_Time"])
    out = []
    for _, vid, tr, t in frames:
        m = me.loc[(vid, tr, t)]
        tl = by_t.get(t)
        rec = {"vid": int(vid), "t": t, "period": period(site, t), "speed": float(m["v_s"]), "lag": None, "dv": None}
        if tl is not None:
            behind = tl[(tl["Local_Y_s"] < m["Local_Y_s"]) & (tl["Vehicle_ID"] != vid)]
            if len(behind):
                f = behind.loc[behind["Local_Y_s"].idxmax()]
                net = float(m["Local_Y_s"] - m["len_m"] - f["Local_Y_s"])
                rec["dv"] = float(m["v_s"] - f["v_s"])
                if f["v_s"] > MIN_FOLLOWER_MS:
                    rec["lag"] = net / float(f["v_s"])
                rec["net_gap"] = net
        out.append(rec)
    return out


def med_ci(x: list, groups: list | None = None) -> dict:
    """Median with a bootstrap interval over vehicles (field) or over runs (plant: groups[i] = the run of x[i])."""
    keep = [i for i, v in enumerate(x) if v is not None]
    v = np.asarray([x[i] for i in keep], float)
    if not len(v):
        return {"n": 0}
    rng = np.random.default_rng(RNG)
    if groups is None:
        b = np.median(v[rng.integers(0, len(v), (B, len(v)))], axis=1)
    else:
        g = [groups[i] for i in keep]
        sets = [v[[i for i, gg in enumerate(g) if gg == k]] for k in sorted(set(g))]
        b = np.array([np.median(np.concatenate([sets[i] for i in rng.integers(0, len(sets), len(sets))])) for _ in range(B)])
    lo, hi = np.percentile(b, (2.5, 97.5))
    return {"n": int(len(v)), "median": float(np.median(v)), "lo": float(lo), "hi": float(hi)}


def field(csv: Path) -> dict:
    d = smooth(segments(read(csv)))
    out = {}
    for site in SITES:
        recs = at_merge(site, d, merge_frames(site, d))
        out[site] = {"merges": len(recs), "lag_s": med_ci([r["lag"] for r in recs]), "dv_ms": med_ci([r["dv"] for r in recs]),
                     "by_period": {p: {"n": sum(r["period"] == p for r in recs), "lag_median": float(np.median([r["lag"] for r in recs if r["period"] == p and r["lag"] is not None] or [np.nan])),
                                       "dv_median": float(np.median([r["dv"] for r in recs if r["period"] == p and r["dv"] is not None] or [np.nan]))} for p in range(3)},
                     "outside_periods": sum(r["period"] < 0 for r in recs)}
    return out


def plant(vv_dir: Path, rows: Path) -> dict:
    """Human merges (car, truck) in the L300|nc runs, from each run's merge log; split by a human or ALKS follower. A follower on
    another lane (still upstream of the merge point) has net gap = SUMO's distance + its minGap (MSLane::getFollowersOnConsecutive)."""
    lag, dv, run, kind = [], [], [], []
    drop = {"alks_merger": 0, "no_follower": 0}
    for line in open(rows):
        r = json.loads(line)
        if r["name"] != "L300|nc" or not r.get("vv_log_file"):
            continue
        for m in json.load(gzip.open(vv_dir / r["vv_log_file"], "rt"))["merges"]:
            f = m.get("lag")
            if m["type"] == "alks":
                drop["alks_merger"] += 1
                continue
            if not f:
                drop["no_follower"] += 1
                continue
            net = f["net_gap"] if f.get("same_lane") else f["sumo_dist"] + f.get("min_gap", 2.5)
            lag.append(net / f["speed"] if f["speed"] > MIN_FOLLOWER_MS else None)
            dv.append(m["speed"] - f["speed"])
            run.append(r["seed"])
            kind.append("alks" if f["type"] == "alks" else "human")
    out = {"dropped": drop}
    for k in ("all", "human", "alks"):
        sel = [i for i in range(len(run)) if k == "all" or kind[i] == k]
        out[k] = {"lag_s": med_ci([lag[i] for i in sel], [run[i] for i in sel]),
                  "dv_ms": med_ci([dv[i] for i in sel], [run[i] for i in sel])}
    out["note"] = "plant merges are instantaneous lane changes; field merges are timed at the lane-ID change (US-101) or line crossing (I-80)"
    return out


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("field", "plant"))
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("out", nargs="?")
    x = ap.parse_args(argv)
    if x.step == "field":
        res, out = field(Path(x.a)), Path(x.b)
    else:
        res, out = plant(Path(x.a), Path(x.b)), Path(x.out)
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps(res)[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
