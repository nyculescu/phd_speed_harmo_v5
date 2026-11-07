"""Thesis reading, V459, not a round-2 verdict: each tested arm and each rule against no control on round 2's stored test rows.
Met when delay is at least 10 % lower with the CI excluding 0 at T2's level, and close-following is not harmed under round 2's harm rule
(TTC point worse than 10 % with the 95 % CI upper bound below 0). Reads rows only; changes no protocol reading.
usage: thesis2.py OUT VALIDATION_JSON"""
import json
import sys
from pathlib import Path

from common2e import PRIMARY, Q, SEEDS_TEST, load_union
import decide2 as dc

LABEL = "thesis reading, V459, not a round-2 verdict"


def bar(K: dict, nc: dict, pct: tuple) -> dict:
    d = dc.raw(K, nc, "all_delay", pct=pct)
    t = dc.raw(K, nc, "ttc_net", pct=dc.P95)
    delay_ok = d[0] >= 10.0 and d[1] > 0
    harmed = t[0] < -10.0 and t[2] < 0
    return {"delay_vs_nc": d, "ttc_vs_nc_95": t, "delay_ok": delay_ok, "ttc_harmed": harmed, "met": delay_ok and not harmed}


def reading(T: dict, groups: dict, rules: list, pct: tuple, q: float = Q) -> dict:
    """groups: arm kind -> its policy names; rules: single-arm names. Arms are the per-seed mean over policies, as in T1."""
    out = {"label": LABEL, "pct": pct, "cells": {}}
    for c in PRIMARY:
        nc = T[(f"{c}|nc", q)]
        cell = {}
        for kind, nm in groups.items():
            r = bar(dc.arm(T, c, nm, q), nc, pct)
            pol = [bar(T[(f"{c}|{n}", q)], nc, pct)["met"] for n in nm]
            cell[kind] = r | {"policies_met": sum(pol), "policies": len(nm)}
        for n in rules:
            if (f"{c}|{n}", q) in T:
                cell[n] = bar(T[(f"{c}|{n}", q)], nc, pct)
        out["cells"][c] = cell
    return out


def main(out: Path, v_f: str) -> dict:
    import test2
    v = json.load(open(v_f))
    g, _ = test2.arms(v)
    T = load_union(sorted((out / "test").glob("rows_*.jsonl")), len(SEEDS_TEST), {k for a in g.values() for k in a})
    tested, inc = test2.plan(v)
    groups = {k: dc.names(k, ch) for k, ch in [*tested, inc]}
    learners = {n for nm in groups.values() for n in nm}
    rules = sorted({k[0].split("|")[1] for k in T} - learners - {"nc"})
    pct = dc.bonferroni((len(v["finalists"]) + 1) * 2)     # T2's level
    r = reading(T, groups, rules, pct)
    (out / "thesis_v459.json").write_text(json.dumps(r, indent=1))
    for c, cell in r["cells"].items():
        for a, x in cell.items():
            print(c, a, "met" if x["met"] else "not met", "delay", x["delay_vs_nc"], "ttc95", x["ttc_vs_nc_95"],
                  f"policies {x['policies_met']}/{x['policies']}" if "policies" in x else "", flush=True)
    return r


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2])
