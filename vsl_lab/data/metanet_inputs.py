"""U.S.169 SB METANET data layer (protocol v3 §3; binding). Part 1: §3.8 steps 1-10.

Two cleaning layers:
- EVENT layer = the committed corridor estimator (corridor_analysis.station_day / episodes), all lanes, raw mph,
  with amendment EA-2 (Anderson Lakes Pkwy removed; named pair P_1 = (S of Highwood Ave, Pioneer Tr) at 3.145 km).
- FIT layer = 30-s gaps <= 15 min interpolated, role-dependent validity (input / scored), speed lanes from the
  lane screen, speeds scaled by c_s; feeds the model inputs and the NRMSE terms.

All decisions (lane screen, ramp sources, flow reliability, c_s, E4 reference) use calibration days only.
"""
from __future__ import annotations

import datetime as dt
import functools
import json
from itertools import groupby
from pathlib import Path

import numpy as np

from vsl_lab.data.corridor_analysis import episodes, station_day
from vsl_lab.data.mndot import DATA_ROOT, available_cached
from vsl_lab.plants import metanet as M

MPH = 1.609344
S30_PER_DAY = 2880
S30_0400, S30_0500, S30_0600, S30_2000, S30_2300 = 480, 600, 720, 2400, 2760
BIN0, NBIN = 48, M.N_BINS            # model bins: 5-min index 48 (04:00) .. 276 (23:00)
SCORE0 = M.SCORE_FROM_BIN             # 12 -> 05:00
GAP_MAX_S30 = 30                      # 15 min
FIELD = None                          # detector field lengths, loaded lazily

ST = {s[0]: {"id": s[0], "km": s[1], "label": s[2], "dets": s[3]} for s in M.STATIONS}
EVENT_STATIONS = [s for s in ST if s != "S1147"]          # EA-2
P1, P2 = ("S1773", "S1140"), ("S1140", "S1141")
E_BY_ID = {e[0]: e for e in M.ENTRANCES}
X_BY_ID = {x[0]: x for x in M.EXITS}
QUEUE_DETS = {"E1": ["3685"], "E2": ["3678", "5318"], "E3": ["3679"], "E4": ["3673", "3674", "3675"],
              "E5": ["3669", "3670"], "E6": ["2000"], "E9": ["3663"], "E12": ["7103"], "E13": ["5426"], "E14": ["5431"]}
# §3.3.2 ramp links: ramp -> (u, d, measured exits in link, other measured entrances in link); E13 has a fallback
RAMP_LINKS = {"E1": ("S453", "S455", ["X1", "X2"], []), "E2": ("S455", "S456", [], []),
              "E3": ("S456", "S457", ["X3"], []), "E4": ("S457", "S458", ["X4"], []),
              "E5": ("S458", "S459", ["X5"], []), "E9": ("S462", "S1770", [], []),
              "E12": ("S1772", "S1773", [], ["E10", "E11"]), "E13": ("S1147", "S1140", ["X12"], []),
              "E14": ("S1140", "S1141", ["X13"], [])}
RAMP_LINK_E13_FALLBACK = ("S1773", "S1140", ["X11", "X12"], [])
# §3.3.4 class-B elements: element -> (u, d, other elements (kind, id) in the link, unknown kind)
CLASS_B = {"X67": ("S459", "S460", [("E", "E6"), ("E", "E7")], "exit"),
           "X9": ("S1770", "S1771", [], "exit"),
           "X10": ("S1771", "S1772", [], "exit"),
           "E15": ("S1141", "S1610", [("X", "X14"), ("X", "X15")], "entrance")}
# §3.3.5 / §1.2 split-ratio references: exit -> list of forms in preference order
#   ("down", station, extra exits added) : F = q_d + e + sum(extra)
#   ("up", station, extra entrances added, extra exits subtracted): F = q_u + sum(entr) - sum(exits)
BETA_REF = {"X1": [("down", "S455", ["X2"])], "X2": [("down", "S455", [])], "X3": [("down", "S457", [])],
            "X4": [("down", "S458", [])], "X5": [("down", "S459", [])],
            "X67": [("up", "S459", ["E6"], [])], "X8": [("down", "S462", [])], "X9": [("down", "S1771", [])],
            "X10": [("down", "S1772", [])], "X11": [("down", "S1147", []), ("up", "S1773", [], [])],
            "X12": [("down", "S1140", [])], "X13": [("down", "S1141", [])],
            "X14": [("down", "S1610", ["X15"])], "X15": [("down", "S1610", [])]}


