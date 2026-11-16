"""Round 1 validation: each trained candidate and baseline-v3 at u250 and u500, with os1_15_10, p333 and no control, X1 and X2 at 5,300, 40 seeds.
Then the checkpoint rule, the advance rule, the floor and the finalists. usage: validate1.py run|read OUT WORKERS TRAINED_JSON
TRAINED_JSON maps each candidate that passed its training checks to its training directory."""
import json
import sys
from pathlib import Path

from common1 import LEARNERS, OPPONENTS, PREFIX, PRIMARY, Q, RULE, SEEDS_VAL, check_rows, incumbent, load, pt_cfg, rule_cfg
import decide1 as dc
from v5b.fleet import plant_sweep as ps

CKS = (250, 500)


def arms(trained: dict) -> dict:
    a = {f"{c}|d{i}u{ck}": pt_cfg(incumbent(i, f"u{ck}"), c) for c in PRIMARY for i in range(LEARNERS) for ck in CKS}
    for kind, d in trained.items():
        a |= {f"{c}|{PREFIX[kind]}{i}u{ck}": pt_cfg(Path(d) / f"C{i}_u{ck}.pt", c) for c in PRIMARY for i in range(LEARNERS) for ck in CKS}
    return a | {f"{c}|{n}": rule_cfg(k, c) for c in PRIMARY for n, k in {RULE: OPPONENTS["ctrl"][RULE], "p333": OPPONENTS["ctrl"]["p333"], "nc": {}}.items()}


def read(T: dict, trained: dict) -> dict:
    inc = {i: dc.choose(T, "d", i, CKS) for i in range(LEARNERS)}
    chosen = {k: {i: dc.choose(T, PREFIX[k], i, CKS) for i in range(LEARNERS)} for k in trained}
    res = {k: dc.advance(T, PREFIX[k], chosen[k], inc) for k in trained}
    return {"incumbent_chosen": inc, "chosen": chosen, "results": res, "finalists": dc.finalists(res)}


if __name__ == "__main__":
    mode, out, w, trained = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3]), json.load(open(sys.argv[4]))
    out.mkdir(parents=True, exist_ok=True)
    f = out / "validation.jsonl"
    if mode == "run":
        ps.matrix(arms(trained), (Q,), SEEDS_VAL, f, w, str(out / "rd"))
    T = load(f)
    check_rows(T, len(SEEDS_VAL))
    r = read(T, trained)
    (out / "validation.json").write_text(json.dumps(r, indent=1))
    for k, x in r["results"].items():
        print(k, "ADVANCES" if x["advances"] else "does not advance", {c: {"delay vs incumbent": v["delay_vs_incumbent"], "ttc vs rule": v["ttc_vs_rule"]} for c, v in x["cells"].items()},
              "harm", x["harm"], "floor", x["floor_kill"], flush=True)
    print("finalists:", r["finalists"] or "none: ROUND KILL, baseline-v3 stays, no test seed used", flush=True)
