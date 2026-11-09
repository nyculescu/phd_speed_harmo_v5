"""Plan B (planb.md §3.4): tune ASCH, the cell-agnostic two-regime scheduler. One configuration for every condition.
Stage 1: every configuration and p333 on seeds 7,480,230-249 in S and in every cell that passed S2. Admissible: in every
condition, close-following not above p333's (median paired difference at most 0) and collisions at most p333's + 1. Score: the
mean over conditions of the median paired delay change against p333 (%). Stage 2: the 5 best admissible re-run on 250-269 with
p333; the best admissible there is ASCH. None admissible: ASCH is a disclosed failed build.

usage: asch.py --out DIR --steady FILE --library FILE --conds S,SURGE,TRUCK [--workers N]
  --steady, --library: written by `plan6.py inputs` from repick.json and the 3E-C picks (the steady pick; 3E-T and each passing
  cell's 3E-C), so plan6 freeze can check them."""
import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pb  # noqa: E402

THETA, TAU, HYST = (40, 55, 70), (10, 30, 60), (5, 15)
TUNE, CHECK = pb.seeds(7_480_230, 7_480_249), pb.seeds(7_480_250, 7_480_269)
TOP = 5
REF = "p333"


def grid(steady: dict, library: dict) -> dict:
    out = {"never": steady}
    for th, tau, h, (rn, rd) in itertools.product(THETA, TAU, HYST, sorted(library.items())):
        out[f"t{th}_u{tau}_h{h}_{rn}"] = {"asch": {"steady": steady, "dist": rd, "theta_kmh": th, "tau_s": tau, "h_kmh": h}}
    return out


def score(rows: dict, names: list, conds: list, seed_list: list) -> list:
    """Per configuration: the score, admissibility and the per-condition parts, ranked best first."""
    out = []
    for n in names:
        parts = {}
        for c in conds:
            A = [rows[(f"{c}|{n}", s)] for s in seed_list]
            B = [rows[(f"{c}|{REF}", s)] for s in seed_list]
            cf = float(np.median([a["ttc_net"] - b["ttc_net"] for a, b in zip(A, B)]))
            parts[c] = {"delay_pct": pb.paired(A, B, "all_delay"), "cf_diff": cf, "coll": sum(a["collisions"] for a in A),
                        "coll_ref": sum(b["collisions"] for b in B)}
        ok = all(p["cf_diff"] <= 0.0 and p["coll"] <= p["coll_ref"] + 1 for p in parts.values())
        out.append({"name": n, "score": float(np.mean([p["delay_pct"] for p in parts.values()])), "admissible": ok, "parts": parts})
    return sorted(out, key=lambda r: (not r["admissible"], r["score"], r["name"]))


def tune(out: Path, steady: dict, library: dict, conds: list, workers: int, runner=pb.run_jobs) -> dict:
    g = grid(steady, library)
    cfgs = lambda names: {f"{c}|{n}": pb.cfg(g[n] if n != REF else pb.ref_ctrl(REF), c) for c in conds for n in names}
    meta = pb.guard(out, {"steady": steady, "library": library, "conds": conds}, cfgs(list(g) + [REF]), strict=runner is pb.run_jobs)
    r1 = pb.batch(cfgs(list(g) + [REF]), TUNE, out / "tune_runs.jsonl", out / "rd", workers, runner)
    s1 = score(r1, list(g), conds, TUNE)
    top = [r["name"] for r in s1 if r["admissible"]][:TOP]
    s2 = []
    if top:
        r2 = pb.batch(cfgs(top + [REF]), CHECK, out / "check_runs.jsonl", out / "rd", workers, runner)
        s2 = score(r2, top, conds, CHECK)
    best = next((r for r in s2 if r["admissible"]), None)
    res = {"conds": conds, "steady": steady, "library": library, "code": meta["code"], "n_configs": len(g), "stage1": s1, "stage2": s2,
           "pick": {"name": best["name"], "ctrl": g[best["name"]], "score": best["score"]} if best else None,
           "failed_build": best is None}
    pb.cma2.write_json(out / "asch.json", res)
    return res


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--steady", required=True)
    ap.add_argument("--library", required=True)
    ap.add_argument("--conds", required=True)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    conds = a.conds.split(",")
    if conds[0] != "S" or len(conds) < 2 or len(set(conds)) != len(conds) or not set(conds[1:]) <= set(pb.CELLS):
        ap.error("--conds is S followed by the cells that passed S2, each once")
    pb.reserve(a.workers)
    res = tune(Path(a.out), pb.load_json(a.steady), pb.load_json(a.library), conds, a.workers)
    print("ASCH:", res["pick"]["name"] if res["pick"] else "failed build (none admissible)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