# ---------------------------------------------------------------- §3.1 split
def wednesdays_2023() -> list[str]:
    d0 = dt.date(2023, 1, 1)
    days = [d0 + dt.timedelta(k) for k in range(365)]
    return [d.strftime("%Y%m%d") for d in days if d.weekday() == 2]


def split_days() -> tuple[list[str], list[str]]:
    w = [dt.datetime.strptime(d, "%Y%m%d").date() for d in wednesdays_2023()]
    cal, val = [], []
    for _, g in groupby(w, key=lambda d: d.month):
        for j, d in enumerate(g):
            (cal if j % 2 == 0 else val).append(d.strftime("%Y%m%d"))
    return cal, val


# ---------------------------------------------------------------- raw data
def fields() -> dict:
    global FIELD
    if FIELD is None:
        FIELD = M.field_lengths(M.load_rnodes())
    return FIELD


@functools.lru_cache(maxsize=20000)
def raw(date: str, det: str):
    """(counts30, occ30) float arrays with NaN, or None if the file is missing/null or the detector is absent."""
    out = []
    for kind in ("counts", "occupancy"):
        f = DATA_ROOT / "mayfly" / date[:4] / date / f"{det}.{kind}.json"
        if not f.exists():
            return None
        t = f.read_text()
        if t == "null":
            return None
        a = np.array([np.nan if x is None else float(x) for x in json.loads(t)])
        if a.size != S30_PER_DAY:
            return None
        out.append(a)
    return out[0], out[1]


# ---------------------------------------------------------------- fit layer (§3.2.2)
def _runs(mask):
    """(start, end_exclusive) runs of True."""
    m = np.concatenate([[False], mask, [False]]).astype(int)
    d = np.diff(m)
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


@functools.lru_cache(maxsize=20000)
def fit_lane(date: str, det: str, role: str) -> dict:
    """role 'input' (gap > 15 min in 04-23 h invalidates the lane-day; 90 % rule over 04-23 h) or 'scored'
    (a long gap invalidates only its bins; 90 % rule over 05-23 h). Returns 5-min q (veh/h), occ (frac),
    valid-bin mask over the 228 model bins, and the lane-day validity."""
    r = raw(date, det)
    bad = {"valid": False, "q": np.full(NBIN, np.nan), "occ": np.full(NBIN, np.nan), "bins": np.zeros(NBIN, bool)}
    if r is None:
        return bad
    c, o = r[0].copy(), r[1].copy()
    miss = np.isnan(c) | np.isnan(o)
    long_gap = np.zeros(S30_PER_DAY, bool)
    for s, e in _runs(miss):
        if e - s <= GAP_MAX_S30 and s > 0 and e < S30_PER_DAY:
            for a in (c, o):
                a[s:e] = np.interp(np.arange(s, e), [s - 1, e], [a[s - 1], a[e]])
        else:
            long_gap[s:e] = True
    if role == "input" and long_gap[S30_0400:S30_2300].any():
        return bad
    q, occ, ok = np.full(NBIN, np.nan), np.full(NBIN, np.nan), np.zeros(NBIN, bool)
    for j in range(NBIN):
        s = (BIN0 + j) * 10
        cs, os_ = c[s:s + 10], o[s:s + 10]
        n = int((~np.isnan(cs) & ~np.isnan(os_)).sum())
        if n >= 9 and not long_gap[s:s + 10].any():
            q[j] = 12.0 * np.nansum(cs) * 10.0 / n
            occ[j] = np.nanmean(os_) / 100.0
            ok[j] = True
    win = slice(0, NBIN) if role == "input" else slice(SCORE0, NBIN)
    dead = not np.nansum(c[S30_0600:S30_2000]) > 0
    valid = bool(ok[win].mean() >= 0.9 and not dead)
    return {"valid": valid, "q": q, "occ": occ, "bins": ok}


def station_fit(date: str, sid: str, role: str, speed_lanes: dict | None = None) -> dict:
    """Flow (all lanes; flow-valid only if every lane is valid) and speed (km/h, unscaled) over the valid speed
    lanes. speed_lanes: sid -> list of lane detectors kept by the lane screen (None = all lanes)."""
    dets = ST[sid]["dets"]
    lanes = {d: fit_lane(date, d, role) for d in dets}
    flow_valid = all(l["valid"] for l in lanes.values())
    q = np.sum([lanes[d]["q"] for d in dets], axis=0) if flow_valid else np.full(NBIN, np.nan)
    sl = [d for d in (speed_lanes.get(sid, dets) if speed_lanes else dets) if lanes[d]["valid"]]
    if sl:
        Q = np.sum([lanes[d]["q"] for d in sl], axis=0)
        K = np.sum([lanes[d]["occ"] * 5280.0 / fields()[d] for d in sl], axis=0)      # veh/mile
        with np.errstate(invalid="ignore", divide="ignore"):
            v = np.where(K > 0, Q / K, np.nan) * MPH
    else:
        v = np.full(NBIN, np.nan)
    K_all = (np.sum([lanes[d]["occ"] * 5280.0 / fields()[d] for d in dets], axis=0) / MPH
             if flow_valid else np.full(NBIN, np.nan))                                # veh/km, all lanes
    return {"flow_valid": flow_valid, "speed_valid": bool(sl), "q": q, "v": v, "K": K_all, "speed_lanes": sl}


