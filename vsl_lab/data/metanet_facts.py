"""U.S.169 SB METANET pre-calibration facts (protocol v3 §3.6, §3.8 steps 11-13, §5.1-§5.2 real side; binding).

python -m vsl_lab.data.metanet_facts   -> docs/lab/day_pattern/metanet_precal_facts.json (+ raw JSON on ext4)

Real data only; no model is run. Decisions use calibration days only; validation-day quantities are the real-side
minima and floors (F11), computed before any model run.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import fisher_exact

from vsl_lab.data import metanet_events as V
from vsl_lab.data import metanet_inputs as I
from vsl_lab.data.mndot import DATA_ROOT, available_cached, year_dates
from vsl_lab.plants import metanet as M

RUNS = Path("/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet")
OUT = Path(__file__).resolve().parents[2] / "docs" / "lab" / "day_pattern" / "metanet_precal_facts.json"
OFF = I.SCORE0                          # event bin 0 (05:00) = model bin 12
DOWN = {"B1": "S1140", "B2": "S1141"}   # discharge stations
UPST = {"B1": "S1773", "B2": "S1140"}   # pair upstream stations (EA-2)
EXIT_IN = {"B1": "X12", "B2": "X13"}
PAIR = {"B1": I.P1, "B2": I.P2}


def boot_ci(x, seed, n=10000, q=(2.5, 97.5)):
    x = np.asarray(x, float)
    if x.size == 0:
        return None
    rng = np.random.default_rng(seed)
    m = np.median(rng.choice(x, (n, x.size)), axis=1)
    return [float(np.percentile(m, q[0])), float(np.percentile(m, q[1]))]


# ---------------------------------------------------------------- real-side day summary (§5.1)
def day_events(d: str) -> dict:
    ep = I.event_pairs(d)
    e1, e2 = ep.get(I.P1, []), ep.get(I.P2, [])
    tc = V.censor_time(e1, e2)
    out = {"pairs": {f"{u}->{v}": e for (u, v), e in ep.items() if e}, "B1": e1, "B2": e2, "censor": tc}
    for k, eps in (("B1", e1), ("B2", e2)):
        if not eps:
            out[k + "_long"] = None
            continue
        if k == "B1":
            durs = [V.censored_duration(e, tc.get(i)) for i, e in enumerate(eps)]
        else:
            durs = [(e[1] - e[0] + 1) * 5 for e in eps]
        i = int(np.argmax(durs))
        q = I.event_station(d, DOWN[k])["q"]
        cap = tc.get(i) if k == "B1" else None
        c = V.c4(q, eps[i], 2, end_cap=cap)
        out[k + "_long"] = {"ep": eps[i], "dur_min": durs[i], "censored": cap is not None, "c4": c,
                            "heavy": bool(durs[i] >= 30 and c is not None)}
    starts = [(e[0], 0, "B1") for e in e1] + [(e[0], 1, "B2") for e in e2]
    out["first"] = min(starts)[2] if starts else None
    b = out["first"]
    if b and out[b + "_long"] and out[b + "_long"]["heavy"]:
        s = out[b + "_long"]["ep"][0]
        other = e2 if b == "B1" else e1
        out["heavy_first"] = not any(o[0] <= s - 12 <= o[1] for o in other)
    else:
        out["heavy_first"] = False
    return out


def merge_section(d: str, k: str, ev: dict) -> dict | None:
    lg = ev[k + "_long"]
    if not lg or not lg["c4"]:
        return None
    a, b = lg["c4"]["window"]
    q = I.event_station(d, DOWN[k])["q"]
    x = I.element_flow(d, EXIT_IN[k], "input")
    if not x["valid"]:
        return None
    xs = x["q"][OFF:OFF + len(q)]
    dis = float(np.nanmean((q[a:b] + xs[a:b]) / 2.0))
    s = lg["ep"][0]
    pre = (q[max(0, s - 12):s] + xs[max(0, s - 12):s]) / 2.0
    roll = np.convolve(np.nan_to_num(pre), np.ones(3) / 3, mode="valid")
    return {"discharge": dis, "pre_max15": float(roll.max()) if roll.size else None,
            "exit_in_discharge": float(np.nanmean(xs[a:b]))}


def s1_real(d: str, k: str, ev: dict):
    lg = ev[k + "_long"]
    if not lg or not lg["c4"]:
        return None
    s, e = lg["ep"]
    q = I.event_station(d, DOWN[k])["q"]
    seg = np.nan_to_num(q[max(0, s - 12):e + 1])
    roll = np.convolve(seg, np.ones(3) / 3, mode="valid")
    return float(roll.max() / lg["c4"]["Q_dis"]) if roll.size else None


# ---------------------------------------------------------------- F11 minima (§5.2)
def minima(days: list[str], evs: dict) -> dict:
    n_val = len(days)
    nA = {k: sum(bool(evs[d][k]) for d in days) for k in ("B1", "B2")}
    nH = {k: sum(bool(evs[d][k + "_long"] and evs[d][k + "_long"]["heavy"]) for d in days) for k in ("B1", "B2")}
    nHf = sum(bool(evs[d]["heavy_first"]) for d in days)
    nHb = sum(bool(evs[d]["B1_long"] and evs[d]["B1_long"]["heavy"] and evs[d]["B2_long"] and evs[d]["B2_long"]["heavy"])
              for d in days)
    nH1u = sum(bool(evs[d]["B1_long"] and evs[d]["B1_long"]["heavy"] and not evs[d]["B1_long"]["censored"]) for d in days)
    nA_any = sum(bool(evs[d]["B1"] or evs[d]["B2"]) for d in days)
    fails = []
    if n_val < 16:
        fails.append(f"n_val {n_val} < 16")
    for k in ("B1", "B2"):
        if nA[k] < 8:
            fails.append(f"n_A,{k[-1]} {nA[k]} < 8")
        if nH[k] < 6:
            fails.append(f"n_H,{k[-1]} {nH[k]} < 6")
    if nHf < 6:
        fails.append(f"n_H,first {nHf} < 6")
    return {"n_val": n_val, "n_A": nA_any, "n_A,1": nA["B1"], "n_A,2": nA["B2"], "n_H,1": nH["B1"], "n_H,2": nH["B2"],
            "n_H,first": nHf, "n_H,both": nHb, "n_H,1u": nH1u, "fails": fails, "met": not fails}


def floors(days, evs):
    out = {}
    for k in ("B1", "B2"):
        r = [evs[d][k + "_long"]["c4"]["r"] for d in days if evs[d][k + "_long"] and evs[d][k + "_long"]["heavy"]]
        ci = boot_ci(r, 7190097)
        out[k] = {"n": len(r), "median_r": float(np.median(r)) if r else None, "L_r": ci[0] if ci else None, "ci": ci}
    return out


def flow_null(cal: list[str], val: list[str], part1: dict) -> dict:
    """N2_q: per station and 5-min bin the median calibration-day flow, scored on the validation days' S_q,d."""
    sl, cs, unrel = part1["speed_lanes"], part1["c_s"], set(part1["unreliable"])
    prof = {}
    for sid in I.INTERIOR:
        qs = [I.station_fit(d, sid, "scored", sl)["q"] for d in cal]
        prof[sid] = np.nanmedian(np.array(qs), axis=0)
    scores = []
    for d in val:
        ft = I.fit_targets(d, sl, cs, unrel)
        xh, x, m = [], [], []
        for sid, s in ft["stations"].items():
            if sid not in prof:
                continue
            xh.append(prof[sid])
            x.append(s["q"])
            m.append(s["q_mask"])
        v = V.nrmse(np.concatenate(xh), np.concatenate(x), np.concatenate(m))
        if v is not None:
            scores.append(v)
    return {"median_nrmse_q": float(np.median(scores)) if scores else None, "n_days": len(scores)}


