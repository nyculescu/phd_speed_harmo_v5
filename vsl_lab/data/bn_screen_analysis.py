"""Analysis part of the bottleneck-anchored screen (docs/plans/day_pattern_corridor_selection_protocol_v1.md)."""
from __future__ import annotations

import gzip
from fractions import Fraction
import xml.etree.ElementTree as ET

import numpy as np

from vsl_lab.data.corridor_analysis import NB, episodes, lane_bins
from vsl_lab.data.mndot import (CONFIG, DATA_ROOT, _dist, available_cached, corridor_detectors, pass1_dates,
                                screening_dates, windows)
from vsl_lab.data.bn_screen import screen_lane

V_CONG, DV, MAX_GAP_KM = 40.0, 20.0, 3.0


def freeway_corridors() -> list[dict]:
    """Ordered active r_nodes per freeway corridor, with km, mainline detectors (name, field) and metered entrances."""
    root = ET.fromstring(gzip.open(CONFIG).read())
    out = []
    for c in root.iter("corridor"):
        route = c.get("route")
        if not any(k in route for k in ("I-", "U.S.", "T.H.")) or "CD" in route:
            continue
        nodes = [n for n in c.iter("r_node") if n.get("active", "t") == "t"]
        pos = [(float(n.get("lat")), float(n.get("lon"))) for n in nodes]
        km = [0.0]
        for i in range(1, len(pos)):
            km.append(km[-1] + _dist(pos[i - 1], pos[i]))
        st, ent = [], []
        for i, n in enumerate(nodes):
            t = n.get("n_type", "Station")
            if t == "Station":
                d = [(x.get("name"), float(x.get("field", "22.0"))) for x in n.iter("detector") if x.get("category", "") == ""]
                if d:
                    st.append({"node": n.get("name"), "label": n.get("label", ""), "km": km[i], "dets": d})
            elif t == "Entrance" and n.find("meter") is not None:
                cats = {}
                for x in n.iter("detector"):
                    cats.setdefault(x.get("category", ""), []).append(x.get("name"))
                ent.append({"meter": n.find("meter").get("name"), "label": n.get("label", ""), "km": km[i], "cats": cats})
        out.append({"route": route, "dir": c.get("dir"), "stations": st, "entrances": ent})
    return out


def station_speed(date: str, st: dict):
    det = screen_lane(date, [d for d, _ in st["dets"]])
    if det is None:
        return None
    field = dict(st["dets"])[det]
    q, occ = lane_bins(date, det)
    if np.mean(~np.isnan(q)) < 0.9:
        return None
    k = occ / 100.0 * 5280.0 / field
    with np.errstate(divide="ignore", invalid="ignore"):
        v = np.where(k > 0, q / k, np.inf)
    return np.where(np.isnan(q) | np.isnan(k), np.nan, v)