def element_flow(date: str, eid: str, role: str = "input", source: str | None = None) -> dict:
    """Measured entrance/exit 5-min flow (veh/h): entrances by their replay source ('passage' default or 'queue');
    exits by their Exit detector. Class-B elements are not measured here."""
    if eid in X_BY_ID:
        det = X_BY_ID[eid][3]
        dets = [] if det is None else [det]
    else:
        dets = QUEUE_DETS[eid] if source == "queue" else E_BY_ID[eid][5]
    if not dets:
        return {"valid": False, "q": np.full(NBIN, np.nan)}
    ls = [fit_lane(date, d, role) for d in dets]
    if not all(l["valid"] for l in ls):
        return {"valid": False, "q": np.full(NBIN, np.nan)}
    return {"valid": True, "q": np.sum([l["q"] for l in ls], axis=0)}


# ---------------------------------------------------------------- event layer (§3.2.1, EA-2)
@functools.lru_cache(maxsize=5000)
def event_station(date: str, sid: str) -> dict:
    st = {"dets": [(d, None, fields()[d]) for d in ST[sid]["dets"]]}
    x = station_day(date, st)
    return {"valid": x["valid"], "v": x["v"], "q": x["q"]}


def event_pairs(date: str, speeds: dict | None = None, valid: dict | None = None) -> dict:
    """Episodes per pair on the EA-2 event layer. speeds/valid override the real ones (model side, already
    converted to detector scale and masked). Returns {(u, d): episodes}."""
    vs = speeds or {s: event_station(date, s)["v"] for s in EVENT_STATIONS}
    ok = valid or {s: event_station(date, s)["valid"] for s in EVENT_STATIONS}
    seq = [s for s in sorted(EVENT_STATIONS, key=lambda s: ST[s]["km"]) if ok[s]]
    out = {}
    for u, d in zip(seq[:-1], seq[1:]):
        if ST[d]["km"] - ST[u]["km"] > 3.0 + 1e-9 and (u, d) != P1:
            continue
        with np.errstate(invalid="ignore"):
            cond = np.nan_to_num(((vs[u] < 40.0) & ((vs[d] - vs[u]) >= 20.0)).astype(float)).astype(bool)
        out[(u, d)] = episodes(cond)
    return out


# ---------------------------------------------------------------- step 2: lane screen (§3.2.3)
def lane_screen(cal: list[str]) -> dict:
    """Per mainline lane: median 05:00-06:00 5-min speed (volume > 0), pooled over its valid calibration lane-days.
    Excluded if outside 50-80 mph or < 100 bins. Returns {sid: kept lanes}, plus the table."""
    kept, table = {}, {}
    for sid, s in ST.items():
        kept[sid] = []
        for d in s["dets"]:
            vals = []
            for day in cal:
                l = fit_lane(day, d, "scored")
                if not l["valid"]:
                    continue
                q, occ = l["q"][SCORE0:SCORE0 + 12], l["occ"][SCORE0:SCORE0 + 12]      # 05:00-06:00
                with np.errstate(invalid="ignore", divide="ignore"):
                    v = np.where((q > 0) & (occ > 0), q / (occ * 5280.0 / fields()[d]), np.nan)
                vals += [x for x in v if np.isfinite(x)]
            med = float(np.median(vals)) if vals else None
            ok = med is not None and len(vals) >= 100 and 50.0 <= med <= 80.0
            table[d] = {"station": sid, "median_mph": med, "n_bins": len(vals), "kept": ok, "field_ft": fields()[d]}
            if ok:
                kept[sid].append(d)
    return {"kept": kept, "table": table}


# ---------------------------------------------------------------- 15-min balances (§3.3.4)
def _to15(x):
    return np.nanmean(x.reshape(-1, 3), axis=1)