# ---------------------------------------------------------------- F16 downstream capacity check (§1.7)
def f16(cal_use: list[str], part1: dict, q_ref: float) -> dict:
    net = M.build_network("model")
    sources = part1["sources"]
    A = []
    for d in cal_use:
        so = I.station_fit(d, "S1141", "input")
        cb = I.CLASS_B["E15"]
        e15 = I.balance(d, cb[0], cb[1], cb[2], cb[3], sources)
        if not (so["flow_valid"] and e15["valid"]):
            continue
        arr = so["q"] + e15["q"]
        roll = np.convolve(np.nan_to_num(arr[OFF:]), np.ones(3) / 3, mode="valid")
        A.append(roll.max())
    A_med = float(np.median(A)) if A else None
    cells = {}
    for i in range(32, net.N):                       # cells 33-36 (all receive OSR + E15 at their upstream end)
        R = A_med / (net.lam[i] * q_ref) if A_med else None
        cells[f"cell {i + 1}"] = {"A_veh_h": A_med, "lambda": int(net.lam[i]), "R": R, "flag": bool(R and R > 1.10)}
    flagged = any(c["flag"] for c in cells.values())
    return {"Q_ref_vphpl": q_ref, "n_days": len(A), "cells": cells, "flagged": flagged,
            "lane_check": "not performed (author decision D3.7: A1 (ii) no lane check)",
            "resolution": "step (b): separate capacity group G4 on cells 33-36" if flagged else "none (all R_i <= 1.10)"}


