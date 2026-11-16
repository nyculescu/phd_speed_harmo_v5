"""Round 1 readings, as fixed in the protocol: checkpoint choice, the advance rule and floor at validation, and the test readings T1 (against
baseline-v3) and T2 (confirmatory 3's tuned reading at the Bonferroni level). Policy arms are named <cell>|<prefix><learner>[u<ck>]."""
import sys

from common1 import LEARNERS, PRIMARY, Q, RULE, arm_mean, collisions, med, paired_median, raw

sys.path.insert(0, str(__import__("common1").ROOT / "docs/research/conf3"))
import decide3 as d3  # noqa: E402

P95 = (2.5, 97.5)


def bonferroni(m: int) -> tuple:
    """Two-sided percentile bounds at 1 - 0.05/m."""
    a = 100.0 * 0.05 / m / 2.0
    return (a, 100.0 - a)


def choose(T: dict, prefix: str, i: int, cks: tuple = (250, 500), q: float = Q) -> int:
    """Per learner: the checkpoint within 2 % of os1_15_10's delay in more cells; then fewer TTC seconds summed over the cells' medians;
    then the later one."""
    def score(ck):
        n = sum(raw(T[(f"{c}|{prefix}{i}u{ck}", q)], T[(f"{c}|{RULE}", q)], "all_delay")[0] >= -2.0 for c in PRIMARY)
        ttc = sum(med(T[(f"{c}|{prefix}{i}u{ck}", q)], "ttc_net") for c in PRIMARY)
        return (n, -ttc, ck)
    return max(cks, key=score)


def arm(T: dict, cell: str, prefix: str, chosen: dict, q: float = Q) -> dict:
    return arm_mean(T, [f"{cell}|{prefix}{i}u{chosen[i]}" for i in range(LEARNERS)], q)


def advance(T: dict, prefix: str, chosen: dict, inc_chosen: dict, q: float = Q) -> dict:
    """The validation rule for one candidate against the incumbent arm, 95 % CIs, no correction (validation selects)."""
    cells, harm, floor = {}, [], []
    for c in PRIMARY:
        K, I = arm(T, c, prefix, chosen, q), arm(T, c, "d", inc_chosen, q)
        d = raw(K, I, "all_delay", pct=P95)
        t = raw(K, T[(f"{c}|{RULE}", q)], "ttc_net", pct=P95)
        cells[c] = {"delay_vs_incumbent": d, "ttc_vs_rule": t, "qualifies": d[1] > 0 and t[0] >= 10.0}
        harm += [c] if d[2] < 0 else []
        K500 = arm(T, c, prefix, {i: 500 for i in range(LEARNERS)}, q)
        tp = raw(K500, T[(f"{c}|p333", q)], "ttc_net", pct=P95)
        dn = raw(K500, T[(f"{c}|nc", q)], "all_delay", pct=P95)
        floor += [c] if tp[0] < 10.0 or dn[2] < 0 else []
        cells[c] |= {"u500_ttc_vs_p333": tp, "u500_delay_vs_nc": dn}
    ok = any(x["qualifies"] for x in cells.values()) and not harm and not floor
    best = max((x["delay_vs_incumbent"][0] for x in cells.values() if x["qualifies"]), default=None)
    return {"cells": cells, "harm": harm, "floor_kill": floor, "advances": ok, "rank_key": best}


def finalists(res: dict, k: int = 2) -> list:
    """At most k candidates that advance, ranked by their largest delay effect against the incumbent."""
    ok = [n for n, r in res.items() if r["advances"]]
    return sorted(ok, key=lambda n: -res[n]["rank_key"])[:k]


def limits(P: dict, O: dict, pct: tuple) -> dict:
    ev = raw(P, O, "alks_full_moving", pct=pct)[0] >= -5.0 or paired_median(P, O, "alks_full_moving") <= 5.0
    return {"delay": raw(P, O, "all_delay", pct=pct)[0] >= -2.0, "flow": raw(P, O, "passed", 1, pct=pct)[0] >= -0.5, "brake": raw(P, O, "b3_step", pct=pct)[0] >= -5.0,
            "events": ev, "coll": collisions(P) <= collisions(O) + 1}


def fails(P: dict, O: dict, margin: float, pct: tuple) -> list:
    e = raw(P, O, "ttc_net", pct=pct)
    out = [] if e[0] >= margin else ["margin"]
    out += [] if e[1] > 0 else ["ci"]
    out += [] if paired_median(O, P, "ttc_net") >= 20.0 else ["per run"]
    return out + [k for k, ok in limits(P, O, pct).items() if not ok]


def tuned(T: dict, cell: str, o: dict, names: list, pct: tuple, q: float = Q) -> dict:
    """T2: confirmatory 3's tuned reading for the named policies, with the CI level passed through; point thresholds unchanged."""
    A = lambda name: T[(f"{cell}|{name}", q)]
    p333 = A("p333")
    c = o["cells"][cell]
    opp = list(dict.fromkeys(["p333", *c["forms"].values()]))
    counts = [r for r in opp if raw(A(r), p333, "all_delay")[0] >= -2.0]
    blocked = [{r: fails(A(n), A(r), 10.0, pct) for r in counts if fails(A(n), A(r), 10.0, pct)} for n in names]
    ok = [not b and d3.anchored(A(n), p333) for b, n in zip(blocked, names)]
    return {"cell": cell, "counts": counts, "tuned": sum(ok), "won": sum(ok) >= 4, "blocked": blocked, "pct": pct}


def better(T: dict, cell: str, names: list, inc: list, pct: tuple, q: float = Q) -> dict:
    """T1: the finalist's arm against the incumbent's, at the corrected level: less delay with the CI clear of 0, TTC at most 10 % more."""
    K, I = arm_mean(T, [f"{cell}|{n}" for n in names], q), arm_mean(T, [f"{cell}|{n}" for n in inc], q)
    d, t = raw(K, I, "all_delay", pct=pct), raw(K, I, "ttc_net", pct=pct)
    return {"cell": cell, "delay_vs_incumbent": d, "ttc_vs_incumbent": t, "better": d[1] > 0 and t[0] >= -10.0}


def band(T: dict, names: list, pct: tuple, cell: str = "B") -> dict:
    """V420: the arm against no control under training slowdowns at each band and edge level. The band is shown if close-following is at
    least 10 % and 20 per run fewer, CI clear of 0, at every band level; all three must hold, so no correction within the arm. Edges are
    reported, not required either way: a policy trained over the range may extend the band."""
    from common1 import BAND, BAND_EVAL
    out = {}
    for q in BAND_EVAL:
        K, nc = arm_mean(T, [f"{cell}|{n}" for n in names], q), T[(f"{cell}|nc", q)]
        t, d = raw(K, nc, "ttc_net", pct=pct), raw(K, nc, "all_delay", pct=pct)
        out[str(q)] = {"ttc_vs_nc": t, "delay_vs_nc": d, "ttc_benefit": t[0] >= 10.0 and t[1] > 0 and paired_median(nc, K, "ttc_net") >= 20.0}
    return {"levels": out, "shown": all(out[str(q)]["ttc_benefit"] for q in BAND), "pct": pct}
