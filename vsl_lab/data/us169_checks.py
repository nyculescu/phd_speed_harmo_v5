"""U.S.169 SB data facts for the METANET protocol v1 (design-review points 2-5; inspection disclosed in the protocol).

python -m vsl_lab.data.us169_checks   -> docs/lab/day_pattern/us169_data_facts.json
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

from vsl_lab.data.corridor_analysis import B0, NB, episodes, lane_bins, station_day
from vsl_lab.data.mndot import US169_METERS, corridor_detectors, pass1_dates

OUT = Path(__file__).resolve().parents[2] / "docs" / "lab" / "day_pattern" / "us169_data_facts.json"
PM = slice(15 * 12 - B0, 19 * 12 - B0)          # 15:00-19:00


def daily(det: str, date: str, sl=slice(None)) -> float | None:
    q, _ = lane_bins(date, det)
    q = q[sl]
    return float(np.nansum(q) / 12.0) if np.mean(~np.isnan(q)) >= 0.9 else None


def main() -> int:
    cd = corridor_detectors(US169_METERS, up_km=12.0, down_km=5.35, exit_down_km=5.35, all_entrances=True)
    st = {s["label"]: s for s in cd["mainline"]}
    ramps = {r["label"]: r for r in cd["ramps"]}
    exits = {e["label"]: e for e in cd["exits"]}
    days = pass1_dates(2023)
    wed = [d for d in days if dt.datetime.strptime(d, "%Y%m%d").weekday() == 2]
    out = {"note": "inspection for protocol design (review wf_2f6737c1-079); disclosed in protocol v1"}

    # (2) Pioneer Tr ramp: passage / green vs the mainline balance across the merge (PM 15-19 h)
    pt = ramps["Pioneer Tr"]
    pas = next(d for d, c in pt["dets"] if c == "Passage")
    grn = next((d for d, c in pt["dets"] if c == "Green"), None)
    rows = []
    for d in wed:
        u, dn = station_day(d, st["Pioneer Tr"]), station_day(d, st["Old Shakopee Rd"])
        if not (u["valid"] and dn["valid"]):
            continue
        ex = [daily(x[0], d, PM) for x in exits.get("Old Shakopee Rd", {"dets": []})["dets"]]
        bal = float(np.nansum(dn["q"][PM]) / 12 - np.nansum(u["q"][PM]) / 12 + sum(x for x in ex if x is not None))
        p_ = daily(pas, d, PM)
        g_ = daily(grn, d, PM) if grn else None
        rows.append({"date": d, "balance_entry_veh": bal, "passage_veh": p_, "green_veh": g_})
    rat = [r["passage_veh"] / r["balance_entry_veh"] for r in rows if r["passage_veh"] and r["balance_entry_veh"] > 50]
    out["pioneer_tr_ramp"] = {"n_days": len(rows), "median_passage_over_balance_PM": float(np.median(rat)) if rat else None,
                              "median_green_over_balance_PM": float(np.median([r["green_veh"] / r["balance_entry_veh"]
                                                                               for r in rows if r["green_veh"] and r["balance_entry_veh"] > 50]))
                              if any(r["green_veh"] for r in rows) else None,
                              "note": "balance = q(Old Shakopee) - q(Pioneer Tr station) + Old Shakopee exit; Old Shakopee "
                                      "entrance (no detector, downstream of station?) may bias it"}

    # (3) upstream boundary candidates: share of Wednesdays uncongested (>= 45 mph in >= 95 % of bins) per station
    bnd = {}
    for s in sorted(cd["mainline"], key=lambda s: s["km"])[:8]:
        ok = []
        for d in wed:
            x = station_day(d, s)
            if x["valid"]:
                v = x["v"][~np.isnan(x["v"])]
                ok.append(bool(np.mean(v >= 45.0) >= 0.95))
        bnd[f"{s['km']:.2f} {s['label']}"] = {"valid_wed": len(ok), "share_uncongested": float(np.mean(ok)) if ok else None}
    out["upstream_boundary_candidates"] = bnd

    # (4) I-494 merges: share of the PM inflow between Valley View Rd and Pioneer Tr; speed at the merge area on B days
    sh = []
    for d in wed:
        m = [daily(x[0], d, PM) for lab in ("I-494 WB", "I-494 EB") for x in ramps[lab]["dets"]]
        oth = [daily(x[0], d, PM) for lab in ("Marth Rd", "Anderson Lakes Pkwy", "Pioneer Tr") for x in ramps[lab]["dets"]
               if x[1] == "Passage"]
        up = station_day(d, st["Valley View Rd"])
        if None in m or None in oth or not up["valid"]:
            continue
        tot = float(np.nansum(up["q"][PM]) / 12) + sum(m) + sum(oth)
        sh.append(sum(m) / tot)
    out["i494_merge_share_of_PM_inflow"] = {"n_days": len(sh), "median": float(np.median(sh)) if sh else None}
    cong = []
    for d in wed:
        a, b = station_day(d, st["Highwood Ave"]), station_day(d, st["Pioneer Tr"])
        if a["valid"] and b["valid"]:
            cong.append((bool(np.nanmin(b["v"][PM]) < 40), bool(np.nanmin(a["v"][PM]) < 40)))
    bd = [c for c in cong if c[0]]
    out["queue_reaches_highwood_when_pioneer_congested"] = {"n_pioneer_cong_days": len(bd),
                                                             "share": float(np.mean([c[1] for c in bd])) if bd else None}

    # (5) capacity-drop r per Wednesday (corridor-protocol estimator) by calendar order halves
    r_by = {}
    for i, d in enumerate(wed):
        u, dn = station_day(d, st["Pioneer Tr"]), station_day(d, st["Old Shakopee Rd"])
        if not (u["valid"] and dn["valid"]):
            continue
        with np.errstate(invalid="ignore"):
            cond = np.nan_to_num(((u["v"] < 40) & ((dn["v"] - u["v"]) >= 20)).astype(float)).astype(bool)
        ep = episodes(cond)
        if not ep:
            continue
        e = max(ep, key=lambda e: e[1] - e[0])
        if (e[1] - e[0] + 1) * 5 < 30 or e[0] < 3:
            continue
        qpre, dis = np.nanmean(dn["q"][e[0] - 3:e[0]]), dn["q"][e[0] + 2:e[1]]
        if len(dis) >= 4 and qpre > 0:
            r_by.setdefault("first_half" if i < len(wed) // 2 else "second_half", []).append(float(np.nanmean(dis) / qpre))
            r_by.setdefault("odd_index_1based" if (i + 1) % 2 else "even_index_1based", []).append(float(np.nanmean(dis) / qpre))
    out["drop_r_by_split"] = {k: {"n": len(v), "median": float(np.median(v))} for k, v in r_by.items()}
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "note"})[:1500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