# ---------------------------------------------------------------- other facts
def f3(days_by_set: dict, part1_excl: dict) -> dict:
    out = {}
    for name, days in days_by_set.items():
        for k in ("B1", "B2"):
            a = sum(1 for d in days if part1_excl[d]["E2"] and part1_excl[d][k])
            b = sum(1 for d in days if part1_excl[d]["E2"] and not part1_excl[d][k])
            c = sum(1 for d in days if not part1_excl[d]["E2"] and part1_excl[d][k])
            e = sum(1 for d in days if not part1_excl[d]["E2"] and not part1_excl[d][k])
            p = fisher_exact([[a, b], [c, e]])[1] if (a + b) and (c + e) else None
            out[f"{name}_{k}"] = {"congested_active": a, "congested_inactive": b, "free_active": c, "free_inactive": e,
                                  "fisher_p": p}
    return out


def f7(cal_use: list[str], evs: dict) -> dict:
    """§1.6 mechanism diagnostic per bottleneck (exit occupancy around onsets)."""
    out = {}
    for k, det in (("B1", "5427"), ("B2", "5432")):
        act = [d for d in cal_use if evs[d][k]]
        inact = [d for d in cal_use if not evs[d][k]]

        def occ(d):
            l = I.fit_lane(d, det, "input")
            return l["occ"][OFF:] if l["valid"] else None
        ctrl_days = [o for o in (occ(d) for d in inact) if o is not None]
        if len(ctrl_days) >= 4:
            ctrl = float(np.nanmedian([np.nanmedian(o[(15 - 5) * 12:(19 - 5) * 12]) for o in ctrl_days]))
        else:
            ctrl = float(np.nanmedian([np.nanmedian(o[(13 - 5) * 12:(15 - 5) * 12]) for o in
                                       (occ(d) for d in cal_use) if o is not None]))
        led, n = 0, 0
        for d in act:
            o = occ(d)
            if o is None:
                continue
            n += 1
            t0 = evs[d][k][0][0]
            seg = o[max(0, t0 - 3):t0 + 7]
            hit = (seg >= 2 * ctrl) & (seg >= 0.20)
            run = first = 0
            first_i = None
            for j, h in enumerate(hit):
                run = run + 1 if h else 0
                if run >= 3 and first_i is None:
                    first_i = j - 2
            if first_i is not None and (max(0, t0 - 3) + first_i) <= t0 + 1:
                led += 1
        share = led / n if n else None
        outcome = "INCONCLUSIVE" if n < 6 else ("EXIT" if share >= 0.5 else ("base" if share <= 0.2 else "INCONCLUSIVE"))
        out[k] = {"exit_detector": det, "control_occ": ctrl, "n_days": n, "exit_led": led, "share": share,
                  "outcome": outcome}
    return out


