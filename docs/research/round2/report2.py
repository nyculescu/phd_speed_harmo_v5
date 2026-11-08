"""Round 2 report tables (report-only, from the stored rows; no simulation). The protocol's "reported beside" items that test2.py does not
write: every test arm's counters with no control beside, the TTC and severe splits by road, speed and period, where each tested arm's
close-following gain over the cell's strongest counting rule lies, the 1-Hz against step-braking check, the band levels, and 3E-X on its
tuning seeds beside validation and test (the overfitting check). usage: report2.py OUT REPORT_DIR"""
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from common2e import PRIMARY, Q, RULE, SEEDS_BAND, SEEDS_TEST, SEEDS_VAL, load_union
from common1 import collisions, effect, load, med, paired_median, val
import decide2 as dc
import test2

d3 = dc.d1.d3
P95 = (2.5, 97.5)
KEY = ("all_delay", "passed", "ttc_net", "ttc3", "sev3", "b3_step", "brake_net", "b7_step", "alks_full_moving", "ttc_half")
REFS = ("nc", "p333", RULE, "3e")
CI = "95 % percentile bootstrap (2.5, 97.5); T2 itself is read at its Bonferroni level in test_result.json"


def tested_arms(v: dict) -> dict:
    """Arm label -> policy names: the finalists, v3w and baseline-v3 at u500 (report-only)."""
    tested, inc = test2.plan(v)
    return {("baseline-v3" if k == "inc" else k) + " arm": dc.names(k, ch) for k, ch in [*tested, inc]}


def cell_arms(T: dict, cell: str, groups: dict, q: float = Q) -> dict:
    A = {lab: dc.arm(T, cell, nm, q) for lab, nm in groups.items()}
    for n in sorted({k[0].split("|")[1] for k in T if k[0].startswith(cell + "|") and k[1] == q}):
        A[n] = T[(f"{cell}|{n}", q)]
    return A


def gain_ci(A: dict, R: dict, key: str, n_boot: int = 20000) -> list:
    """Median of R minus A over paired seeds, in samples (positive = A has fewer), with a 95 % percentile bootstrap CI."""
    ds = sorted(set(A) & set(R))
    d = np.array([val(R[k], key) - val(A[k], key) for k in ds])
    b = np.median(d[np.random.default_rng(20261104).integers(0, len(d), (n_boot, len(d)))], axis=1)
    return [round(float(np.median(d)), 1), round(float(np.percentile(b, 2.5)), 1), round(float(np.percentile(b, 97.5)), 1)]


def row(A: dict, name: str, cell: str, q: float, refs: dict) -> dict:
    r = d3.row_of(A, name, cell, q) | {k: round(med(A, k), 1) for k in KEY} | {k: round(med(A, k), 1) for k in d3.SPLITS}
    if name.endswith(" arm"):     # the per-seed mean over 5 learners, so the sum is collisions per learner over the runs
        r["collisions_per_learner"] = r.pop("collisions_total")
    for ref, R in refs.items():
        if R is A:
            continue
        for key, sign, lab in (("ttc_net", -1, "ttc"), ("all_delay", -1, "delay"), ("passed", 1, "flow"), ("b3_step", -1, "brake")):
            r[f"{lab}_vs_{ref}_95"] = "{} [{}, {}]".format(*effect(A, R, key, sign, P95))
    return r


def write(path: Path, rows: list) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows)


