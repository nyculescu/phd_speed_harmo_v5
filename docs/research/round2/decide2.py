"""Round 2 readings, as fixed in docs/research/protocols/round_2.md (revision 2, V454): checkpoints, advance (paths a and b), harm,
floor KILL and ranking at validation; T1, T2, the 3E status and the readings beside at test; the band profile; what follows."""
import sys

import numpy as np

from common2e import LEARNERS, OPPONENTS, ORDER, PREFIX, PRIMARY, Q, RULE, BAND_EVAL, opponents2, e3_rules
sys.path.insert(0, str(__import__("common2e").ROOT / "docs/research/round1"))
import decide1 as d1  # noqa: E402
from common1 import arm_mean, collisions, med, paired_median, raw  # noqa: E402,F401

P95 = (2.5, 97.5)
d3 = d1.d3
bonferroni = d1.bonferroni


def names(kind: str, chosen: dict | None) -> list:
    """Arm names of a candidate's learners (without the cell): tail has no checkpoint."""
    p = PREFIX[kind]
    if kind == "tail":
        return [f"{p}{i}" for i in range(LEARNERS)]
    return [f"{p}{i}u{chosen[i]}" for i in range(LEARNERS)]


def choose_all(T: dict, kind: str, q: float = Q) -> dict:
    """Round 1's checkpoint rule for each learner of an arm with u250 and u500 (os1_15_10 is the reference)."""
    return {i: d1.choose(T, PREFIX[kind], i, q=q) for i in range(LEARNERS)}


def arm(T: dict, cell: str, nm: list, q: float = Q) -> dict:
    return arm_mean(T, [f"{cell}|{n}" for n in nm], q)


def paths(K: dict, W: dict, pct: tuple) -> dict:
    """Path (a), path (b) and harm of arm K against the incumbent arm W. Harm is always read at 95 %."""
    d, t = raw(K, W, "all_delay", pct=pct), raw(K, W, "ttc_net", pct=pct)
    d95, t95 = raw(K, W, "all_delay", pct=P95), raw(K, W, "ttc_net", pct=P95)
    a = d[1] > 0 and t[0] >= -10.0
    b = t[1] > 0 and t[0] >= 10.0 and d[0] >= -2.0
    harm = (d95[0] < -2.0 and d95[2] < 0) or (t95[0] < -10.0 and t95[2] < 0)
    return {"delay": d, "ttc": t, "a": a, "b": b, "better": a or b, "harm": harm, "score": max(d[0] / 2.0, t[0] / 10.0)}


def advance(T: dict, kind: str, chosen: dict | None, w_chosen: dict, o2: dict, killed: bool = False, q: float = Q) -> dict:
    cells, harm, floor = {}, [], []
    for c in PRIMARY:
        K, W = arm(T, c, names(kind, chosen), q), arm(T, c, names("v3w", w_chosen), q)
        r = paths(K, W, P95)
        u500 = names(kind, {i: 500 for i in range(LEARNERS)})
        K500 = arm(T, c, u500, q)
        tp = raw(K500, T[(f"{c}|p333", q)], "ttc_net", pct=P95)
        dn = raw(K500, T[(f"{c}|nc", q)], "all_delay", pct=P95)
        r |= {"u500_ttc_vs_p333": tp, "u500_delay_vs_nc": dn, "tuned": d1.tuned(T, c, o2, names(kind, chosen), P95, q)["tuned"]}
        cells[c] = r
        harm += [c] if r["harm"] else []
        floor += [c] if tp[0] < 10.0 or dn[2] < 0 else []
    better = [c for c, r in cells.items() if r["better"]]
    ok = bool(better) and not harm and not floor and not killed
    return {"cells": cells, "better": better, "harm": harm, "floor_kill": floor, "killed": killed, "advances": ok,
            "count": sum(r["tuned"] for r in cells.values()), "score": max((cells[c]["score"] for c in better), default=None)}


def finalists(res: dict, k: int = 2) -> list:
    ok = [n for n, r in res.items() if r["advances"]]
    return sorted(ok, key=lambda n: (-res[n]["count"], -res[n]["score"], ORDER.index(n)))[:k]