def balance(date: str, u: str, d: str, others: list, unknown: str, sources: dict | None = None) -> dict:
    """15-min balance for one unknown element on link u -> d (fit layer, input role), held over 3 bins."""
    su, sd = station_fit(date, u, "input"), station_fit(date, d, "input")
    if not (su["flow_valid"] and sd["flow_valid"]):
        return {"valid": False}
    E, X = np.zeros(NBIN), np.zeros(NBIN)
    for kind, eid in others:
        f = element_flow(date, eid, "input", (sources or {}).get(eid))
        if not f["valid"]:
            return {"valid": False}
        if kind == "E":
            E += f["q"]
        else:
            X += f["q"]
    ell = abs(ST[d]["km"] - ST[u]["km"])
    N = ell * (su["K"] + sd["K"]) / 2.0                    # vehicles (5-min)
    Nb = N.reshape(-1, 3)
    dNdt = (Nb[:, -1] - Nb[:, 0]) / 0.25                   # veh/h over the 15-min bin
    qu, qd, E15, X15 = _to15(su["q"]), _to15(sd["q"]), _to15(E), _to15(X)
    if unknown == "entrance":
        y = qd + X15 - qu - E15 + dNdt
    else:
        y = qu + E15 - qd - X15 - dNdt
    clipped = np.maximum(-y, 0.0)
    y = np.maximum(y, 0.0)
    tot = np.nansum(y) * 0.25
    return {"valid": True, "q": np.repeat(y, 3), "clip_share": float(np.nansum(clipped) * 0.25 / max(tot, 1.0)),
            "storage_share": float(np.nansum(np.abs(dNdt)[np.abs(dNdt) > 0.1 * np.abs(y)]) * 0.25 / max(tot, 1.0))}


# ---------------------------------------------------------------- step 4: ramp rule (§3.3.2)
def ramp_rule(cal: list[str]) -> dict:
    out = {}
    for r, link in RAMP_LINKS.items():
        rec = {"ratios": [], "closable_days": 0}
        usable_q = all(any(raw(day, q) is not None for day in cal) for q in QUEUE_DETS[r])
        for day in cal:
            lk = link
            if r == "E13" and not station_fit(day, "S1147", "input")["flow_valid"]:
                lk = RAMP_LINK_E13_FALLBACK
            u, d, xs, es = lk
            others = [("X", x) for x in xs] + [("E", e) for e in es]
            bal = balance(day, u, d, others, "entrance")
            pas = element_flow(day, r, "input", "passage")
            if not (bal["valid"] and pas["valid"]):
                continue
            rec["closable_days"] += 1
            qq = element_flow(day, r, "input", "queue") if usable_q else {"valid": False}
            su = station_fit(day, u, "input")
            inflow = np.nansum(su["q"][SCORE0:]) + np.nansum(pas["q"][SCORE0:])
            row = {}
            for wname, w in (("all", slice(SCORE0, NBIN)), ("pm", slice((15 - 4) * 12, (19 - 4) * 12))):
                B = np.nansum(bal["q"][w])
                row[f"pas_{wname}"] = np.nansum(pas["q"][w]) / B if B > 0 else np.nan
                row[f"que_{wname}"] = np.nansum(qq["q"][w]) / B if (qq["valid"] and B > 0) else np.nan
            row["gap_share"] = abs(np.nansum(pas["q"][SCORE0:]) - np.nansum(bal["q"][SCORE0:])) / max(inflow, 1.0)
            rec["ratios"].append(row)
        rr = rec["ratios"]

        def med(k):
            v = [x[k] for x in rr if np.isfinite(x[k])]
            return float(np.median(np.abs(np.array(v) - 1.0))) if v else np.nan
        rec["med_abs_pas"] = {w: med(f"pas_{w}") for w in ("all", "pm")}
        rec["med_abs_que"] = {w: med(f"que_{w}") for w in ("all", "pm")}
        rec["med_gap_share"] = float(np.median([x["gap_share"] for x in rr])) if rr else np.nan
        switch = (usable_q and rec["closable_days"] >= 8
                  and all(rec["med_abs_que"][w] <= 0.05 for w in ("all", "pm"))
                  and any(rec["med_abs_pas"][w] > 0.10 for w in ("all", "pm")) and rec["med_gap_share"] > 0.01)
        rec["usable_queue"] = usable_q
        rec["source"] = "queue" if switch else "passage"
        rec["status"] = "switched" if switch else ("unchecked" if rec["closable_days"] < 8 else "kept")
        del rec["ratios"]
        out[r] = rec
    out["E6"] = {"source": "passage", "status": "unchecked (two undetected exits in its link)"}
    return out


def sources_of(rule: dict) -> dict:
    return {r: v["source"] for r, v in rule.items()}


