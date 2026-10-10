"""Per-day gate items shared by the plant gate (`metanet_gate.deterministic`) and the v5 objective J5 (protocol v5
§B1.1: one implementation). Pure functions: real events and model day outputs in, per-day statistics out. The
aggregation into rows (medians, CIs, thresholds) stays in the gate. Test 30 checks the gate against tag
`metanet-v4-stop` bit for bit.
"""
from __future__ import annotations

import numpy as np

from vsl_lab.data import metanet_events as V
from vsl_lab.data import metanet_inputs as I

UNMATCHED_ONSET_MIN = 90


def p4_day(re: list, me: list) -> list:
    """P4: per real episode, (|Δonset| in minutes or None if unmatched, matched model index or None)."""
    mt = V.match_episodes(re, me)
    return [((abs(r[0] - me[mt[i]][0]) * 5), mt[i]) if i in mt else (None, None) for i, r in enumerate(re)]


def p5a_day(real_long: dict, model_c4: dict | None) -> float | None:
    """P5a: Q̂_dis/Q_dis − 1 on a heavy day, None if the model C4 is not usable."""
    return None if model_c4 is None else model_c4["Q_dis"] / real_long["c4"]["Q_dis"] - 1


def p7a_day(ev: dict, md_k: dict, k: str) -> tuple:
    """P7a on a heavy day at k: (model duration, real duration, t_c). Unmatched -> model duration 0 (the gate's |0 − d_r|)."""
    lg = ev[k + "_long"]
    re = [tuple(e) for e in ev[k]]
    tc = ev["censor"].get(re.index(tuple(lg["ep"]))) if k == "B1" else None
    mep = md_k.get("matched")
    return (V.censored_duration(tuple(mep), tc) if mep else 0), lg["dur_min"], tc


def p5c_day(rmerge: list, mm: list) -> float | None:
    """P5c: model/real ratio of the B2/B1 merge-section discharges − 1; None if a model value is missing."""
    if not all(x is not None for x in mm):
        return None
    return (mm[1] / mm[0]) / (rmerge[1]["discharge"] / rmerge[0]["discharge"]) - 1


def matched_model(ev: dict, md: dict) -> dict:
    """Model episodes matched (one-to-one, ±90 min) to the real ones, per bottleneck (all model episodes)."""
    out = {}
    for k in ("B1", "B2"):
        re = [tuple(e) for e in ev[k]]
        me = md[k]["episodes"]
        out[k] = [me[j] for j in V.match_episodes(re, me).values()]
    return out


def p7b_day(ev: dict, md: dict, rsp: dict, rvl: dict, msp: dict, mvl: dict, extent, upst: dict) -> dict:
    """P7b: real and model extent stations and the index error in the real-valid event-station order.
    err = 0 if the stations coincide; |Δindex| if both are in the order; None if not comparable or unmatched."""
    rk = "B1" if ev["B1"] else "B2"
    r_ext = extent(rsp, rvl, upst[rk], [tuple(x) for x in list(ev["B1"]) + list(ev["B2"])])
    mm = matched_model(ev, md)
    if not (mm["B1"] or mm["B2"]):
        return {"matched": False, "r_ext": r_ext, "m_ext": None, "err": None}
    mk = "B1" if mm["B1"] else "B2"
    m_ext = extent(msp, mvl, upst[mk], [tuple(x) for x in mm["B1"] + mm["B2"]])
    order = [s for s in sorted(I.EVENT_STATIONS, key=lambda s: I.ST[s]["km"]) if rvl[s]]
    if m_ext == r_ext:
        err = 0
    elif r_ext in order and m_ext in order:
        err = abs(order.index(m_ext) - order.index(r_ext))
    else:
        err = None
    return {"matched": True, "r_ext": r_ext, "m_ext": m_ext, "err": err}


def p7b_hit(r: dict) -> bool:
    """The gate's P7b hit: the model extent station is the real one or one of its two neighbours."""
    return bool(r["matched"] and r["err"] is not None and r["err"] <= 1)


def p7c_day(ev: dict, md: dict) -> tuple:
    """P7c: (dur_sys,real, dur_sys,model) in minutes, on all model P_1/P_2 episodes."""
    return V.p7c_pair(ev["B1"], ev["B2"], md["B1"]["episodes"], md["B2"]["episodes"])


def p8_day(md: dict, ev: dict, rp: dict, spurious, overlaps) -> dict:
    """P8 per day: spurious pairs (i)-(ii) and, per bottleneck, the model episodes that overlap no real one (iii)."""
    sp = spurious(md["pairs"], rp)
    extra = {}
    for k in ("B1", "B2"):
        extra[k] = [e for e in md[k]["episodes"] if not overlaps([e], [tuple(x) for x in ev[k]])]
    return {"spurious": sp, "extra": extra,
            "extra_min": {k: sum((e[1] - e[0] + 1) * 5 for e in x) for k, x in extra.items()}}


def s1_ratio(q: np.ndarray, s: int, e: int, qd: float, cut: int | None) -> float | None:
    """P9 S1: max 15-min rolling flow in [onset − 60 min, end (or cut − 1)] / Q_dis; None if the window is empty.
    (The gate at tag metanet-v4-stop raised on an empty window instead of returning None; fixed pre-look, v5 rev.)"""
    e = e if cut is None else min(e, cut - 1)
    seg = np.nan_to_num(q[max(0, s - 12):e + 1])
    if seg.size == 0:
        return None
    roll = np.convolve(seg, np.ones(3) / 3, mode="valid")
    return float(roll.max() / qd)
