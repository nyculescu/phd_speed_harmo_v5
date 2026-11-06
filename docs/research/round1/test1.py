"""Round 1 test, used once: each finalist's 5 learners at their chosen checkpoints, baseline-v3 at its chosen checkpoints and its final policies
(report-only), every confirmatory-3 opponent, p333 and no control; X1 and X2 at 5,300, 40 fresh seeds. Readings T1 and T2 at the Bonferroni
level over finalists x cells; confirmatory 3's other readings beside. usage: test1.py run|read OUT WORKERS TRAINED_JSON VALIDATION_JSON"""
import json
import sys
from pathlib import Path

from common1 import LEARNERS, OPPONENTS, PREFIX, PRIMARY, Q, SEEDS_TEST, check_rows, effect, incumbent, load, med, pt_cfg, rule_cfg
import decide1 as dc
from v5b.fleet import plant_sweep as ps


def arms(trained: dict, v: dict) -> dict:
    a = {f"{c}|d{i}": pt_cfg(incumbent(i, f"u{v['incumbent_chosen'][str(i)]}"), c) for c in PRIMARY for i in range(LEARNERS)}
    a |= {f"{c}|f{i}": pt_cfg(incumbent(i, "final"), c) for c in PRIMARY for i in range(LEARNERS)}
    for k in v["finalists"]:
        a |= {f"{c}|{PREFIX[k]}{i}": pt_cfg(Path(trained[k]) / f"C{i}_u{v['chosen'][k][str(i)]}.pt", c) for c in PRIMARY for i in range(LEARNERS)}
    return a | {f"{c}|{n}": rule_cfg(k, c) for c in PRIMARY for n, k in {**OPPONENTS["ctrl"], "nc": {}}.items()}


def beside(T: dict, cell: str, prefix: str) -> dict:
    """Confirmatory 3's other readings for one finalist, its policies renamed d0-d4 for decide3.read_cell; report-only."""
    R = {k: x for k, x in T.items() if k[0].split("|")[1] in {*OPPONENTS["ctrl"], "nc"}}
    R |= {(f"{cell}|d{i}", Q): T[(f"{cell}|{prefix}{i}", Q)] for i in range(LEARNERS)}
    r = dc.d3.read_cell(R, cell, OPPONENTS)
    return {k: r[k] for k in ("replication", "replication_met", "delay", "delay_won", "severe_ok", "worse_than_nc_on_ttc", "nc_delay_more_pct", "strongest", "ttc_gain_on_strongest")}


def read(T: dict, v: dict) -> dict:
    fin = v["finalists"]
    pct = dc.bonferroni(len(fin) * len(PRIMARY))
    out = {"pct": pct, "finalists": {}}
    for k in fin:
        names = [f"{PREFIX[k]}{i}" for i in range(LEARNERS)]
        out["finalists"][k] = {c: {"T1": dc.better(T, c, names, [f"d{i}" for i in range(LEARNERS)], pct), "T2": dc.tuned(T, c, OPPONENTS, names, pct),
                                   "T2_incumbent_chosen": dc.tuned(T, c, OPPONENTS, [f"d{i}" for i in range(LEARNERS)], pct), "beside": beside(T, c, PREFIX[k])} for c in PRIMARY}
    out["no_control"] = {c: {m: med(T[(f"{c}|nc", Q)], m) for m in ("ttc_net", "all_delay", "b3_step")} for c in PRIMARY}
    out["final_vs_chosen_incumbent"] = {c: [effect(T[(f"{c}|f{i}", Q)], T[(f"{c}|d{i}", Q)], "all_delay", pct=dc.P95) for i in range(LEARNERS)] for c in PRIMARY}
    return out


if __name__ == "__main__":
    mode, out, w = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
    trained, v = json.load(open(sys.argv[4])), json.load(open(sys.argv[5]))
    if not v["finalists"]:
        sys.exit("no finalist: the test is not run")
    out.mkdir(parents=True, exist_ok=True)
    f = out / "test.jsonl"
    if mode == "run":
        ps.matrix(arms(trained, v), (Q,), SEEDS_TEST, f, w, str(out / "rd"))
    T = load(f)
    check_rows(T, len(SEEDS_TEST))
    r = read(T, v)
    (out / "test_result.json").write_text(json.dumps(r, indent=1))
    for k, x in r["finalists"].items():
        for c, y in x.items():
            print(k, c, "T1", "BETTER than baseline-v3" if y["T1"]["better"] else "not better", y["T1"]["delay_vs_incumbent"], "| T2", "WON" if y["T2"]["won"] else "not won", y["T2"]["tuned"], "of 5, counts", y["T2"]["counts"], flush=True)