# ---------------------------------------------------------------- split ratios (§3.3.5)
def split_ratios(date: str, sources: dict, unreliable: set) -> dict:
    """beta per exit (228 bins) or invalid. Class-B exits from their balance."""
    out = {}
    for x, forms in BETA_REF.items():
        if X_BY_ID[x][3] is None:
            cb = CLASS_B[x]
            e = balance(date, cb[0], cb[1], cb[2], cb[3], sources)
            if not e["valid"]:
                out[x] = {"valid": False}
                continue
            eq = e["q"]
        else:
            ef = element_flow(date, x, "input")
            if not ef["valid"]:
                out[x] = {"valid": False}
                continue
            eq = ef["q"]
        chosen = None
        cands = []
        for f in forms:
            s = station_fit(date, f[1], "input")
            if not s["flow_valid"]:
                continue
            cands.append((f, s))
        pref = [c for c in cands if c[0][1] not in unreliable] or cands
        if not pref:
            out[x] = {"valid": False}
            continue
        f, s = pref[0]
        if f[0] == "down":
            F = s["q"] + eq + sum(element_flow(date, k, "input")["q"] if X_BY_ID[k][3] is not None else
                                  balance(date, *CLASS_B[k][:2], CLASS_B[k][2], CLASS_B[k][3], sources)["q"] for k in f[2])
        else:
            F = s["q"] + sum(element_flow(date, k, "input", sources.get(k))["q"] for k in f[2]) \
                - sum(element_flow(date, k, "input")["q"] for k in f[3])
        if X_BY_ID[x][3] is None:
            F = np.repeat(_to15(F), 3)
        with np.errstate(invalid="ignore", divide="ignore"):
            b = np.clip(eq / F, 0.0, 1.0)
        bs = np.convolve(np.nan_to_num(b), np.ones(3) / 3, mode="same")
        for j in range(NBIN):
            if not (F[j] >= 300.0) and j > 0:
                bs[j] = bs[j - 1]
        out[x] = {"valid": True, "beta": bs, "ref": f[1], "form": f[0], "flagged_unreliable": f[1] in unreliable,
                  "check": float(abs(np.nansum(bs * F) - np.nansum(eq)) / max(np.nansum(eq), 1.0))}
    return out


# ---------------------------------------------------------------- steps 5-6: conservation (§3.4)
def _closed_links(date: str, sources: dict) -> list:
    """Station-to-station links between consecutive stations with every element class M; residual statistics."""
    sts = sorted(ST, key=lambda s: ST[s]["km"])
    out = []
    for u, d in zip(sts[:-1], sts[1:]):
        lo, hi = ST[u]["km"], ST[d]["km"]
        els = [("E", e[0]) for e in M.ENTRANCES if lo < e[1] <= hi] + [("X", x[0]) for x in M.EXITS if lo < x[1] <= hi]
        if any((k == "X" and X_BY_ID[i][3] is None) or i == "E15" for k, i in els):
            continue                                             # closed by a class-B element: not checked
        su, sd = station_fit(date, u, "input"), station_fit(date, d, "input")
        if not (su["flow_valid"] and sd["flow_valid"]):
            continue
        fl = [(k, element_flow(date, i, "input", sources.get(i))) for k, i in els]
        if not all(f["valid"] for _, f in fl):
            continue
        w = slice(SCORE0, NBIN)
        inflow = np.nansum(su["q"][w]) + sum(np.nansum(f["q"][w]) for k, f in fl if k == "E")
        outflow = np.nansum(sd["q"][w]) + sum(np.nansum(f["q"][w]) for k, f in fl if k == "X")
        out.append({"u": u, "d": d, "e_signed": (inflow - outflow) / inflow, "e": abs(inflow - outflow) / inflow})
    return out


def flow_reliability(cal: list[str], sources: dict) -> dict:
    links = {}
    for day in cal:
        for l in _closed_links(day, sources):
            links.setdefault((l["u"], l["d"]), []).append((day, l["e_signed"]))
    unreliable, shared = set(), {}
    # shared-station test
    for (u, d), rows in links.items():
        nxt = [k for k in links if k[0] == d]
        if not nxt:
            continue
        r2 = dict(links[nxt[0]])
        both = [(e1, r2[day]) for day, e1 in rows if day in r2]
        if len(both) < 8:
            shared[d] = {"testable": False, "n": len(both)}
            continue
        hit = [np.sign(a) != np.sign(b) and abs(a) > 0.01 and abs(b) > 0.01 and 0.5 <= abs(a) / abs(b) <= 2.0
               for a, b in both]
        frac = float(np.mean(hit))
        shared[d] = {"testable": True, "n": len(both), "share": frac, "unreliable": frac > 0.5}
        if frac > 0.5:
            unreliable.add(d)
    # detector-fault rule
    systematic = {}
    for (u, d), rows in links.items():
        es = [abs(e) for _, e in rows]
        frac = float(np.mean([e > 0.03 for e in es]))
        systematic[f"{u}->{d}"] = {"n_closed": len(es), "share_gt_3pct": frac, "median_e": float(np.median(es)),
                                   "systematic": frac > 0.20}
        if frac > 0.20:
            unreliable.add(d)
    return {"unreliable": sorted(unreliable), "shared": shared, "links": systematic}


