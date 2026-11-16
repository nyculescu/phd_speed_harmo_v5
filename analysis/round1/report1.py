"""Round 1 report tables (report-only, from the stored rows; no simulation): every test arm's counters with no control beside, the TTC split
by road, speed and period, the 1-Hz against step-braking check, and the band levels. usage: report1.py OUT REPORT_DIR"""
import csv
import json
import sys
from pathlib import Path

from common1 import LEARNERS, OPPONENTS, PRIMARY, Q, BAND_EVAL, RULE, SEEDS_BAND, SEEDS_TEST, arm_mean, check_rows, collisions, effect, load, med
import decide1 as dc

d3 = dc.d3
P95 = (2.5, 97.5)
KEY = ("all_delay", "passed", "ttc_net", "ttc3", "sev3", "b3_step", "brake_net", "alks_full_moving", "ttc_half")


def arms_of(T: dict, cell: str, q: float = Q) -> dict:
    """Arm means of v3w and baseline-v3 (5 learners each), then every single policy and rule arm in the cell."""
    A = {"v3w arm": arm_mean(T, [f"{cell}|w{i}" for i in range(LEARNERS)], q), "baseline-v3 arm": arm_mean(T, [f"{cell}|d{i}" for i in range(LEARNERS)], q)}
    for n in sorted({k[0].split("|")[1] for k in T if k[0].startswith(cell + "|") and k[1] == q}):
        A[n] = T[(f"{cell}|{n}", q)]
    return A


def row(A: dict, name: str, cell: str, q: float, refs: dict) -> dict:
    r = d3.row_of(A, name, cell, q) | {k: round(med(A, k), 1) for k in ("ttc3", "brake_net", "ttc_half")} | {k: round(med(A, k), 1) for k in d3.SPLITS}
    for ref, R in refs.items():
        for key, sign, lab in (("ttc_net", -1, "ttc"), ("all_delay", -1, "delay"), ("passed", 1, "flow"), ("b3_step", -1, "brake")):
            e = effect(A, R, key, sign, P95)
            r[f"{lab}_vs_{ref}"] = f"{e[0]} [{e[1]}, {e[2]}]"
    return r


def write(path: Path, rows: list) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    out, rep = Path(sys.argv[1]), Path(sys.argv[2])
    rep.mkdir(parents=True, exist_ok=True)
    T, TB = load(out / "test" / "test.jsonl"), load(out / "test" / "band.jsonl")
    check_rows(T, len(SEEDS_TEST))
    check_rows(TB, len(SEEDS_BAND))
    print("1-Hz against step braking, whole against half-second TTC, arms over 5 %: test", d3.blind_spots(T), "band", d3.blind_spots(TB))
    rows = []
    for c in PRIMARY:
        A = arms_of(T, c)
        refs = {n: A[n] for n in ("nc", "p333", RULE)}
        for n, X in A.items():
            rows.append(row(X, n, c, Q, refs))
        print(f"\n{c} at {Q:.0f}: medians over {len(SEEDS_TEST)} runs; collisions summed (arm: mean over 5 learners)")
        print("arm", *KEY, "collisions", sep=" | ")
        for n in ("v3w arm", "baseline-v3 arm", *[k for k in OPPONENTS["ctrl"]], "nc"):
            print(n, *[round(med(A[n], k), 1) for k in KEY], round(collisions(A[n]), 1), sep=" | ")
        for n in ("v3w arm", "baseline-v3 arm", "p333", RULE, "nc"):
            print("split", c, n, {k: round(med(A[n], k), 1) for k in d3.SPLITS if k.startswith("ttc3")})
    write(rep / "test_table.csv", rows)
    brows = []
    for q in BAND_EVAL:
        A = {"v3w arm": arm_mean(TB, [f"B|w{i}" for i in range(LEARNERS)], q), "baseline-v3 arm": arm_mean(TB, [f"B|d{i}" for i in range(LEARNERS)], q),
             **{n: TB[(f"B|{n}", q)] for n in ("p333", RULE, "nc")}}
        for n, X in A.items():
            r = {"q": q, "name": n, **{k: round(med(X, k), 1) for k in ("all_delay", "passed", "ttc_net", "sev3", "b3_step")}, "collisions_total": round(collisions(X), 1)}
            if n != "nc":
                r |= {f"{lab}_vs_nc": "{} [{}, {}]".format(*effect(X, A["nc"], key, -1, P95)) for key, lab in (("ttc_net", "ttc"), ("all_delay", "delay"))}
            brows.append(r)
            print("band", q, n, {k: v for k, v in r.items() if k not in ("q", "name")})
    write(rep / "band_table.csv", brows)
    for f in ("val/validation.json", "test/test_result.json"):
        (rep / Path(f).name).write_text((out / f).read_text())
    json.dump({"source": str(out)}, open(rep / "source.json", "w"))