def e3_status(T: dict, cell: str, q: float = Q, pct: tuple = P95) -> dict:
    """Each 3E rule of the cell: counts or not (delay within 2 % of p333, point), and its delay and TTC against p333 and os1_15_10."""
    out = {}
    p333, os1 = T[(f"{cell}|p333", q)], T[(f"{cell}|{RULE}", q)]
    for n in e3_rules(cell):
        A = T[(f"{cell}|{n}", q)]
        d = raw(A, p333, "all_delay", pct=pct)
        out[n] = {"counts": d[0] >= -2.0, "delay_vs_p333": d, "ttc_vs_p333": raw(A, p333, "ttc_net", pct=pct),
                  "delay_vs_os1": raw(A, os1, "all_delay", pct=pct), "ttc_vs_os1": raw(A, os1, "ttc_net", pct=pct),
                  "flow_vs_p333": raw(A, p333, "passed", 1, pct), "b3_vs_p333": raw(A, p333, "b3_step", pct=pct),
                  "collisions": collisions(A), "collisions_p333": collisions(p333)}
    return out


def beside(T: dict, cell: str, nm: list, o2: dict, q: float = Q) -> dict:
    """Confirmatory 3's other readings for one arm on T2's counting set (3E rules included), its policies renamed d0-d4 for read_cell."""
    keep = {*o2["ctrl"], *[n for c in o2["cells"].values() for n in c["forms"].values()], "nc"}
    R = {k: x for k, x in T.items() if k[0].split("|")[1] in keep and k[0].startswith(cell + "|")}
    R |= {(f"{cell}|d{i}", q): T[(f"{cell}|{n}", q)] for i, n in enumerate(nm)}
    r = d3.read_cell(R, cell, o2, n=LEARNERS, q=q)
    return {k: r[k] for k in ("counts", "replication", "replication_met", "delay_opponent", "delay", "delay_won", "severe_ok",
                              "worse_than_nc_on_ttc", "nc_delay_more_pct", "strongest", "ttc_gain_on_strongest")}


def noninferiority(T: dict, cell: str, nm: list, counts: list, pct: tuple, q: float = Q) -> dict:
    """Report-only (D11): per policy and counting opponent, the worse end of the corrected delay CI, against a 5 % margin."""
    out = {}
    for n in nm:
        P = T[(f"{cell}|{n}", q)]
        out[n] = {r: {"lower": raw(P, T[(f"{cell}|{r}", q)], "all_delay", pct=pct)[1]} for r in counts}
        for r in counts:
            out[n][r]["within_5"] = out[n][r]["lower"] >= -5.0
    return out


def t1(T: dict, cell: str, nm: list, w_nm: list, pct: tuple, q: float = Q) -> dict:
    r = paths(arm(T, cell, nm, q), arm(T, cell, w_nm, q), pct)
    return r | {"t1_better": r["better"] and not r["harm"]}


def follows(res: dict, v3w_t2_cells: int) -> dict:
    """D10: a finalist replaces v3w only if T1-better in a cell, harmed in neither, and T2 in at least as many cells as v3w."""
    ok = {k: r for k, r in res.items() if any(x["t1_better"] for x in r["T1"].values()) and not any(x["harm"] for x in r["T1"].values())
          and r["t2_cells"] >= v3w_t2_cells}
    if not ok:
        return {"incumbent": "v3w", "qualified": []}
    best = sorted(ok, key=lambda k: (-ok[k]["t2_cells"], -ok[k]["t2_learners"], -ok[k]["score"]))[0]
    return {"incumbent": best, "qualified": sorted(ok)}


def share_ci(x: np.ndarray, n_boot: int = 20000, seed: int = 20261107) -> list:
    """Share of seeds where the arm has fewer TTC seconds than no control, with a 95 % percentile bootstrap CI."""
    rng = np.random.default_rng(seed)
    b = rng.integers(0, len(x), (n_boot, len(x)))
    s = x[b].mean(1)
    return [float(x.mean()), float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))]


def band_profile(TB: dict, nm: list, cell: str = "B") -> dict:
    """Report-only (D5): per level, TTC and delay against no control (95 %) and the share of seeds with fewer TTC seconds."""
    out = {}
    for q in BAND_EVAL:
        K, nc = arm(TB, cell, nm, q), TB[(f"{cell}|nc", q)]
        ds = sorted(set(K) & set(nc))
        fewer = np.array([float(K[s]["ttc_net"] < nc[s]["ttc_net"]) for s in ds])
        out[str(q)] = {"ttc_vs_nc": raw(K, nc, "ttc_net", pct=P95), "delay_vs_nc": raw(K, nc, "all_delay", pct=P95), "share_fewer": share_ci(fewer)}
    return out