# ---------------------------------------------------------------- c_s (§3.2.4)
def station_scaling(cal_days: list[str], speed_lanes: dict) -> dict:
    groups = {}
    for sid, s in ST.items():
        g = "G1" if s["km"] < 0 else ("G2" if s["km"] < 3.751 else "G3")
        groups.setdefault(g, []).append(sid)
    m_s, m_s_all = {}, {}
    for sid in ST:
        if sid == "S453":
            continue
        meds, meds_all = [], []
        for day in cal_days:
            x = station_fit(day, sid, "scored", speed_lanes)
            if x["speed_valid"]:
                v = x["v"][SCORE0:SCORE0 + 12]
                if np.isfinite(v).any():
                    meds.append(np.nanmedian(v) / MPH)
            y = event_station(day, sid)
            if y["valid"]:
                v2 = y["v"][0:12]                       # event arrays start at 05:00 (corridor estimator)
                if np.isfinite(v2).any():
                    meds_all.append(np.nanmedian(v2))
        m_s[sid] = float(np.median(meds)) if meds else np.nan
        m_s_all[sid] = float(np.median(meds_all)) if meds_all else np.nan
    full = {sid for sid in ST if set(speed_lanes.get(sid, [])) == set(ST[sid]["dets"])}
    grp = {sid: g for g, sids in groups.items() for sid in sids if sid != "S453"}
    from vsl_lab.data.metanet_events import scale_table
    c = scale_table({sid: m_s[sid] for sid in grp}, grp, full)
    for sid in c:
        c[sid]["m_s_all_lanes"] = m_s_all[sid]
    return c


# ---------------------------------------------------------------- exclusions (§3.5)
def e1b(date: str) -> bool:
    return not (event_station(date, "S1773")["valid"] and event_station(date, "S1140")["valid"]
                and event_station(date, "S1141")["valid"])


def e2(date: str) -> bool:
    x = event_station(date, "S453")
    v = x["v"][np.isfinite(x["v"])]                     # event arrays cover 05:00-23:00
    return (not x["valid"]) or bool(np.mean(v < 45.0) > 0.05) if v.size else True


def e3(date: str) -> bool:
    x = event_station(date, "S1610")
    v = x["v"]
    run, best = 0, 0
    for b in np.nan_to_num(v, nan=99.0) < 45.0:
        run = run + 1 if b else 0
        best = max(best, run)
    if best >= 3:
        return True
    ep = event_pairs(date)
    return bool(ep.get(("S1141", "S1610")))


def real_status(date: str) -> dict:
    ep = event_pairs(date)
    return {"B1": bool(ep.get(P1)), "B2": bool(ep.get(P2)), "episodes": {f"{u}->{d}": e for (u, d), e in ep.items() if e}}


# ---------------------------------------------------------------- inputs and fit targets for one day
INTERIOR = [s for s in sorted(ST, key=lambda s: ST[s]["km"]) if s not in ("S453", "S1610")]
FLOW_CLOSED_BY_B = {"S460": "X67", "S1771": "X9", "S1772": "X10", "S1610": "E15"}
Q_A = ["S1770", "S1771", "S1772", "S1773", "S1147", "S1140", "S1141"]