def screen() -> dict:
    dates = screening_dates()
    screened = {s["node"] for w in windows() for s in w["stations"]}
    cors = freeway_corridors()
    av = {d: set(available_cached(d)) for d in dates}
    pairs = []
    for c in cors:
        sts = [s for s in c["stations"] if s["node"] in screened]
        V = {s["node"]: {d: station_speed(d, s) for d in dates} for s in sts}
        for u, dn in zip(sts[:-1], sts[1:]):
            if dn["km"] - u["km"] > MAX_GAP_KM:
                continue
            valid = act = 0
            dvs = []
            for d in dates:
                vu, vd = V[u["node"]][d], V[dn["node"]][d]
                if vu is None or vd is None:
                    continue
                valid += 1
                with np.errstate(invalid="ignore"):
                    cond = np.nan_to_num(((vu < V_CONG) & ((vd - vu) >= DV)).astype(float)).astype(bool)
                if episodes(cond):
                    act += 1
                    dd = (vd - vu)[cond]
                    dvs += [float(x) for x in dd[np.isfinite(dd)]]
            pairs.append({"route": c["route"], "dir": c["dir"], "u": u["node"], "u_label": u["label"], "km_u": u["km"],
                          "d": dn["node"], "d_label": dn["label"], "km_d": dn["km"], "valid": valid, "active": act,
                          "share": act / valid if valid else None,
                          "median_dv_mph": float(np.median(dvs)) if dvs else None})
    cand = [p for p in pairs if p["valid"] >= 15 and 0.30 <= p["share"] <= 0.90]
    # merge near-duplicates (same route/dir, u within 3 km): keep the one with most active days
    cand.sort(key=lambda p: -p["active"])
    merged = []
    for p in cand:
        if any(q["route"] == p["route"] and q["dir"] == p["dir"] and abs(q["km_u"] - p["km_u"]) <= 3.0 for q in merged):
            continue
        merged.append(p)
    feas, rejected = [], []
    cmap = {(c["route"], c["dir"]): c for c in cors}
    for p in merged:
        c = cmap[(p["route"], p["dir"])]
        why = []

        def healthy(e):
            q = [x for x in e["cats"].get("Queue", []) if sum(x in av[d] for d in dates) >= 0.9 * len(dates)]
            ps = [x for x in e["cats"].get("Passage", []) if sum(x in av[d] for d in dates) >= 0.9 * len(dates)]
            return bool(q) and bool(ps)
        rng = [e for e in c["entrances"] if p["km_u"] - 6.0 <= e["km"] <= p["km_d"]]
        good = [e for e in rng if healthy(e)]
        good.sort(key=lambda e: -e["km"])                       # nearest to d first
        if len(good) < 2:
            why.append(f"feeding ramps with healthy queue+passage: {len(good)} of {len(rng)} metered in range")
        elif p["km_d"] - good[0]["km"] > 2.0:
            why.append(f"nearest healthy feeding ramp {p['km_d'] - good[0]['km']:.2f} km upstream of d (> 2)")
        sel = sorted(good[:3], key=lambda e: e["km"])
        first_km = sel[0]["km"] if sel else p["km_u"]
        if not any(s["km"] <= first_km - 10.0 for s in c["stations"]):
            why.append("no mainline station >= 10 km upstream of the first feeding ramp")
        down = [s for s in c["stations"] if p["km_d"] < s["km"] <= p["km_d"] + 5.0]
        if len(down) < 2:
            why.append(f"only {len(down)} station(s) within 5 km downstream of d")
        rec = p | {"feeding": [(e["label"], e["meter"], round(e["km"], 2)) for e in sel],
                   "n_feeding": min(len(good), 3)}
        (rejected if why else feas).append(rec | ({"why": why} if why else {}))
    # exact distance from 0.5 (bn-screen review: float error split exact ties, so key 2 was never consulted)
    feas.sort(key=lambda p: (Fraction(abs(2 * p["active"] - p["valid"]), 2 * p["valid"]), -p["n_feeding"],
                             -(p["median_dv_mph"] or 0.0)))
    av104 = {d: set(available_cached(d)) for d in pass1_dates(2023)}
    top = []
    for p in feas[:3]:
        meters = [m for _, m, _ in p["feeding"]]
        c = cmap[(p["route"], p["dir"])]
        down = sorted([s for s in c["stations"] if s["km"] > p["km_d"]], key=lambda s: s["km"])[:2]
        down_km = (down[-1]["km"] if down else p["km_d"]) - max(km for _, _, km in p["feeding"]) + 0.01
        cd = corridor_detectors(meters, up_km=4.0, down_km=max(down_km, 0.5), exit_down_km=max(down_km, 0.5))
        dets = sorted({x[0] for g in cd["mainline"] + cd["ramps"] + cd["exits"] for x in g["dets"]})
        # exactly what the pull fetches: detectors in that day's archive list, not yet cached (bn-screen review)
        new = sum(not (DATA_ROOT / "mayfly" / d[:4] / d / f"{det}.{k}.json").exists()
                  for d in pass1_dates(2023) for det in dets if det in av104[d] for k in ("counts", "occupancy"))
        top.append(p | {"meters": meters, "down_km": round(max(down_km, 0.5), 3), "n_detectors": len(dets),
                        "requests_104d": new, "within_cap_12000": new <= 12000})
    return {"protocol": "docs/plans/day_pattern_corridor_selection_protocol_v1.md", "dates": dates,
            "n_pairs": len(pairs), "n_candidates": len(cand), "n_merged": len(merged), "n_feasible": len(feas),
            "candidates_merged": merged, "feasible": feas, "rejected": rejected, "top3": top}
