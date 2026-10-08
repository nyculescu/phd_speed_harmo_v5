"""Hidden-demand check before a METANET v5 (pre-registration docs/lab/day_pattern/demand_check_prereg.md, D4.12).
Data only, calibration days only, no model fit.

python -m vsl_lab.jobs.metanet_demand_check     # -> docs/lab/day_pattern/demand_check.{json,md}
"""
from __future__ import annotations

import json
import sys

import numpy as np

from vsl_lab.data import metanet_facts as F
from vsl_lab.data import metanet_inputs as I
from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import metanet_gate as G
from vsl_lab.jobs import metanet_postcal as Q
from vsl_lab.plants import metanet as M

OUT = C.REPO / "docs" / "lab" / "day_pattern"
F2F = {"E7": "S459", "E8": "S460", "E10": "S1772", "E11": "S1772"}   # v3 §3.3.3: nearest event-valid station upstream
CTRL = ["E9", "E12", "E13", "E14"]
EV0 = M.SCORE_FROM_BIN


def queued_bins(d: str, sid: str) -> np.ndarray:
    """228-bin mask: the station's event-layer speed below 45 mph (event series start at 05:00)."""
    v = I.event_station(d, sid)["v"]
    m = np.zeros(M.N_BINS, bool)
    with np.errstate(invalid="ignore"):
        m[EV0:EV0 + len(v)] = np.nan_to_num(v, nan=99.0) < 45.0
    return m


def rnl(d_o_day: np.ndarray, j: int, P: np.ndarray, q: np.ndarray) -> np.ndarray:
    """v3 §3.3.3: in queued bins, s_m,d * P_m(t); s from the 12 unqueued bins just before the first queued bin."""
    x = d_o_day[j].copy()
    if not q.any():
        return x
    first = int(np.flatnonzero(q)[0])
    pre = [b for b in range(first - 1, -1, -1) if not q[b]][:12]
    s = (x[pre].sum() / P[pre].sum()) if len(pre) >= 6 and P[pre].sum() > 0 else 1.0
    x[q] = s * P[q]
    return x


def excess_minutes(A15: np.ndarray, qdis: float, s_ev: int, e_ev: int) -> tuple:
    a = (EV0 + max(0, s_ev - 12)) // 3
    b = (EV0 + e_ev) // 3
    w = A15[a:b + 1]
    return int((w > qdis).sum()) * 15, float(w.max() / qdis) if w.size else None


