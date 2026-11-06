"""Round 1, step 0: demand sweep that sets the training range (protocol round_1_sweep.md). Training slowdowns, 2,500-7,500 veh/h by 250,
no control, p333, os1_15_10 and baseline-v3's final policies, 10 seeds. usage: sweep1.py run|read OUT WORKERS [--no-policies]"""
import json
import sys
from pathlib import Path

import numpy as np

from common1 import LEARNERS, OPPONENTS, RULE, TRAINING_SLOWDOWNS, check_rows, incumbent, load, med, pt_cfg, raw, rule_cfg, val
from v5b.fleet import plant_sweep as ps

LEVELS = tuple(float(x) for x in range(2500, 7501, 250))
SEEDS = range(7_440_600, 7_440_610)
RULES = {"nc": {}, "p333": OPPONENTS["ctrl"]["p333"], RULE: OPPONENTS["ctrl"][RULE]}
P95 = (2.5, 97.5)


def arms(policies: bool = True) -> dict:
    a = {f"T|{n}": rule_cfg(k, "S", TRAINING_SLOWDOWNS) for n, k in RULES.items()}
    return a | ({f"T|d{i}": pt_cfg(incumbent(i, "final"), "S", TRAINING_SLOWDOWNS) for i in range(LEARNERS)} if policies else {})


def served(r: dict) -> float:
    """Vehicles entering road 4, past both merges, over the demand in the window."""
    return val(r, "passed") / (r["q"] * (r["steps"]) / 3600.0)


def read(T: dict, names: list) -> dict:
    per, controllable, clean = {}, [], []
    for q in LEVELS:
        A = {n: T[(f"T|{n}", q)] for n in names}
        nc = A["nc"]
        x = {n: {"delay": med(a, "all_delay"), "ttc": med(a, "ttc_net"), "served": float(np.median([served(r) for r in a.values()])),
                 "teleports": sum(val(r, "teleports") for r in a.values()), "collisions": sum(val(r, "collisions") for r in a.values())} for n, a in A.items()}
        for n in names:
            if n != "nc":
                x[n] |= {"delay_vs_nc": raw(A[n], nc, "all_delay", pct=P95), "ttc_vs_nc": raw(A[n], nc, "ttc_net", pct=P95)}
        hit = any(abs(e[0]) >= 10.0 and (e[1] > 0 or e[2] < 0) for n in ("p333", RULE) for e in (x[n]["delay_vs_nc"], x[n]["ttc_vs_nc"]))
        ok = all(x[n]["teleports"] == 0 and x[n]["collisions"] <= 2 for n in names) and max(x[n]["served"] for n in names) >= 0.90
        controllable += [q] if hit else []
        clean += [q] if ok else []
        per[str(q)] = {"arms": x, "controllable": hit, "clean": ok}
    lo = min(controllable) if controllable else None
    hi = max(clean) if clean else None
    rng = [lo, hi] if lo is not None and hi is not None and lo <= hi else None
    return {"levels": per, "L": lo, "U": hi, "range": rng, "note": None if rng else "no range: goes to the author"}


if __name__ == "__main__":
    mode, out, w = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
    pol = "--no-policies" not in sys.argv
    out.mkdir(parents=True, exist_ok=True)
    f = out / "sweep1.jsonl"
    if mode == "run":
        ps.matrix(arms(pol), LEVELS, SEEDS, f, w, str(out / "rd"))
    T = load(f)
    check_rows(T, len(SEEDS))
    names = [k.split("|")[1] for k in arms(pol)]
    r = read(T, names)
    (out / "sweep1.json").write_text(json.dumps(r, indent=1))
    print("controllable:", [q for q, x in r["levels"].items() if x["controllable"]], flush=True)
    print("clean:", [q for q, x in r["levels"].items() if x["clean"]], flush=True)
    print("training range:", r["range"] or r["note"], flush=True)
