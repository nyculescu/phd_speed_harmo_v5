"""Corridor analysis on real MnDOT data (docs/plans/day_pattern_corridor_analysis_protocol_v0.md, committed first).

Uses only cached Mayfly files (no requests). Writes docs/plans/day_pattern_corridor_analysis_v0.json.

python -m vsl_lab.data.corridor_analysis
"""
from __future__ import annotations

import datetime as dt
from fractions import Fraction
import json
import sys
from pathlib import Path

import numpy as np
from scipy.signal import find_peaks
from scipy.stats import spearmanr

from vsl_lab.data.mndot import DATA_ROOT, DOWN_KM, TOP3, corridor_detectors, pass1_dates

B0, B1 = 60, 276                 # 5-min bins 05:00-23:00 (216 bins)
NB = B1 - B0
V_CONG, DV, BN_MIN, BN_WIN = 40.0, 20.0, 5, 7
MAX_GAP_KM, MERGE_GAP = 3.0, 6   # pair spacing; episodes merged if separated by < 30 min
OUT = Path(__file__).resolve().parents[2] / "docs" / "plans" / "day_pattern_corridor_analysis_v1.json"   # Addendum A re-run


def _load(date: str, det: str, kind: str):
    f = DATA_ROOT / "mayfly" / date[:4] / date / f"{det}.{kind}.json"
    if not f.exists():
        return None
    t = f.read_text()
    return None if t == "null" else json.loads(t)


def lane_bins(date: str, det: str):
    """(flow veh/h, occupancy %, valid) arrays over the 216 bins. With 9 of 10 values present, the flow is scaled
    by 10/9 (disclosed implementation detail of 'the sum of its ten 30-s counts')."""
    c, o = _load(date, det, "counts"), _load(date, det, "occupancy")
    q = np.full(NB, np.nan)
    occ = np.full(NB, np.nan)
    if c is None or o is None:
        return q, occ
    for j, b in enumerate(range(B0, B1)):
        cs = [x for x in c[b * 10:(b + 1) * 10] if x is not None]
        os_ = [x for x in o[b * 10:(b + 1) * 10] if x is not None]
        if len(cs) >= 9 and len(os_) >= 9:
            q[j] = 12.0 * sum(cs) * 10.0 / len(cs)
            occ[j] = sum(os_) / len(os_)
    return q, occ


def station_day(date: str, st: dict):
    """Station flow q (veh/h), density k (veh/mi), speed v (mph); NaN where any lane is invalid."""
    Q, K = np.zeros(NB), np.zeros(NB)
    for det, _lane, field in st["dets"]:
        q, occ = lane_bins(date, det)
        Q = Q + q
        K = K + occ / 100.0 * 5280.0 / float(field)
    with np.errstate(divide="ignore", invalid="ignore"):
        V = np.where(K > 0, Q / K, np.inf)
    V = np.where(np.isnan(Q) | np.isnan(K), np.nan, V)
    valid = np.mean(~np.isnan(Q)) >= 0.9
    return {"q": Q, "k": K, "v": V, "valid": bool(valid), "lanes": len(st["dets"])}


def episodes(cond: np.ndarray) -> list:
    """Spans of qualifying windows (>= BN_MIN of BN_WIN bins), merged across gaps < MERGE_GAP; inclusive bins."""
    cov = np.zeros(len(cond), bool)
    for j in range(len(cond) - BN_WIN + 1):
        if cond[j:j + BN_WIN].sum() >= BN_MIN:
            cov[j:j + BN_WIN] = True
    spans, start = [], None
    for j, x in enumerate(list(cov) + [False]):
        if x and start is None:
            start = j
        elif not x and start is not None:
            spans.append([start, j - 1])
            start = None
    merged = []
    for s in spans:
        if merged and s[0] - merged[-1][1] - 1 < MERGE_GAP:
            merged[-1][1] = s[1]
        else:
            merged.append(s)
    return merged


def hhmm(j: int) -> str:
    m = (B0 + j) * 5
    return f"{m // 60:02d}:{m % 60:02d}"


def ramp_valid(date: str, det: str) -> bool:
    q, _ = lane_bins(date, det)
    if np.mean(~np.isnan(q)) < 0.9:
        return False
    day = q[(6 * 12 - B0):(20 * 12 - B0)]
    return bool(np.nansum(day) > 0)