def model_inputs(date: str, sources: dict, unreliable: set, net: M.Net) -> dict:
    """Replay inputs (veh/h on the 228 bins) in net.entrances / net.exits order, plus validity and diagnostics."""
    bad = []
    b0 = station_fit(date, "S453", "input")
    if not b0["flow_valid"]:
        bad.append("boundary S453")
    d_o, clip = [], {}
    for e in net.entrances:
        if e["id"] == "E15":
            cb = CLASS_B["E15"]
            f = balance(date, cb[0], cb[1], cb[2], cb[3], sources)
            if f["valid"]:
                clip["E15"] = f["clip_share"]
        else:
            f = element_flow(date, e["id"], "input", sources.get(e["id"]))
        if not f["valid"]:
            bad.append(f"entrance {e['id']}")
            f = {"q": np.zeros(NBIN)}
        d_o.append(np.nan_to_num(f["q"]))
    sr = split_ratios(date, sources, unreliable)
    beta = []
    for x in net.exits:
        r = sr[x["id"]]
        if not r["valid"]:
            bad.append(f"exit {x['id']}")
            beta.append(np.zeros(NBIN))
        else:
            beta.append(r["beta"])
    for x in ("X67", "X9", "X10"):
        cb = CLASS_B[x]
        f = balance(date, cb[0], cb[1], cb[2], cb[3], sources)
        if f["valid"]:
            clip[x] = f["clip_share"]
    return {"valid": not bad, "why": bad, "d0": np.nan_to_num(b0["q"]), "d_o": np.array(d_o), "beta": np.array(beta),
            "class_b_clip": clip, "beta_meta": {k: {kk: v[kk] for kk in ("ref", "form", "flagged_unreliable", "check")}
                                                for k, v in sr.items() if v["valid"]}}


def congestion_window(date: str) -> np.ndarray:
    """W_d over the 228 model bins: 15:00-19:00 plus [onset - 30, end + 30 min] of every real B1/B2 episode."""
    w = np.zeros(NBIN, bool)
    w[(15 - 4) * 12:(19 - 4) * 12] = True
    ep = event_pairs(date)
    for pair in (P1, P2):
        for s, e in ep.get(pair, []):
            a, b = SCORE0 + s - 6, SCORE0 + e + 6            # event bins start at 05:00 = model bin 12
            w[max(a, 0):min(b + 1, NBIN)] = True
    return w


def fit_targets(date: str, speed_lanes: dict, cs: dict, unreliable: set) -> dict:
    """Real fit-layer series and the S_q / S_v / S_c memberships (§4.2) for one day (scored role)."""
    W = congestion_window(date)
    out = {"W": W, "stations": {}}
    for sid in INTERIOR + ["S1610"]:
        x = station_fit(date, sid, "scored", speed_lanes)
        c = cs.get(sid, {})
        dropped = c.get("dropped", False)
        v = x["v"] * c.get("c_s", np.nan) if x["speed_valid"] and not dropped else np.full(NBIN, np.nan)
        in_sv = x["speed_valid"] and not dropped
        q_mask = np.zeros(NBIN, bool)
        if x["flow_valid"] and sid in INTERIOR and sid not in unreliable:
            if sid not in FLOW_CLOSED_BY_B:
                q_mask[SCORE0:] = True
            elif sid in ("S1771", "S1772"):
                q_mask = W.copy()
                q_mask[:SCORE0] = False
        q_mask &= np.isfinite(x["q"])
        v_mask = np.zeros(NBIN, bool)
        if in_sv:
            v_mask[SCORE0:] = True
            v_mask &= np.isfinite(v)
        c_mask = v_mask & W if sid in Q_A else np.zeros(NBIN, bool)
        out["stations"][sid] = {"q": x["q"], "v": v, "q_mask": q_mask, "v_mask": v_mask, "c_mask": c_mask}
    return out


# ---------------------------------------------------------------- E1 completion and E4
def e1(date: str, mi: dict, speed_lanes: dict, cs: dict, unreliable: set, sources: dict) -> list:
    why = list(mi["why"])
    sv = 0
    for sid in INTERIOR:
        x = station_fit(date, sid, "scored", speed_lanes)
        sv += bool(x["speed_valid"] and not cs.get(sid, {}).get("dropped", False))
    if sv < 0.8 * len(INTERIOR):
        why.append(f"speed-valid interior stations {sv}/{len(INTERIOR)}")
    for k, v in mi["class_b_clip"].items():
        if v > 0.02:
            why.append(f"class-B clip {k} {v:.3f}")
    for l in _closed_links(date, sources):
        if l["u"] in unreliable or l["d"] in unreliable:
            continue
        if l["e"] > 0.05:
            why.append(f"link {l['u']}->{l['d']} e={l['e']:.3f}")
    if not event_station(date, "S1610")["valid"]:
        why.append("T.H.101 event-invalid")
    return why