def f10(cal_use: list[str], evs: dict, part1: dict) -> dict:
    counts = {}
    for d in cal_use:
        for p, e in evs[d]["pairs"].items():
            counts[p] = counts.get(p, 0) + 1
    cs = part1["c_s"]
    a = {d: bool(evs[d]["B1"]) for d in cal_use}
    b = {}
    for d in cal_use:
        su, sd = I.event_station(d, "S1773"), I.event_station(d, "S1140")
        vu = su["v"] * cs["S1773"]["c_s"]
        vd = sd["v"] * cs["S1140"]["c_s"]
        ep = V.pair_episodes({"S1773": vu, "S1140": vd}, {"S1773": 2.893, "S1140": 6.038}, {"S1773": True, "S1140": True})
        b[d] = bool(ep.get(("S1773", "S1140")))
    D = [d for d in cal_use if a[d] or b[d]]
    dis = sum(a[d] != b[d] for d in D)
    option_c = bool(D) and dis / len(D) > 0.25
    hidden = []
    for d in cal_use:
        v = I.event_station(d, "S1773")["v"]
        run = best = 0
        for x in np.nan_to_num(v, nan=99.0) < 40.0:
            run = run + 1 if x else 0
            best = max(best, run)
        if best >= 12 and not evs[d]["B1"] and not evs[d]["B2"]:
            hidden.append(d)
    cens_eps = sum(len(evs[d]["censor"]) for d in cal_use)
    cens_heavy = sum(bool(evs[d]["B1_long"] and evs[d]["B1_long"]["heavy"] and evs[d]["B1_long"]["censored"])
                     for d in cal_use)
    return {"pair_day_counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])),
            "share_active": {k: float(np.mean([bool(evs[d][k]) for d in cal_use])) for k in ("B1", "B2")},
            "first_location": {k: sum(evs[d]["first"] == k for d in cal_use) for k in ("B1", "B2")},
            "B1_raw_days": sum(a.values()), "B1_scaled_days": sum(b.values()), "disagree": dis, "D": len(D),
            "option_c": option_c, "highwood_slow_no_episode": hidden, "censored_episodes": cens_eps,
            "censored_heavy_days": cens_heavy}


def f12(cal_use: list[str], part1: dict, evs: dict) -> dict:
    out = {}
    pm = slice((15 - 4) * 12, (19 - 4) * 12)
    near = {"E7": "S459", "E8": "S460", "E10": "S1772", "E11": "S1772"}
    for m, sid in near.items():
        sh, q45 = [], []
        for d in cal_use:
            x = I.element_flow(d, m, "input")
            b0 = I.station_fit(d, "S453", "input")
            if not (x["valid"] and b0["flow_valid"]):
                continue
            tot = np.nansum(b0["q"][pm]) + sum(np.nansum(I.element_flow(d, e[0], "input", part1["sources"].get(e[0]))["q"][pm])
                                                for e in M.ENTRANCES if e[0] != "E15")
            sh.append(np.nansum(x["q"][pm]) / tot)
            if evs[d]["B1"] or evs[d]["B2"]:
                v = I.event_station(d, sid)["v"]
                eps = (evs[d]["B1"] or []) + (evs[d]["B2"] or [])
                binsm = np.zeros(len(v), bool)
                for s, e in eps:
                    binsm[s:e + 1] = True
                q45.append(bool(np.nanmean(v[binsm] < 45.0) >= 0.30) if binsm.any() else False)
        out[m] = {"share_pm_inflow": float(np.median(sh)) if sh else None,
                  "share_active_days_queued": float(np.mean(q45)) if q45 else None}
    return out


def f14(days: list[str], part1: dict) -> dict:
    dets = sorted({d for s in M.STATIONS for d in s[3]} | {e[5][0] for e in M.ENTRANCES if e[5]}
                  | {x[3] for x in M.EXITS if x[3]} | {q for qs in I.QUEUE_DETS.values() for q in qs})
    pres = {d: sum(d in set(available_cached(day)) for day in days) for d in dets}
    return {"n_days": len(days), "absent_all_days": [d for d, n in pres.items() if n == 0],
            "absent_some_days": {d: len(days) - n for d, n in pres.items() if 0 < n < len(days)}}


