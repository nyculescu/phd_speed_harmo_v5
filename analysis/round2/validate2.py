"""Round 2 validation (round_2.md): 40 fresh seeds, X1 and X2 at 5,300; checkpoints, ahead's KILL, advance, harm, floor and ranking.
usage: validate2.py run OUT RUN_COMMIT WORKERS | chosen OUT | killjob OUT | decide OUT"""
import json
import sys
from pathlib import Path

from common2e import (AHEAD_INPUTS, KILL_SEEDS, policy, CKS, LEARNERS, ORDER, PREFIX, PRIMARY, Q, SEEDS_VAL, TRAINED, cand_cfg, load_union, opponents2, rule_arms, run_arms,
                      snapshot_of)
import decide2 as dc

KINDS_CK = (*TRAINED, "v3w", "sw")     # arms with a checkpoint choice


def arms() -> dict:
    g = {}
    for c in PRIMARY:
        for kind in KINDS_CK:
            for i in range(LEARNERS):
                for ck in CKS:
                    g.setdefault(snapshot_of(kind), {})[f"{c}|{PREFIX[kind]}{i}u{ck}"] = cand_cfg(kind, i, ck, c)
        g.setdefault("eval", {}).update({f"{c}|t{i}": cand_cfg("tail", i, None, c) for i in range(LEARNERS)})
        g["eval"] |= rule_arms(c, c)
    return g


def table(out: Path) -> dict:
    expect = {k for a in arms().values() for k in a}
    return load_union(sorted(out.glob("rows_*.jsonl")), len(SEEDS_VAL), expect)


def chosen_all(T: dict) -> dict:
    return {k: {str(i): c for i, c in dc.choose_all(T, k).items()} for k in KINDS_CK}


if __name__ == "__main__":
    mode, out = sys.argv[1], Path(sys.argv[2])
    if mode == "run":
        run_arms(arms(), (Q,), SEEDS_VAL, out, int(sys.argv[4]), sys.argv[3])
        sys.exit(0)
    T = table(out)
    ch = chosen_all(T)
    if mode == "chosen":
        (out / "chosen.json").write_text(json.dumps(ch, indent=1))
        print("chosen", ch, flush=True)
        sys.exit(0)
    if mode == "killjob":     # ahead's KILL: its learners at their chosen checkpoints, traced on two validation seeds per cell
        runs = [{"name": f"{c}|h{i}u{ck}", "cfg": cand_cfg("ahead", i, ck, c), "q": Q, "seed": s, "learner": i, "pt": str(policy("ahead", i, ck)),
                 "stored": T[(f"{c}|h{i}u{ck}", Q)][s]} for c in PRIMARY for i, ck in ((int(i), x) for i, x in ch["ahead"].items()) for s in KILL_SEEDS]
        (out / "killjob.json").write_text(json.dumps({"runs": runs, "cols": list(AHEAD_INPUTS), "limit": 0.02, "rd": str(out / "rd_kill")}))
        sys.exit(0)
    imp = json.load(open(out / "importance.json"))
    o2 = opponents2()
    w = {int(i): c for i, c in ch["v3w"].items()}
    res = {}
    for k in ORDER:
        c = None if k == "tail" else {int(i): x for i, x in ch[k].items()}
        res[k] = dc.advance(T, k, c, w, o2, killed=(k == "ahead" and imp["killed"]))
    fin = dc.finalists(res)
    e3 = {c: dc.e3_status(T, c) for c in PRIMARY}
    r1 = {c: dc.d1.tuned(T, c, o2, ["w0u250", "w1u250", "w2u500", "w3u500", "w4u500"], dc.P95) for c in PRIMARY}     # report-only
    v = {"chosen": ch, "importance": imp, "results": res, "finalists": fin, "e3_status": e3, "v3w_round1_checkpoints_95": r1}
    (out / "validation.json").write_text(json.dumps(v, indent=1, default=str))
    for k, r in res.items():
        print(k, "ADVANCES" if r["advances"] else "out", "better", r["better"], "harm", r["harm"], "floor", r["floor_kill"], "count", r["count"],
              "score", r["score"], flush=True)
    print("finalists", fin, "| 3E counts:", {c: {n: x["counts"] for n, x in e.items()} for c, e in e3.items()}, flush=True)