def analyse_corridor(name: str, meters: list, dates: list, down_km: float | None = None) -> dict:
    cor = corridor_detectors(meters, down_km=down_km if down_km is not None else DOWN_KM.get(name, 2.0))
    sts = sorted(cor["mainline"], key=lambda s: s["km"])
    ramp_km = [r["km"] for r in cor["ramps"]]
    wed = [d for d in dates if dt.datetime.strptime(d, "%Y%m%d").weekday() == 2]
    days = {}
    for d in dates:
        sd = [(s, station_day(d, s)) for s in sts]
        days[d] = [(s, x) for s, x in sd if x["valid"]]
    # active bottlenecks per day
    act = {}
    for d, sd in days.items():
        act[d] = {}
        for (su, xu), (sdn, xd) in zip(sd[:-1], sd[1:]):
            if sdn["km"] - su["km"] > MAX_GAP_KM:
                continue
            cond = (xu["v"] < V_CONG) & ((xd["v"] - xu["v"]) >= DV)
            cond = np.nan_to_num(cond.astype(float)).astype(bool)
            ep = episodes(cond)
            if ep:
                act[d][(su["node"], sdn["node"])] = {"ep": ep, "u": su, "d": sdn, "xd": xd, "lanes_d": xd["lanes"]}
    lo, hi = -0.5, max(ramp_km) + 2.0
    cnt = {}
    for d in wed:
        for key, a in act[d].items():
            if lo <= a["u"]["km"] <= hi:
                cnt[key] = cnt.get(key, 0) + 1
    out = {"corridor": name, "route": cor["route"], "dir": cor["dir"], "meters": meters,
           "ramps": [{"label": r["label"], "km": r["km"], "storage": r["storage"]} for r in cor["ramps"]],
           "n_days": len(dates), "n_wednesdays": len(wed), "bottleneck_pair_counts_wed": {
               f"{k[0]}->{k[1]}": v for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])[:5]}}
    # B-independent items first (review fix #3): implausible speeds, C2, C3 are reported even without a bottleneck
    # Addendum A.2 (reported only): implausible free-flow speeds
    implaus = []
    for s in sts:
        ff = [np.nanmedian(x["v"][0:12]) for d in wed for s2, x in days[d] if s2["node"] == s["node"]]
        mff = float(np.nanmedian(ff)) if ff else None
        if mff is not None and not (50.0 <= mff <= 80.0):
            implaus.append({"station": s["label"] or s["node"], "km": s["km"], "median_05_06_mph": round(mff, 1)})
    out["implausible_speed_stations"] = implaus
    # C2
    rr = []
    for r in cor["ramps"]:
        res, wkb = {}, {}
        for cat in ("Queue", "Passage"):
            best = 0.0
            for det, c in r["dets"]:
                if c != cat:
                    continue
                best = max(best, float(np.mean([ramp_valid(d, det) for d in wed])))   # Wednesdays (review fix #0)
                wkb[cat] = max(wkb.get(cat, 0.0), float(np.mean([ramp_valid(d, det) for d in dates if d not in wed])))
            res[cat] = best
        rr.append({"ramp": r["label"], "queue_valid_share": res["Queue"], "passage_valid_share": res["Passage"],
                   "weekend_queue_valid_share": wkb.get("Queue"), "weekend_passage_valid_share": wkb.get("Passage"),
                   "PASS": res["Queue"] >= 0.9 and res["Passage"] >= 0.9})
    out["C2"] = {"ramps": rr, "PASS": all(x["PASS"] for x in rr)}
    # C3 (per Wednesday: the most upstream valid station)
    unc = []
    for d in wed:
        if not days[d]:
            continue
        s0, x0 = days[d][0]
        v = x0["v"][~np.isnan(x0["v"])]
        unc.append(bool(np.mean(v >= 45.0) >= 0.95) if len(v) else False)
    c3 = float(np.mean(unc)) if unc else None
    ext = corridor_detectors(meters, up_km=12.0)
    up_st = [s for s in ext["mainline"] if s["km"] <= -4.0]
    out["C3"] = {"share_uncongested_wed": c3, "PASS": c3 is not None and c3 >= 0.95,
                 "extension_stations_km_le_-4": len(up_st),
                 "extension_min_km": min((s["km"] for s in ext["mainline"]), default=None),
                 "extension_detectors": sum(len(s["dets"]) for s in up_st)}
    if not cnt:
        out["C1"] = {"PASS": False, "note": "no active bottleneck in the window"}
        return out
    B = max(cnt, key=cnt.get)
    bu = next(s for s in sts if s["node"] == B[0])
    bd = next(s for s in sts if s["node"] == B[1])
    out["B"] = {"u": bu["label"] or bu["node"], "d": bd["label"] or bd["node"], "u_km": bu["km"], "d_km": bd["km"]}
    # Addendum A.2 (reported only): ramps feeding B
    out["ramps_upstream_of_B_within_6km"] = [r["label"] for r in cor["ramps"] if bu["km"] - 6.0 <= r["km"] <= bu["km"]]
    # C1
    wed_valid = [d for d in wed if any(s["node"] == B[0] for s, _ in days[d]) and any(s["node"] == B[1] for s, _ in days[d])]
    wed_act = [d for d in wed_valid if B in act[d]]
    share = len(wed_act) / len(wed_valid) if wed_valid else None
    out["C1"] = {"valid_wed": len(wed_valid), "active_wed": len(wed_act), "share": share,
                 "PASS": share is not None and 0.30 <= share <= 0.90}
    wk = [d for d in dates if d not in wed]
    wk_valid = [d for d in wk if any(s["node"] == B[0] for s, _ in days[d]) and any(s["node"] == B[1] for s, _ in days[d])]
    out["weekend_active_share"] = (sum(B in act[d] for d in wk_valid) / len(wk_valid)) if wk_valid else None
    # C4 and reported per-episode numbers (Wednesdays)
    rs, qdis_l, cap_l, onsets, durs, am, pm, both = [], [], [], [], [], 0, 0, 0
    for d in wed_act:
        a = act[d][B]
        q = a["xd"]["q"]
        ep_am = any(e[0] < (12 * 12 - B0) for e in a["ep"])
        ep_pm = any(e[0] >= (12 * 12 - B0) for e in a["ep"])
        am += ep_am
        pm += ep_pm
        both += ep_am and ep_pm
        for e in a["ep"]:
            onsets.append(hhmm(e[0]))
            durs.append((e[1] - e[0] + 1) * 5)
        e = max(a["ep"], key=lambda e: e[1] - e[0])
        if (e[1] - e[0] + 1) * 5 < 30 or e[0] < 3:
            continue
        qpre = np.nanmean(q[e[0] - 3:e[0]])
        dis = q[e[0] + 2:e[1]]
        if len(dis) < 4 or not np.isfinite(qpre) or qpre <= 0:
            continue
        qdis = np.nanmean(dis)
        rs.append(float(qdis / qpre))
        qdis_l.append(float(qdis / a["lanes_d"]))
        pre = q[max(0, e[0] - 12):e[0]]
        if len(pre) >= 3:
            roll = np.convolve(np.nan_to_num(pre), np.ones(3) / 3, mode="valid")
            cap_l.append(float(roll.max() / a["lanes_d"]))
    med = lambda x: float(np.median(x)) if x else None
    out["C4"] = {"n_episode_days": len(rs), "median_r": med(rs), "r_iqr": [float(np.percentile(rs, 25)), float(
        np.percentile(rs, 75))] if rs else None, "PASS": len(rs) >= 5 and 0.82 <= np.median(rs) <= 0.97}
    out["reported"] = {"Q_dis_vphpl_median": med(qdis_l), "capacity_15min_vphpl_median": med(cap_l),
                       "onset_median": sorted(onsets)[len(onsets) // 2] if onsets else None,
                       "episode_min_median": med(durs), "wed_with_AM_episode": am, "wed_with_PM_episode": pm,
                       "wed_with_both": both, "share_wed_both": both / len(wed_valid) if wed_valid else None}
    # day shapes at the boundary: the most upstream station valid on >= 80 % of Wednesdays
    bnd = next((s for s in sts if np.mean([any(x["node"] == s["node"] for x, _ in days[d]) for d in wed]) >= 0.8), None)
    shapes, peak_counts = {}, {}
    tot, peak = {}, {}
    if bnd is not None:
        for d in dates:
            x = next((x for s, x in days[d] if s["node"] == bnd["node"]), None)
            if x is None:
                continue
            q15 = np.nanmean(x["q"][:NB - NB % 3].reshape(-1, 3), axis=1)
            mx = np.nanmax(q15)
            mid = np.nanmedian(q15[4:60])                    # 06:00-20:00 in 15-min bins
            npk = 0
            if mx / max(mid, 1e-9) < 1.3:
                lab = "flat"
            else:
                pk, _ = find_peaks(np.nan_to_num(q15), prominence=0.15 * mx, distance=12)
                times = [(5 * 60 + 15 * p) for p in pk]
                npk = len(pk)
                if len(pk) == 2 and min(times) < 720 <= max(times):   # protocol: two peaks (review fix #1)
                    lab = "M"
                elif len(pk) == 1:
                    lab = "^"
                else:
                    lab = "other"
            wd = dt.datetime.strptime(d, "%Y%m%d").weekday()
            grp = "wed" if wd == 2 else ("sat" if wd == 5 else "sun")
            shapes.setdefault(grp, {}).setdefault(lab, 0)
            shapes[grp][lab] += 1
            peak_counts.setdefault(grp, {}).setdefault(str(npk), 0)
            peak_counts[grp][str(npk)] += 1
            qi = x["q"].copy()                             # review fix #2: interpolate missing bins, not zeros
            ok = ~np.isnan(qi)
            qi[~ok] = np.interp(np.flatnonzero(~ok), np.flatnonzero(ok), qi[ok])
            tot[d] = float(np.sum(qi) / 12.0)
            peak[d] = float(np.max(np.convolve(qi, np.ones(12) / 12, mode="valid")))
    out["boundary_station"] = (bnd["label"] or bnd["node"], bnd["km"]) if bnd else None
    out["day_shapes"] = shapes
    out["day_peak_counts"] = peak_counts             # review fix #1: 3+-peak days stay visible ("other")
    # M-to-trapezoid descriptive (Wednesdays)
    rows = []
    for d in wed_valid:
        if d not in tot:
            continue
        dur = sum((e[1] - e[0] + 1) * 5 for e in act[d][B]["ep"]) if B in act[d] else 0
        rows.append((tot[d], peak[d], dur))
    if len(rows) >= 8:
        T = np.array(rows)
        rho_t = spearmanr(T[:, 0], T[:, 2]).statistic
        rho_p = spearmanr(T[:, 1], T[:, 2]).statistic
        qs = np.percentile(T[:, 0], [25, 50, 75])
        bins = np.digitize(T[:, 0], qs)
        table = []
        for b in range(4):
            sel = T[bins == b]
            table.append({"quartile": b + 1, "n": int(len(sel)), "total_veh_median": float(np.median(sel[:, 0])) if len(sel) else None,
                          "duration_min_median": float(np.median(sel[:, 2])) if len(sel) else None,
                          "share_any_episode": float(np.mean(sel[:, 2] > 0)) if len(sel) else None})
        out["m_to_trapezoid"] = {"n": len(rows), "spearman_total_vs_duration": float(rho_t),
                                 "spearman_peakhour_vs_duration": float(rho_p), "by_total_quartile": table}
    return out


def main(argv=None) -> int:
    """No argument: the TOP3 corridors (v1 output). '--from-bnscreen': the top 3 of the bottleneck-anchored screen
    (selection protocol v1), same criteria and choice rule, written to ..._v2.json."""
    argv = sys.argv[1:] if argv is None else argv
    dates = pass1_dates(2023)
    if "--from-bnscreen" in argv:
        bn = json.loads((OUT.parent / "day_pattern_bnscreen_v1.json").read_text())
        cors = {f"{c['route']}_{c['dir']}_{c['u_label']}".replace(" ", "").replace(".", ""): (c["meters"], c["down_km"])
                for c in bn["top3"] if c["within_cap_12000"]}       # over-cap corridors were not pulled
        over_cap = [f"{c['route']} {c['dir']} {c['u_label']} ({c['requests_104d']} requests)" for c in bn["top3"]
                    if not c["within_cap_12000"]]
        out_path = OUT.parent / "day_pattern_corridor_analysis_v2.json"
    else:
        cors = {k: (v, None) for k, v in TOP3.items()}
        over_cap = []
        out_path = OUT
    res = {"protocol": "docs/plans/day_pattern_corridor_analysis_protocol_v0.md", "dates": f"{len(dates)} days of 2023",
           "corridors": {}}
    for name, (meters, dk) in cors.items():
        res["corridors"][name] = analyse_corridor(name, meters, dates, down_km=dk)
    elig = [n for n, c in res["corridors"].items() if c.get("C1", {}).get("PASS") and c.get("C2", {}).get("PASS")
            and c.get("C4", {}).get("PASS")]

    def rank(n):
        c = res["corridors"][n]
        ext_ok = c["C3"]["PASS"] or (c["C3"]["extension_min_km"] is not None and c["C3"]["extension_min_km"] <= -10.0)
        c1 = c["C1"]                                   # exact distance from 0.5 (bn-screen review)
        return (not ext_ok, Fraction(abs(2 * c1["active_wed"] - c1["valid_wed"]), 2 * c1["valid_wed"]),
                -(c["reported"]["share_wed_both"] or 0.0))
    res["eligible"] = elig
    res["ranking"] = sorted(elig, key=rank)
    res["proposed"] = res["ranking"][0] if res["ranking"] else None
    if over_cap:
        res["not_analysed_over_cap_author_decision_pending"] = over_cap
    out_path.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({"eligible": elig, "proposed": res["proposed"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