def e3x_overfit(out: Path, TV: dict, T: dict, v: dict, tr: dict) -> dict:
    """3E-X against p333 on its 40 tuning seeds (final_runs.jsonl: "ref" is p333), on validation and on test; 95 %, positive = better.
    Each cell carries its counting status and the search's convergence flag, which the protocol puts beside every 3E-X result."""
    res = {}
    for c, x in (("X1", "3ex1"), ("X2", "3ex2")):
        d = out / f"cma3e_{x[2:]}"
        pick = json.load(open(d / "final.json"))["pick"]["name"]
        F = load(d / "final_runs.jsonl")
        tune = {"pick": F[(pick, Q)], "ref": F[("ref", Q)]}
        r = {"pick": pick, "tuning_seeds": len(tune["pick"]), "ci": CI, "convergence": tr["e3x_convergence"][c],
             "counts_at_validation": v["e3_status"][c][x]["counts"], "counts_at_test": tr["e3_status"][c][x]["counts"]}
        for phase, P, R in (("tuning", tune["pick"], tune["ref"]), ("validation", TV[(f"{c}|{x}", Q)], TV[(f"{c}|p333", Q)]),
                            ("test", T[(f"{c}|{x}", Q)], T[(f"{c}|p333", Q)])):
            r[phase] = {"ttc_vs_p333": effect(P, R, "ttc_net", -1, P95), "delay_vs_p333": effect(P, R, "all_delay", -1, P95),
                        "collisions": [collisions(P), collisions(R)], "seeds": len(set(P) & set(R))}
        for phase, TT in (("validation", TV), ("test", T)):
            P, R = TT[(f"{c}|{x}", Q)], TT[(f"{c}|{RULE}", Q)]
            r[phase] |= {f"ttc_vs_{RULE}": effect(P, R, "ttc_net", -1, P95), f"delay_vs_{RULE}": effect(P, R, "all_delay", -1, P95)}
        res[c] = r
    return res


def e3_side(T: dict, cell: str) -> dict:
    """Each 3E rule of the cell against p333 and os1_15_10 on test rows: the side metrics with paired values (95 %, positive = 3E better)."""
    out = {}
    for x in ("3e", "3ex1" if cell == "X1" else "3ex2"):
        P = T[(f"{cell}|{x}", Q)]
        for ref in ("p333", RULE):
            R = T[(f"{cell}|{ref}", Q)]
            out[f"{x}_vs_{ref}"] = {**{lab: effect(P, R, key, sign, P95) for key, sign, lab in
                                        (("all_delay", -1, "delay"), ("passed", 1, "flow"), ("b3_step", -1, "b3"), ("b7_step", -1, "b7"))},
                                     "full_moving_paired_median": paired_median(P, R, "alks_full_moving"),
                                     "full_moving_totals": [sum(val(a, "alks_full_moving") for a in P.values()), sum(val(a, "alks_full_moving") for a in R.values())],
                                     "collisions": [collisions(P), collisions(R)], "ci": CI}
    return out


def blind_list(T: dict) -> list:
    return [{"row": n, "q": q, "brake_1hz_over_step": b, "ttc_whole_over_half": t} for n, q, b, t in d3.blind_spots(T)]


def provenance() -> dict:
    here = Path(__file__).resolve()
    git = lambda *a: subprocess.run(["git", "-C", str(here.parent), *a], capture_output=True, text=True).stdout.strip()
    return {"script": "docs/research/round2/report2.py", "commit": git("log", "-1", "--format=%H", "--", here.name),
            "dirty": bool(git("status", "--porcelain", "--", here.name)), "sha256": hashlib.sha256(here.read_bytes()).hexdigest()}