def ffree_speed(date: str, sid: str, speed_lanes: dict):
    """Median free-flow speed (mph): 06-20 h bins with occupancy < 10 % and flow <= 1,200 veh/h/lane."""
    x = station_fit(date, sid, "scored", speed_lanes)
    if not x["speed_valid"]:
        return None
    lanes = [fit_lane(date, d, "scored") for d in x["speed_lanes"]]
    occ = np.nanmean([l["occ"] for l in lanes], axis=0)
    qpl = x["q"] / len(ST[sid]["dets"]) if x["flow_valid"] else np.nansum([l["q"] for l in lanes], axis=0) / len(lanes)
    w = slice((6 - 4) * 12, (20 - 4) * 12)
    m = (occ[w] < 0.10) & (qpl[w] <= 1200.0) & np.isfinite(x["v"][w])
    return float(np.median(x["v"][w][m]) / MPH) if m.sum() >= 10 else None


# ---------------------------------------------------------------- orchestration: §3.8 steps 1-10
def run_part1(out_path: Path | None = None) -> dict:
    cal, val = split_days()
    days = cal + val
    net = M.build_network("model")
    res = {"split": {"calibration": cal, "validation": val}}
    # step 2: lane screen
    ls = lane_screen(cal)
    speed_lanes = ls["kept"]
    res["lane_screen"] = ls["table"]
    # step 3: event-layer validity, E1-B, E2, E3 (all days)
    ev = {d: {"E1-B": e1b(d), "E2": e2(d), "E3": e3(d)} for d in days}
    pass13 = [d for d in cal if not any(ev[d].values())]
    # step 4: ramp rule
    rule = ramp_rule(pass13)
    sources = sources_of(rule)
    res["ramp_rule"] = rule
    # steps 5-6: shared-station test and detector-fault classification
    rel = flow_reliability(pass13, sources)
    unreliable = set(rel["unreliable"])
    res["flow_reliability"] = rel
    # step 7: c_s on calibration days passing 1-3 and the E1 data checks other than the speed-valid share
    pre = {d: model_inputs(d, sources, unreliable, net) for d in days}
    cs_days = [d for d in pass13 if pre[d]["valid"]]
    cs = station_scaling(cs_days, speed_lanes)
    res["c_s"] = cs
    # step 8: E1 on all days
    excl = {}
    for d in days:
        why = e1(d, pre[d], speed_lanes, cs, unreliable, sources)
        excl[d] = {"E1": why, **{k: v for k, v in ev[d].items()}}
    # step 9: E4 with the reference over calibration days passing 1-8
    pass18 = [d for d in cal if not excl[d]["E1"] and not any(excl[d][k] for k in ("E1-B", "E2", "E3"))]
    ref = {}
    for sid in INTERIOR:
        vals = [ffree_speed(d, sid, speed_lanes) for d in pass18]
        vals = [v for v in vals if v is not None]
        ref[sid] = float(np.median(vals)) if vals else None
    for d in days:
        drops = []
        for sid in INTERIOR:
            if ref[sid] is None:
                continue
            v = ffree_speed(d, sid, speed_lanes)
            if v is not None:
                drops.append(v <= ref[sid] - 8.0)
        excl[d]["E4"] = bool(drops) and float(np.mean(drops)) >= 0.5
    status = {d: real_status(d) for d in days}

    def usable(d):
        x = excl[d]
        return not x["E1"] and not x["E1-B"] and not x["E2"] and not x["E3"] and not x["E4"]
    res["exclusions"] = {d: {"E1": excl[d]["E1"], "E1-B": excl[d]["E1-B"], "E2": excl[d]["E2"], "E3": excl[d]["E3"],
                             "E4": excl[d]["E4"], "usable": usable(d), "B1": status[d]["B1"], "B2": status[d]["B2"]}
                         for d in days}
    res["usable"] = {"calibration": [d for d in cal if usable(d)], "validation": [d for d in val if usable(d)]}
    # step 10: stop rules
    stop = []
    if len(res["usable"]["calibration"]) < 18:
        stop.append(f"usable calibration days {len(res['usable']['calibration'])} < 18")
    for name, ds in (("calibration", cal), ("validation", val)):
        for k in ("B1", "B2"):
            act = [d for d in ds if status[d][k]]
            rm = [d for d in act if excl[d]["E2"]]
            if act and len(rm) > len(act) / 3:
                stop.append(f"E2 removes {len(rm)}/{len(act)} {k}-active {name} days")
        for k in ("E3", "E4"):
            n = sum(bool(excl[d][k]) for d in ds)
            if n > 0.25 * len(ds):
                stop.append(f"{k} removes {n}/{len(ds)} {name} days")
    res["stop_rules"] = stop
    res["sources"] = sources
    res["speed_lanes"] = speed_lanes
    res["unreliable"] = sorted(unreliable)
    if out_path:
        out_path.write_text(json.dumps(res, indent=1, default=lambda o: float(o) if isinstance(o, np.floating) else str(o)))
    return res