def f9(cal_use: list[str], evs: dict) -> dict:
    """§5.4 P7b rule, real side, on calibration heavy days: most upstream station of the unbroken congested run."""
    order = sorted(I.EVENT_STATIONS, key=lambda s: I.ST[s]["km"])
    ext = []
    for d in cal_use:
        if not any(evs[d][k + "_long"] and evs[d][k + "_long"]["heavy"] for k in ("B1", "B2")):
            continue
        start = "S1773" if evs[d]["B1"] else "S1140"
        win = np.zeros(216, bool)
        for s, e in (evs[d]["B1"] or []) + (evs[d]["B2"] or []):
            win[s:e + 1] = True
        idx = order.index(start)
        extent = start
        for sid in reversed(order[:idx + 1]):
            st = I.event_station(d, sid)
            if not st["valid"]:
                continue
            slow = np.nan_to_num(st["v"], nan=99.0) < 40.0
            run, ok = 0, False
            for j in range(216):
                run = run + 1 if slow[j] else 0
                if run >= 3 and win[max(0, j - run + 1):j + 1].any():
                    ok = True
                    break
            if not ok:
                break
            extent = sid
        ext.append({"date": d, "start": start, "extent": extent, "km": I.ST[extent]["km"]})
    kms = [x["km"] for x in ext]
    return {"days": ext, "median_extent_km": float(np.median(kms)) if kms else None,
            "share_reaching_I494_merges": float(np.mean([k <= 1.667 for k in kms])) if kms else None}


def f13(days: list[str]) -> dict:
    from vsl_lab.data.corridor_analysis import station_day
    rn = M.load_rnodes()
    out = {}
    for lab in ("N of I-394", "S of I-394"):
        n = next(x for x in rn if x["type"] == "Station" and x["label"] == lab)
        st = {"dets": [(d[0], None, d[2]) for d in n["dets"] if d[1] == ""]}
        cong, mins = [], []
        for d in days:
            x = station_day(d, st)
            if not x["valid"]:
                continue
            pm = x["v"][(15 - 5) * 12:(19 - 5) * 12]
            cong.append(bool(np.nanmean(x["v"] < 45.0) > 0.05))
            mins.append(float(np.nanmean(pm < 45.0)))
        out[lab] = {"n_days": len(cong), "share_days_congested": float(np.mean(cong)) if cong else None,
                    "share_pm_minutes_below_45mph": float(np.mean(mins)) if mins else None}
    return out


# ---------------------------------------------------------------- main
# ---------------------------------------------------------------- protocol v4 recompute list (§A6 step 3)
def _series(d: str, eid: str, sources: dict) -> dict:
    """Replayed series of a ramp element (class B from its balance, class M as replayed)."""
    if eid in I.CLASS_B:
        cb = I.CLASS_B[eid]
        return I.balance(d, cb[0], cb[1], cb[2], cb[3], sources)
    return I.element_flow(d, eid, "input", sources.get(eid))


def conservation_flow(x_km: float, st_km: float, q_st: np.ndarray, elems: list) -> np.ndarray:
    """Flow just downstream of km x (elements exactly at x are upstream of the point) from a station's flow and the
    ramp series between them. elems: (km, sign, series), sign +1 entrance, -1 exit. Pure function (test 23)."""
    xe = x_km + 1e-6
    q = np.array(q_st, float)
    for km, sign, ser in elems:
        if st_km < xe and st_km < km < xe:
            q = q + sign * np.asarray(ser, float)
        elif st_km > xe and xe < km < st_km:
            q = q - sign * np.asarray(ser, float)
    return q


def arriving_flow(d: str, x_km: float, part1: dict, station: str | None = None):
    """v3 §1.7 A_i: arriving flow just downstream of km x from the nearest flow-valid station and the replayed ramp
    series (no storage term). Returns (series on 228 bins, station id) or None."""
    sources = part1["sources"]
    xe = x_km + 1e-6
    cands = sorted(M.STATIONS, key=lambda st: abs(st[1] - x_km))
    if station is not None:                                   # §A4 (ii) names the source station explicitly
        cands = [st for st in M.STATIONS if st[0] == station]
    for sid, skm, *_ in cands:
        st = I.station_fit(d, sid, "input")
        if not st["flow_valid"]:
            continue
        lo, hi = sorted((skm, xe))
        between = [(e[1], e[0], +1) for e in M.ENTRANCES if lo < e[1] < hi] + \
                  [(x[1], x[0], -1) for x in M.EXITS if lo < x[1] < hi]
        series = []
        for km, eid, sign in between:
            f = _series(d, eid, sources)
            if not f["valid"]:
                break
            series.append((km, sign, np.nan_to_num(np.asarray(f["q"], float))))
        else:
            return conservation_flow(x_km, skm, st["q"], series), sid
    return None


