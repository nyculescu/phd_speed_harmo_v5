"""Round 2 test, used once (round_2.md): the finalists, v3w and baseline-v3 (report-only) against every opponent, the 3E rules included,
X1 and X2 at 5,300 on 40 fresh seeds; then the band profile on 20 fresh seeds under the training slowdowns (report-only).
usage: test2.py run OUT RUN_COMMIT WORKERS VALIDATION_JSON | read OUT VALIDATION_JSON"""
import json
import sys
from pathlib import Path

import numpy as np

from common2e import (BAND_EVAL, LEARNERS, OPPONENTS, PRIMARY, Q, RULE, SEEDS_BAND, SEEDS_TEST, TRAINING_SLOWDOWNS, cand_cfg, load_union,
                      opponents2, rule_arms, run_arms, snapshot_of)
import decide2 as dc

BAND_RULES = {"nc", "p333", RULE, "3e"}


def plan(v: dict) -> tuple:
    """(kind, chosen) for the finalists and v3w, and baseline-v3 at u500 (report-only)."""
    ch = lambda k: None if k == "tail" else {int(i): c for i, c in v["chosen"][k].items()}
    tested = [(k, ch(k)) for k in v["finalists"]] + [("v3w", ch("v3w"))]
    return tested, ("inc", {i: 500 for i in range(LEARNERS)})


def arms(v: dict) -> tuple:
    tested, inc = plan(v)
    g, gb = {}, {}
    for kind, ch in [*tested, inc]:
        for i in range(LEARNERS):
            ck = None if ch is None else ch[i]
            nm = dc.names(kind, ch)[i]
            for c in PRIMARY:
                g.setdefault(snapshot_of(kind), {})[f"{c}|{nm}"] = cand_cfg(kind, i, ck, c)
            gb.setdefault(snapshot_of(kind), {})[f"B|{nm}"] = cand_cfg(kind, i, ck, "S", TRAINING_SLOWDOWNS)
    for c in PRIMARY:
        g.setdefault("eval", {}).update(rule_arms(c, c))
    gb.setdefault("eval", {}).update(rule_arms("B", "S", TRAINING_SLOWDOWNS, BAND_RULES))
    return g, gb


def per_level_vs(TB: dict, a: str, b: str) -> dict:
    """3E-T against os1_15_10 per band level, as change against the reference (positive = more), and TTC pooled in seconds."""
    out, dsum, bsum = {}, 0.0, 0.0
    for q in BAND_EVAL:
        A, B = TB[(f"B|{a}", q)], TB[(f"B|{b}", q)]
        ds = sorted(set(A) & set(B))
        diff = lambda k: float(np.median([A[s][k] - B[s][k] for s in ds]))
        base = lambda k: max(float(np.median([B[s][k] for s in ds])), 1.0)
        out[str(q)] = {"ttc_pct": 100 * diff("ttc_net") / base("ttc_net"), "delay_pct": 100 * diff("all_delay") / base("all_delay"),
                       "ttc_ci_95_more": [-x for x in dc.raw(A, B, "ttc_net", pct=dc.P95)][::-1], "delay_ci_95_more": [-x for x in dc.raw(A, B, "all_delay", pct=dc.P95)][::-1]}
        dsum, bsum = dsum + diff("ttc_net"), bsum + base("ttc_net")
    tune = json.load(open(Path(__file__).parent / "3e/final.json"))["pick"]["name"]
    fin = json.load(open(Path(__file__).parent / "3e/final.json"))
    tuning = next(c for c in fin["candidates"] if c["name"] == tune)
    return {"per_level": out, "pooled_ttc_pct": 100 * dsum / bsum,
            "tuning_seeds": {"per_level": {q: {"ttc_pct": v["ttc_pct"], "delay_pct": v["delay_pct"]} for q, v in tuning["per_level"].items()},
                             "pooled_ttc_pct": tuning["ttc_pct"]}}


