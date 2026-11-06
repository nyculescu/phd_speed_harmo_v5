"""Round 1, stage 0 (no training). 0a: baseline-v3's checkpoints u50-u500 with os1_15_10, p333 and no control, X1 and X2 at 5,300, 20 seeds
(report-only). 0b: os1_15_10, p333 and baseline-v3's final policies under training conditions at the 7 training levels, 20 seeds: 2C's d_ref
and its stop rule. 0c: no control in steady traffic at the 7 training levels, 20 seeds: the reward references (as confirmatory 3's make_env).
usage: stage0.py run|read OUT WORKERS"""
import json
import sys
from pathlib import Path

import numpy as np

from common1 import CHECKPOINTS, LEARNERS, LEVELS, OPPONENTS, PRIMARY, Q, RULE, SEEDS_STAGE0A, SEEDS_STAGE0B, SEEDS_STAGE0C, TRAINING_SLOWDOWNS, check_rows, incumbent, load, med, pt_cfg, raw, rule_cfg, val
import decide1 as dc
from v5b.fleet import c_train as ct, plant_sweep as ps

RULES0 = {RULE: OPPONENTS["ctrl"][RULE], "p333": OPPONENTS["ctrl"]["p333"]}


def arms_0a() -> dict:
    a = {f"{c}|d{i}u{ck}": pt_cfg(incumbent(i, f"u{ck}"), c) for c in PRIMARY for i in range(LEARNERS) for ck in CHECKPOINTS}
    a |= {f"{c}|{n}": rule_cfg(k, c) for c in PRIMARY for n, k in {**RULES0, "nc": {}}.items()}
    return a


def arms_0b() -> dict:
    a = {f"T|{n}": rule_cfg(k, "S", TRAINING_SLOWDOWNS) for n, k in RULES0.items()}
    return a | {f"T|d{i}": pt_cfg(incumbent(i, "final"), "S", TRAINING_SLOWDOWNS) for i in range(LEARNERS)}


def refs_0c(T: dict) -> dict:
    """Per training level, the median over seeds of no control's braking, TTC and vehicles in system per second (V334, V358)."""
    return {str(q): [round(float(np.median([val(x, k) / x["steps"] for x in T[("S|nc", q)].values()])), d) for k, d in (("brake3", 3), ("E30", 3), ("N", 1))] for q in LEVELS}


def spearman(x: list, y: list) -> float:
    rx, ry = np.argsort(np.argsort(x)), np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1])


def read_0a(T: dict) -> dict:
    """Per cell: each checkpoint against os1_15_10; how early checkpoints rank learners; whether a chosen checkpoint clears where u500 does not."""
    out = {"effects": {}, "rank_vs_u500": {}, "chosen": {}, "clears": {}}
    O = {c: T[(f"{c}|{RULE}", Q)] for c in PRIMARY}
    bar = lambda c, name: (lambda t, d: d[0] if t[0] >= 10.0 else -100.0)(raw(T[(f"{c}|{name}", Q)], O[c], "ttc_net", pct=dc.P95), raw(T[(f"{c}|{name}", Q)], O[c], "all_delay", pct=dc.P95))
    for c in PRIMARY:
        out["effects"][c] = {f"d{i}u{ck}": {"ttc": raw(T[(f"{c}|d{i}u{ck}", Q)], O[c], "ttc_net", pct=dc.P95), "delay": raw(T[(f"{c}|d{i}u{ck}", Q)], O[c], "all_delay", pct=dc.P95)}
                             for i in range(LEARNERS) for ck in CHECKPOINTS}
        final = [bar(c, f"d{i}u500") for i in range(LEARNERS)]
        out["rank_vs_u500"][c] = {ck: spearman([bar(c, f"d{i}u{ck}") for i in range(LEARNERS)], final) for ck in (100, 150, 250)}
    for i in range(LEARNERS):
        ck = dc.choose(T, "d", i, CHECKPOINTS)
        out["chosen"][f"d{i}"] = ck
        for c in PRIMARY:
            f500 = dc.fails(T[(f"{c}|d{i}u500", Q)], O[c], 10.0, (1.25, 98.75))
            fch = dc.fails(T[(f"{c}|d{i}u{ck}", Q)], O[c], 10.0, (1.25, 98.75))
            out["clears"][f"{c}|d{i}"] = {"u500_fails": f500, "chosen_fails": fch}
    return out


def read_0b(T: dict) -> dict:
    """d_ref per level: the lower median training-mode delay of os1_15_10 and p333. J per policy: mean over runs of delay / d_ref(q)."""
    d_ref, lower = {}, {}
    for q in LEVELS:
        m = {n: float(np.median([r["delay_s"] for r in T[(f"T|{n}", q)].values()])) for n in RULES0}
        lower[str(q)] = min(m, key=m.get)
        d_ref[str(q)] = m[lower[str(q)]]
    J = {n: float(np.mean([r["delay_s"] / d_ref[str(q)] for q in LEVELS for r in T[(f"T|{n}", q)].values()])) for n in [*RULES0, *(f"d{i}" for i in range(LEARNERS))]}
    met = sum(J[f"d{i}"] <= ct.LAGR["target"] for i in range(LEARNERS))
    return {"d_ref": d_ref, "lower_rule": lower, "J": J, "policies_meeting_target": met, "stop_2c": met >= 4, "target": ct.LAGR["target"]}


if __name__ == "__main__":
    mode, out, w = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    if mode == "run":
        ps.matrix(arms_0a(), (Q,), SEEDS_STAGE0A, out / "stage0a.jsonl", w, str(out / "rd"))
        ps.matrix(arms_0b(), LEVELS, SEEDS_STAGE0B, out / "stage0b.jsonl", w, str(out / "rd"))
        ps.matrix({"S|nc": rule_cfg({}, "S")}, LEVELS, SEEDS_STAGE0C, out / "stage0c.jsonl", w, str(out / "rd"))
    A, B, C = load(out / "stage0a.jsonl"), load(out / "stage0b.jsonl"), load(out / "stage0c.jsonl")
    check_rows(A, len(SEEDS_STAGE0A))
    check_rows(B, len(SEEDS_STAGE0B))
    check_rows(C, len(SEEDS_STAGE0C))
    assert all(r.get("delay_s") is not None for x in B.values() for r in x.values()), "a stage-0b row lacks delay_s"
    a, b = read_0a(A), {**read_0b(B), "refs": refs_0c(C)}
    assert all(np.isfinite(x) and x >= 0 for v in b["refs"].values() for x in v) and all(v[2] > 0 for v in b["refs"].values()), b["refs"]
    (out / "stage0a.json").write_text(json.dumps(a, indent=1))
    (out / "stage0b.json").write_text(json.dumps(b, indent=1))
    print("0a rank against u500:", a["rank_vs_u500"], "chosen:", a["chosen"], flush=True)
    print("0a chosen clears where u500 fails:", {k: v for k, v in a["clears"].items() if v["u500_fails"] and not v["chosen_fails"]}, flush=True)
    print("0c reward references:", b["refs"], flush=True)
    print("0b d_ref:", b["d_ref"], "lower rule:", b["lower_rule"], "J:", {k: round(v, 4) for k, v in b["J"].items()}, flush=True)
    print("2C", "NOT TRAINED: constraint not binding" if b["stop_2c"] else "trains", f"({b['policies_meeting_target']} of 5 policies at J <= {b['target']})", flush=True)
