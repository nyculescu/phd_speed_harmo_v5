"""Round 1 test, used once: each finalist's 5 learners at their chosen checkpoints, baseline-v3 at its chosen checkpoints and its final policies
(report-only), every confirmatory-3 opponent, p333 and no control; X1 and X2 at 5,300, 40 fresh seeds. Readings T1 and T2 at the Bonferroni
level over finalists x cells; confirmatory 3's other readings beside. usage: test1.py run|read OUT WORKERS TRAINED_JSON VALIDATION_JSON"""
import json
import sys
from pathlib import Path

from common1 import BAND_EVAL, LEARNERS, OPPONENTS, PREFIX, PRIMARY, Q, RULE, SEEDS_BAND, SEEDS_TEST, TRAINING_SLOWDOWNS, check_rows, effect, incumbent, load, med, pt_cfg, rule_cfg
import decide1 as dc
from v5b.fleet import plant_sweep as ps


def tested(trained: dict, v: dict) -> list:
    """The finalists, plus the control arm whenever it trained, for attribution (V420)."""
    return list(dict.fromkeys([*v["finalists"], *(["v3w"] if "v3w" in trained else [])]))


def pol(trained: dict, v: dict, cell: str, slow: dict | None = None) -> dict:
    a = {f"{cell}|d{i}": pt_cfg(incumbent(i, f"u{v['incumbent_chosen'][str(i)]}"), cell, slow) for i in range(LEARNERS)}
    for k in tested(trained, v):
        a |= {f"{cell}|{PREFIX[k]}{i}": pt_cfg(Path(trained[k]) / f"C{i}_u{v['chosen'][k][str(i)]}.pt", cell, slow) for i in range(LEARNERS)}
    return a


def arms(trained: dict, v: dict) -> dict:
    a = {k: x for c in PRIMARY for k, x in pol(trained, v, c).items()}
    a |= {f"{c}|f{i}": pt_cfg(incumbent(i, "final"), c) for c in PRIMARY for i in range(LEARNERS)}
    return a | {f"{c}|{n}": rule_cfg(k, c) for c in PRIMARY for n, k in {**OPPONENTS["ctrl"], "nc": {}}.items()}


def band_arms(trained: dict, v: dict) -> dict:
    """The band, under training slowdowns: the tested candidates, baseline-v3 at its chosen checkpoints, no control, p333 and os1_15_10."""
    a = {k.replace("S|", "B|"): x for k, x in pol(trained, v, "S", TRAINING_SLOWDOWNS).items()}
    return a | {f"B|{n}": rule_cfg(k, "S", TRAINING_SLOWDOWNS) for n, k in {"nc": {}, "p333": OPPONENTS["ctrl"]["p333"], RULE: OPPONENTS["ctrl"][RULE]}.items()}


def beside(T: dict, cell: str, prefix: str) -> dict:
    """Confirmatory 3's other readings for one finalist, its policies renamed d0-d4 for decide3.read_cell; report-only."""
    R = {k: x for k, x in T.items() if k[0].split("|")[1] in {*OPPONENTS["ctrl"], "nc"}}
    R |= {(f"{cell}|d{i}", Q): T[(f"{cell}|{prefix}{i}", Q)] for i in range(LEARNERS)}
    r = dc.d3.read_cell(R, cell, OPPONENTS)
    return {k: r[k] for k in ("replication", "replication_met", "delay", "delay_won", "severe_ok", "worse_than_nc_on_ttc", "nc_delay_more_pct", "strongest", "ttc_gain_on_strongest")}


def read(T: dict, v: dict, trained: dict | None = None, TB: dict | None = None) -> dict:
    fin = v["finalists"]
    pct = dc.bonferroni(len(fin) * len(PRIMARY))
    out = {"pct": pct, "finalists": {}}
    if TB is not None:     # the band: Bonferroni over the arms read; v3w and baseline-v3 beside
        arms_b = tested(trained, v)
        pb = dc.bonferroni(len(arms_b))
        out["band"] = {k: dc.band(TB, [f"{PREFIX[k]}{i}" for i in range(LEARNERS)], pb) for k in arms_b}
        out["band"]["incumbent_report_only"] = dc.band(TB, [f"d{i}" for i in range(LEARNERS)], pb)
    if "v3w" in (trained or {}):     # attribution, report-only: each method finalist against the control arm on the new range
        out["vs_control"] = {k: {c: dc.better(T, c, [f"{PREFIX[k]}{i}" for i in range(LEARNERS)], [f"w{i}" for i in range(LEARNERS)], dc.P95) for c in PRIMARY} for k in fin if k != "v3w"}
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
    f, fb = out / "test.jsonl", out / "band.jsonl"
    if mode == "run":
        ps.matrix(arms(trained, v), (Q,), SEEDS_TEST, f, w, str(out / "rd"))
        ps.matrix(band_arms(trained, v), BAND_EVAL, SEEDS_BAND, fb, w, str(out / "rd"))
    T, TB = load(f), load(fb)
    check_rows(T, len(SEEDS_TEST))
    check_rows(TB, len(SEEDS_BAND))
    r = read(T, v, trained, TB)
    (out / "test_result.json").write_text(json.dumps(r, indent=1))
    for k, x in r["finalists"].items():
        for c, y in x.items():
            print(k, c, "T1", "BETTER than baseline-v3" if y["T1"]["better"] else "not better", y["T1"]["delay_vs_incumbent"], "| T2", "WON" if y["T2"]["won"] else "not won", y["T2"]["tuned"], "of 5, counts", y["T2"]["counts"], flush=True)
    for k, x in r.get("band", {}).items():
        print("band", k, "SHOWN" if x["shown"] else "not shown", {q: (y["ttc_vs_nc"][0], y["ttc_benefit"]) for q, y in x["levels"].items()}, flush=True)