def read(T: dict, TB: dict, v: dict, TV: dict) -> dict:
    tested, inc = plan(v)
    fin = v["finalists"]
    p1, p2 = dc.bonferroni(max(len(fin), 1) * 2), dc.bonferroni((len(fin) + 1) * 2)
    o2 = opponents2()
    w_nm = dc.names("v3w", tested[-1][1])
    out = {"pct_T1": p1, "pct_T2": p2, "arms": {}, "e3_status": {c: dc.e3_status(T, c) for c in PRIMARY}}
    for kind, ch in tested:
        nm = dc.names(kind, ch)
        r = {"T2": {c: dc.d1.tuned(T, c, o2, nm, p2) for c in PRIMARY}, "T2_old_grid": {c: dc.d1.tuned(T, c, OPPONENTS, nm, p2) for c in PRIMARY},
             "beside": {c: dc.beside(T, c, nm, o2) for c in PRIMARY}, "severe_at_T2_level": {c: dc.severe_ok(T, c, nm, o2, p2) for c in PRIMARY}}
        r["noninferiority"] = {c: dc.noninferiority(T, c, nm, r["T2"][c]["counts"], p2) for c in PRIMARY}
        r["t2_cells"] = sum(x["won"] for x in r["T2"].values())
        r["t2_learners"] = sum(x["tuned"] for x in r["T2"].values())
        r["q2_answered"] = {c: any(n in r["T2"][c]["counts"] for n in out["e3_status"][c]) for c in PRIMARY}
        if kind != "v3w":
            r["T1"] = {c: dc.t1(T, c, nm, w_nm, p1) for c in PRIMARY}
            h = any(x["harm"] for x in r["T1"].values())     # harmed in either cell: better in neither
            for x in r["T1"].values():
                x["t1_better"] = x["better"] and not h
            r["score"] = max((x["score"] for x in r["T1"].values() if x["t1_better"]), default=-1e9)
        out["arms"][kind] = r
    inc_nm = dc.names("inc", inc[1])
    out["incumbent_report_only"] = {c: dc.d1.tuned(T, c, o2, inc_nm, p2) for c in PRIMARY}
    out["v3w_round1_checkpoints"] = {c: dc.d1.tuned(TV, c, o2, ["w0u250", "w1u250", "w2u500", "w3u500", "w4u500"], p2) for c in PRIMARY}
    out["closing"] = {c: {"counting_3e": any(n in out["arms"]["v3w"]["T2"][c]["counts"] for n in out["e3_status"][c]),
                          "won": any(r["T2"][c]["won"] for r in out["arms"].values())} for c in PRIMARY}
    for c, x in out["closing"].items():     # D10: a cell with a counting 3E rule that no tested arm wins closes
        x["closes"] = x["counting_3e"] and not x["won"]
    out["e3x_convergence"] = {c: dc.e3x_convergence(c) for c in PRIMARY}
    out["follows"] = dc.follows({k: r for k, r in out["arms"].items() if k != "v3w"}, out["arms"]["v3w"]["t2_cells"])
    out["no_control"] = {c: {m: dc.med(T[(f"{c}|nc", Q)], m) for m in ("ttc_net", "all_delay", "b3_step")} for c in PRIMARY}
    out["band"] = {k: dc.band_profile(TB, dc.names(k, ch)) for k, ch in [*tested, inc]}
    out["band_rules"] = {n: dc.band_profile(TB, [n]) for n in ("p333", RULE, "3e")}
    out["band_3e_vs_os1"] = per_level_vs(TB, "3e", RULE)
    return out


if __name__ == "__main__":
    mode, out = sys.argv[1], Path(sys.argv[2])
    v = json.load(open(sys.argv[-1]))
    g, gb = arms(v)
    if mode == "run":
        run_arms(g, (Q,), SEEDS_TEST, out / "test", int(sys.argv[4]), sys.argv[3])
        from common2e import BAND_EVAL as LV
        run_arms(gb, LV, SEEDS_BAND, out / "band", int(sys.argv[4]), sys.argv[3])
    T = load_union(sorted((out / "test").glob("rows_*.jsonl")), len(SEEDS_TEST), {k for a in g.values() for k in a})
    TB = load_union(sorted((out / "band").glob("rows_*.jsonl")), len(SEEDS_BAND), {k for a in gb.values() for k in a})
    sys.path.insert(0, str(Path(__file__).parent))
    import validate2
    TV = validate2.table(Path(sys.argv[-1]).parent)
    r = read(T, TB, v, TV)
    (out / "test_result.json").write_text(json.dumps(r, indent=1, default=str))
    for k, x in r["arms"].items():
        print(k, "T2", {c: (y["won"], y["tuned"], y["counts"]) for c, y in x["T2"].items()}, "Q2 answered", x["q2_answered"],
              "T1", {c: y["t1_better"] for c, y in x.get("T1", {}).items()}, flush=True)
    print("follows", r["follows"], flush=True)