def main() -> int:
    p1 = C.part1()
    days = p1["usable"]["calibration"]
    net = M.build_network(C.VARIANT)
    p = Q.plant_params()                                 # v4 nominal group v_f: travel times only
    src, unrel = p1["sources"], set(p1["unreliable"])
    ids = [e["id"] for e in net.entrances]
    mi = {d: I.model_inputs(d, src, unrel, net) for d in days}
    d_o = np.array([mi[d]["d_o"] for d in days])
    P = {m: np.median(d_o[:, ids.index(m)], axis=0) for m in F2F}
    real_ev = {d: F.day_events(d) for d in days}
    res = {"days": {}, "modes": ["R", "R-NL", "R-NL+Q"]}
    for i, d in enumerate(days):
        base = d_o[i].copy()
        modes = {"R": base}
        nl = base.copy()
        for m, sid in F2F.items():
            nl[ids.index(m)] = rnl(base, ids.index(m), P[m], queued_bins(d, sid))
        modes["R-NL"] = nl
        q = nl.copy()
        for m in CTRL:
            f = I.element_flow(d, m, "input", "queue")
            if f["valid"]:
                q[ids.index(m)] = np.nan_to_num(np.asarray(f["q"], float))
        modes["R-NL+Q"] = q
        ev = real_ev[d]
        rec = {"real_active": {k: bool(ev[k]) for k in ("B1", "B2")}}
        for k in ("B1", "B2"):
            lg = ev[k + "_long"]
            r = {"heavy": bool(lg and lg["heavy"])}
            for mode, dd in modes.items():
                A = G.arrivals(mi[d]["d0"], dd, mi[d]["x_q"], net, p, k)
                if r["heavy"]:
                    s_ev, e_ev = lg["ep"]
                    if k == "B1":
                        tc = ev["censor"].get([tuple(x) for x in ev[k]].index(tuple(lg["ep"])))
                        e_ev = min(e_ev, tc - 1) if tc is not None else e_ev
                    mins, ratio = excess_minutes(A, lg["c4"]["Q_dis"], s_ev, e_ev)
                    r[mode] = {"excess_min": mins, "peak_ratio": ratio}
                else:
                    r[mode] = {"A15": A.tolist()}
            rec[k] = r
        res["days"][d] = rec
    summ = {}
    for k in ("B1", "B2"):
        heavy = [d for d in days if res["days"][d][k]["heavy"]]
        qd_med = float(np.median([real_ev[d][k + "_long"]["c4"]["Q_dis"] for d in heavy])) if heavy else None
        summ[k] = {"n_heavy": len(heavy), "Q_dis_median": qd_med}
        for mode in res["modes"]:
            ex = [res["days"][d][k][mode]["excess_min"] for d in heavy]
            pr = [res["days"][d][k][mode]["peak_ratio"] for d in heavy if res["days"][d][k][mode]["peak_ratio"]]
            inactive = [d for d in days if not res["days"][d][k]["heavy"] and not res["days"][d]["real_active"][k]]
            spur = 0
            for d in inactive:
                A = np.array(res["days"][d][k][mode]["A15"])
                w = A[(EV0 + 120) // 3:(EV0 + 168) // 3]           # 15:00-19:00
                spur += int((w > qd_med).sum() >= 1) if qd_med else 0
            summ[k][mode] = {"share_heavy_with_excess": float(np.mean([e >= 15 for e in ex])) if ex else None,
                             "median_excess_min": float(np.median(ex)) if ex else None,
                             "median_peak_ratio": float(np.median(pr)) if pr else None,
                             "inactive_days": len(inactive), "inactive_with_overload": spur}
    signal = any(all((summ[k][m]["share_heavy_with_excess"] or 0) >= 0.75 for k in ("B1", "B2"))
                 for m in ("R-NL", "R-NL+Q"))
    out = {"prereg": "docs/lab/day_pattern/demand_check_prereg.md", "n_days": len(days), "summary": summ,
           "signal_worth_writing_v5": signal}
    for d in res["days"]:                                    # keep the record small: drop per-bin arrays
        for k in ("B1", "B2"):
            for mode in res["modes"]:
                res["days"][d][k][mode].pop("A15", None)
    out["per_day"] = res["days"]
    (OUT / "demand_check.json").write_text(json.dumps(out, indent=1))
    L = ["# Hidden-demand check (D4.12; pre-registration `demand_check_prereg.md`)", "",
         f"**Signal \"worth writing v5\": {'YES' if signal else 'NO'}.** Calibration days: {len(days)}.", "",
         "| bottleneck | mode | heavy days | share with excess ≥ 15 min | median excess (min) | median peak A/Q_dis | "
         "inactive days with overload |", "|---|---|---|---|---|---|---|"]
    for k in ("B1", "B2"):
        for m in res["modes"]:
            x = summ[k][m]
            L.append(f"| {k} | {m} | {summ[k]['n_heavy']} | {x['share_heavy_with_excess']} | {x['median_excess_min']} | "
                     f"{x['median_peak_ratio'] and round(x['median_peak_ratio'], 3)} | {x['inactive_with_overload']}/{x['inactive_days']} |")
    (OUT / "demand_check.md").write_text("\n".join(L) + "\n")
    print(json.dumps({"signal": signal, "summary": {k: {m: summ[k][m] for m in res["modes"]} for k in summ}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