def _ratio_cells(cal_use: list[str], part1: dict, q_ref: float, net, cells: list[int], anchor: dict | None = None) -> dict:
    out = {}
    for i in cells:
        ents = [e for e in net.entrances if e["cell"] == i]
        x = max(e["km"] for e in ents) if ents else float(net.km_from[i])
        A = []
        for d in cal_use:
            r = arriving_flow(d, x, part1, (anchor or {}).get(i))
            if r is None:
                continue
            roll = np.convolve(np.nan_to_num(r[0][OFF:]), np.ones(3) / 3, mode="valid")
            A.append(float(roll.max()))
        A_med = float(np.median(A)) if A else None
        R = A_med / (net.lam[i] * q_ref) if A_med else None
        out[f"cell {i + 1}"] = {"point_km": x, "anchor_station": (anchor or {}).get(i, "nearest flow-valid"), "A_veh_h": A_med, "n_days": len(A), "lambda": int(net.lam[i]),
                                "R": R, "over_1.10": bool(R and R > 1.10)}
    return out


def f16_cells(net) -> list:
    """§A4 (ii): the F16 domain from the build: the cells read by Anderson Lakes Pkwy and Pioneer Tr, and every cell
    downstream of B2's last scaled cell (0-based)."""
    sc = {st["id"]: st["cell"] for st in net.stations}
    return [sc["S1147"], sc["S1140"]] + list(range(net.b2_cells[-1] + 1, net.N))


def main_v4() -> int:
    """Protocol v4 §A6 step 3: the recompute list only -> docs/lab/day_pattern/metanet_v4_precal_facts.json. Reused
    facts are read from the v3 file, never written."""
    import subprocess
    from vsl_lab.jobs import metanet_calibrate as C
    p1 = C.part1()
    v3 = json.loads(OUT.read_text())
    blob = subprocess.run(["git", "-C", str(C.REPO), "hash-object", str(OUT)], capture_output=True, text=True).stdout.strip()
    net = M.build_network("v4")
    cal_use = p1["usable"]["calibration"]
    q_ref = max(x for x in (v3["F8"]["B1"]["Q_dis_per_lane_median"], v3["F8"]["B2"]["Q_dis_per_lane_median"]) if x)
    facts = {"protocol": "docs/plans/day_pattern_metanet_protocol_v4.md", "protocol_version": "v4",
             "v3_facts_git_blob": blob, "v3_facts_path": str(OUT.relative_to(C.REPO)),
             "F1": {"variant": net.variant, "N": net.N, "km_from": net.km_from.round(4).tolist(),
                    "km_to": net.km_to.round(4).tolist(), "lanes": net.lam.astype(int).tolist(),
                    "group": [int(g) + 1 for g in net.group], "merge_log": net.merge_log,
                    "b1_cells": [i + 1 for i in net.b1_cells], "b2_cells": [i + 1 for i in net.b2_cells],
                    "head1": net.head1 + 1, "phi_cell": net.phi_cell + 1,
                    "entrances": {e["id"]: {"cell": e["cell"] + 1, "merging": e["merging"]} for e in net.entrances},
                    "exits": {x["id"]: x["cell"] + 1 for x in net.exits},
                    "stations": {st["id"]: {"cell": st["cell"] + 1, "corr_entr": st["corr_entr"],
                                            "corr_exit": st["corr_exit"]} for st in net.stations}},
             "F16": {"report_only": True, "Q_ref_vphpl": q_ref, "n_cal_days": len(cal_use),
                     "cells": _ratio_cells(cal_use, p1, q_ref, net, f16_cells(net),
                                           anchor={i: "S1141" for i in range(net.b2_cells[-1] + 1, net.N)}),
                     "step": "(b), adopted without condition (§A4 (i))"},
             "F14_G1G2_ratios": {"report_only": True,
                                 "cells": _ratio_cells(cal_use, p1, q_ref, net, [i for i in range(net.N) if net.group[i] in (0, 1)])},
             "F7_cells_restated": {"X12": next(x["cell"] + 1 for x in net.exits if x["id"] == "X12"),
                                   "X13": next(x["cell"] + 1 for x in net.exits if x["id"] == "X13"),
                                   "outcome": {k: v3["F7"][k]["outcome"] for k in ("B1", "B2")}}}
    C.FACTS_V4.write_text(json.dumps(facts, indent=1, default=str))
    print(json.dumps({"F16": {k: round(v["R"], 3) if v["R"] else None for k, v in facts["F16"]["cells"].items()},
                      "F14_over_1.10": [k for k, v in facts["F14_G1G2_ratios"]["cells"].items() if v["over_1.10"]]}))
    return 0


