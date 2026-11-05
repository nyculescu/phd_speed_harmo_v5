"""Chooses the opponents on tuning seeds, as the protocol fixes them, and applies the early kill. usage: select_opp.py out_dir [copy_rule.json]. Exit 2: early kill."""
import json
import sys
from pathlib import Path

from common import PRIMARY, Q, collisions, effect, families, load, med


def admissible(T: dict, cell: str, rule: str) -> bool:
    A, P = T[(f"{cell}|{rule}", Q)], T[(f"{cell}|p333", Q)]
    return effect(A, P, "all_delay")[0] >= -2.0 and collisions(A) <= collisions(P) + 1


def choose(T: dict, fam: dict) -> dict:
    out = {"cells": {}}
    every = {r: k for rules in fam.values() for r, k in rules.items()}
    for cell in PRIMARY:
        ok = {f: [r for r in rules if admissible(T, cell, r)] for f, rules in fam.items()}
        forms = {f: min(rs, key=lambda r: med(T[(f"{cell}|{r}", Q)], "ttc_net")) for f, rs in ok.items() if rs}
        P = T[(f"{cell}|p333", Q)]
        close = [r for r in every if effect(T[(f"{cell}|{r}", Q)], P, "ttc_net")[0] >= -10.0]
        wide = [r for r in every if effect(T[(f"{cell}|{r}", Q)], P, "all_delay")[0] >= -10.0]
        out["cells"][cell] = {"forms": forms, "admissible": {f: len(rs) for f, rs in ok.items()},
                              "delay_opponent": min(close, key=lambda r: med(T[(f"{cell}|{r}", Q)], "all_delay")),
                              "front_row": min(wide, key=lambda r: med(T[(f"{cell}|{r}", Q)], "ttc_net"))}
    both = [r for r in every if all(admissible(T, c, r) for c in PRIMARY)]
    gain = {r: sum(effect(T[(f"{c}|{r}", Q)], T[(f"{c}|p333", Q)], "ttc_net")[0] for c in PRIMARY) / 2 for r in both}
    out["single_rule"] = max(gain, key=gain.get)
    out["ctrl"] = {r: every[r] for r in {out["single_rule"], "p333"} | {x for c in out["cells"].values() for x in (*c["forms"].values(), c["delay_opponent"], c["front_row"])}}
    return out


def early_kill(T: dict, fam: dict) -> list:
    """Rules beating no control on delay by at least 10 %, CI excluding 0, in a primary cell."""
    return [(c, r) for c in PRIMARY for rules in fam.values() for r in rules
            if (lambda e: e[0] >= 10.0 and e[1] > 0)(effect(T[(f"{c}|{r}", Q)], T[(f"{c}|nc", Q)], "all_delay"))]


if __name__ == "__main__":
    d = Path(sys.argv[1])
    fam = families()
    files = [d / "tune.jsonl"]
    if len(sys.argv) > 2:
        fam["copy"] = {"copy": json.load(open(sys.argv[2]))}
        files.append(d / "tune_copy.jsonl")
    T = load(*files)
    n = {f"{c}|{r}": len(T[(f"{c}|{r}", Q)]) for c in PRIMARY for rules in fam.values() for r in rules}
    assert set(n.values()) == {20}, {k: v for k, v in n.items() if v != 20}
    kill = early_kill(T, fam)
    print("rules beating no control on delay by 10 %:", len(kill), flush=True)
    if not kill:
        print("EARLY KILL: no rule beats no control", flush=True)
        sys.exit(2)
    o = choose(T, fam)
    json.dump(o, open(d / "opponents.json", "w"), indent=1)
    for c, x in o["cells"].items():
        print(c, x, flush=True)
    print("single rule", o["single_rule"], flush=True)