if __name__ == "__main__":
    out, rep = Path(sys.argv[1]), Path(sys.argv[2])
    rep.mkdir(parents=True, exist_ok=True)
    v = json.load(open(out / "val/validation.json"))
    tr = json.load(open(out / "test_result.json"))
    groups = tested_arms(v)
    g, gb = test2.arms(v)
    T = load_union(sorted((out / "test").glob("rows_*.jsonl")), len(SEEDS_TEST), {k for a in g.values() for k in a})
    TB = load_union(sorted((out / "band").glob("rows_*.jsonl")), len(SEEDS_BAND), {k for a in gb.values() for k in a})
    TV = load_union(sorted((out / "val").glob("rows_*.jsonl")), len(SEEDS_VAL), set())
    blind = {"test": blind_list(T), "band": blind_list(TB), "validation": blind_list(TV),
             "limit": "single learner or rule rows over 5 %: 1-Hz against step braking where the step count is >= 50, "
                      "or whole against half-second TTC where the half-second count is >= 50"}
    print("1-Hz against step braking, whole against half-second TTC, rows over 5 %:", json.dumps(blind))
    rows, where, side = [], [], {}
    for c in PRIMARY:
        A = cell_arms(T, c, groups)
        x = "3ex1" if c == "X1" else "3ex2"
        counts = tr["arms"]["v3w"]["T2"][c]["counts"]
        refs = {n: A[n] for n in dict.fromkeys((*REFS, x, *counts))}
        for n, X in A.items():
            rows.append(row(X, n, c, Q, refs))
        strongest = min(counts, key=lambda n: med(A[n], "ttc_net"))
        against = list(dict.fromkeys((strongest, *[r for r in ("3e", x) if r in counts], "nc")))
        print(f"\n{c}: counting {counts}; strongest (lowest median TTC) {strongest}; where against {against}")
        print("arm", *KEY, "collisions (arm rows: per learner)", sep=" | ")
        for n in (*groups, *counts, *[r for r in (*REFS, x) if r not in counts]):
            print(n, *[round(med(A[n], k), 1) for k in KEY], round(collisions(A[n]), 1), sep=" | ")
        for lab in groups:
            for ref in against:
                w = {"cell": c, "arm": lab, "against": ref, "strongest": ref == strongest, "ci": CI,
                     "unit": "TTC samples per run (median of paired differences, reference minus arm; positive = arm fewer)"}
                w |= {k: gain_ci(A[lab], A[ref], k) for k in ("ttc_net", *[s for s in d3.SPLITS if s.startswith("ttc3")])}
                where.append(w)
                print("where", c, lab, "vs", ref, {k: w[k] for k in w if k.startswith("ttc")})
        side[c] = e3_side(T, c)
    write(rep / "test_table.csv", rows)
    json.dump(where, open(rep / "where_gain.json", "w"), indent=1)
    brows = []
    for q in sorted({k[1] for k in TB}):
        A = {lab: dc.arm(TB, "B", nm, q) for lab, nm in groups.items()} | {n: TB[(f"B|{n}", q)] for n in ("p333", RULE, "3e", "nc")}
        for n, X in A.items():
            r = {"q": q, "name": n, **{k: round(med(X, k), 1) for k in ("all_delay", "passed", "ttc_net", "sev3", "b3_step")},
                 ("collisions_per_learner" if n.endswith(" arm") else "collisions_total"): round(collisions(X), 1)}
            if n != "nc":
                r |= {f"{lab}_vs_nc_95": "{} [{}, {}]".format(*effect(X, A["nc"], key, -1, P95)) for key, lab in (("ttc_net", "ttc"), ("all_delay", "delay"))}
            brows.append(r)
    write(rep / "band_table.csv", brows)
    ov = e3x_overfit(out, TV, T, v, tr)
    print("\n3E-X tuning, validation, test against p333 (95 %, positive = better):", json.dumps(ov))
    print("\n3E side metrics against p333 and os1_15_10 (test, 95 %):", json.dumps(side))
    json.dump({"blind_spots": blind, "e3x_overfit": ov, "e3_side": side}, open(rep / "report_extra.json", "w"), indent=1)
    for f in ("val/validation.json", "test_result.json", "thesis_v459.json"):
        (rep / Path(f).name).write_text((out / f).read_text())
    json.dump({"source": str(out), "label_thesis": "thesis reading, V459, not a round-2 verdict", "made_by": provenance(),
               "ci_tables": CI, "note": "band_3e_vs_os1 in test_result.json stores its *_ci_95_more fields as [lo, hi, point]"},
              open(rep / "source.json", "w"), indent=1)