def main() -> int:
    raise SystemExit("protocol v3 facts are frozen (v4 §A9: v3 paths are read-only); run main_v4 via --v4")


def main_v3_frozen() -> int:
    raise SystemExit("protocol v3 facts are frozen (code at tag metanet-v3-stop)")
    p1 = json.loads((RUNS / "precal_part1.json").read_text())
    cal, val = p1["split"]["calibration"], p1["split"]["validation"]
    cal_use, val_use = p1["usable"]["calibration"], p1["usable"]["validation"]
    facts = {"protocol": "docs/plans/day_pattern_metanet_protocol_v3.md", "part1_raw": str(RUNS / "precal_part1.json")}
    evs = {d: day_events(d) for d in cal + val}
    # F11 on the validation Wednesdays (step 12)
    m_wed = minima(val_use, evs)
    facts["F11_wednesdays"] = m_wed
    ext = {}
    final_val = list(val_use)
    if not m_wed["met"]:
        # step 13: extension on the pre-fetched 2023 Tuesdays and Thursdays, references frozen
        tt = [d for d in year_dates(2023) if dt.datetime.strptime(d, "%Y%m%d").weekday() in (1, 3)]
        present = sum((DATA_ROOT / "mayfly" / "2023" / d / "_detectors.json").exists() for d in tt)
        net = M.build_network("model")
        ext = I.exclusions_frozen(tt, p1, net)
        for d in tt:
            evs[d] = day_events(d)
        ext_use = [d for d in tt if ext[d]["usable"]]
        final_val = val_use + ext_use
        facts["extension"] = {"days": len(tt), "detector_lists_present": present, "usable": len(ext_use),
                              "exclusions": {k: sum(bool(ext[d][k]) for d in tt) for k in ("E1-B", "E2", "E3", "E4")}
                                            | {"E1": sum(bool(ext[d]["E1"]) for d in tt)},
                              "usable_days": ext_use}
    m_fin = minima(final_val, evs)
    facts["F11"] = m_fin | {"validation_days": final_val, "floors": floors(final_val, evs),
                            "flow_null_N2_q": flow_null(cal_use, final_val, p1),
                            "P8_tolerance": max(2, int(np.ceil(0.10 * len(final_val))))}
    facts["INCONCLUSIVE_on_wednesdays"] = not m_wed["met"]
    facts["outcome_minima"] = "met" if m_fin["met"] else "INCONCLUSIVE (final)"
    # F8 (calibration)
    f8 = {}
    for k in ("B1", "B2"):
        heavy = [d for d in cal_use if evs[d][k + "_long"] and evs[d][k + "_long"]["heavy"]]
        act = [d for d in cal_use if evs[d][k + "_long"] and evs[d][k + "_long"]["c4"]]
        r_h = [evs[d][k + "_long"]["c4"]["r"] for d in heavy]
        r_a = [evs[d][k + "_long"]["c4"]["r"] for d in act]
        qd = [evs[d][k + "_long"]["c4"]["Q_dis_per_lane"] for d in heavy]
        ms = [merge_section(d, k, evs[d]) for d in heavy]
        s1 = [s1_real(d, k, evs[d]) for d in heavy if evs[d]["first"] == k]
        f8[k] = {"n_heavy": len(heavy), "median_r": float(np.median(r_h)) if r_h else None,
                 "iqr_r": [float(np.percentile(r_h, 25)), float(np.percentile(r_h, 75))] if r_h else None,
                 "ci_r": boot_ci(r_h, 7190094), "share_r_ge_1": float(np.mean(np.array(r_h) >= 1)) if r_h else None,
                 "all_active_median_r": float(np.median(r_a)) if r_a else None,
                 "Q_dis_per_lane_median": float(np.median(qd)) if qd else None,
                 "S1_first_active_median": float(np.median([x for x in s1 if x is not None])) if s1 else None,
                 "merge_section": {d: m for d, m in zip(heavy, ms) if m}}
    both = [d for d in cal_use if all(evs[d][k + "_long"] and evs[d][k + "_long"]["heavy"] for k in ("B1", "B2"))]
    rat = {}
    for key in ("discharge", "pre_max15"):
        rr = [f8["B2"]["merge_section"][d][key] / f8["B1"]["merge_section"][d][key] for d in both
              if d in f8["B1"]["merge_section"] and d in f8["B2"]["merge_section"]]
        rat[key] = {"n": len(rr), "median": float(np.median(rr)) if rr else None, "ci": boot_ci(rr, 7190094),
                    "share_gt_1": float(np.mean(np.array(rr) > 1)) if rr else None}
    f8["merge_ratio_B2_over_B1"] = rat
    facts["F8"] = f8
    qref = max(x for x in (f8["B1"]["Q_dis_per_lane_median"], f8["B2"]["Q_dis_per_lane_median"]) if x)
    facts["F16"] = f16(cal_use, p1, qref)
    facts["F2"] = {"calibration": {"usable": len(cal_use), "of": len(cal)}, "validation_wednesdays": {"usable": len(val_use), "of": len(val)},
                   "exclusions": {d: {k: v for k, v in p1["exclusions"][d].items()} for d in cal + val}}
    facts["F3"] = f3({"calibration": cal, "validation": val}, p1["exclusions"])
    facts["F4"] = p1["ramp_rule"]
    facts["F5"] = p1["flow_reliability"]
    facts["F6"] = {"lane_screen": p1["lane_screen"], "c_s": p1["c_s"]}
    facts["F7"] = f7(cal_use, evs)
    facts["F10"] = f10(cal_use, evs, p1)
    facts["F9"] = f9(cal_use, evs)
    facts["F12"] = f12(cal_use, p1, evs)
    facts["F13"] = f13(cal + val)
    facts["F14"] = f14(cal + val, p1)
    facts["F15"] = {"E4_days": [d for d in cal + val if p1["exclusions"][d]["E4"] in (True, "True")],
                    "holiday_adjacent": ["20230104", "20230705", "20231122", "20231227"]}
    facts["events_summary"] = {d: {"B1": evs[d]["B1"], "B2": evs[d]["B2"], "first": evs[d]["first"],
                                   "heavy": {k: bool(evs[d][k + "_long"] and evs[d][k + "_long"]["heavy"]) for k in ("B1", "B2")}}
                               for d in cal_use + final_val}
    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "precal_facts_full.json").write_text(json.dumps(facts, indent=1, default=str))
    OUT.write_text(json.dumps(facts, indent=1, default=str))
    print(json.dumps({"F11_wed": {k: m_wed[k] for k in ("n_val", "fails")}, "F11_final": {k: m_fin[k] for k in
                      ("n_val", "n_A,1", "n_A,2", "n_H,1", "n_H,2", "n_H,first", "n_H,both", "met")},
                      "F16": facts["F16"]["resolution"], "F10_option_c": facts["F10"]["option_c"],
                      "F7": {k: v["outcome"] for k, v in facts["F7"].items()}}))
    return 0


if __name__ == "__main__":
    sys.exit(main_v4() if "--v4" in sys.argv else main())
