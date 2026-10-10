"""METANET v5 calibration driver (protocol v5 §B2): CMA-ES on J5, v4's optimiser settings, seeds 7,192,010-017.
Calibration days only. Launch only after the facts commit, the premise check and the author's go (§B8).

python -m vsl_lab.jobs.metanet_v5_calibrate restart --seed 7192010
python -m vsl_lab.jobs.metanet_v5_calibrate restart --seed 7192010 --continue-to 8000
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import metanet_postcal as Q
from vsl_lab.jobs.metanet_j5_eval import J5Eval, J_INADMISSIBLE
from vsl_lab.plants import metanet as M

PROTOCOL = "docs/plans/day_pattern_metanet_protocol_v5.md"
RUNS5 = Path("/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet_v5")
FACTS5 = C.REPO / "docs" / "lab" / "day_pattern" / "metanet_v5_precal_facts.json"
FACTS5_SHA = C.REPO / "docs" / "lab" / "day_pattern" / "metanet_v5_precal_facts.sha256"
SEEDS = list(range(7192010, 7192018))
BUDGET = C.BUDGET


def evaluator(data: dict | None = None, net: M.Net | None = None) -> J5Eval:
    """The J5 evaluator on the committed facts (hash from the committed .sha256 file; J5 refuses otherwise)."""
    sha = FACTS5_SHA.read_text().split()[0]
    net = net or M.build_network(C.VARIANT)
    return J5Eval(FACTS5, sha, data if data is not None else C.load_data(), net, Q.part1()["c_s"])


def restart(seed: int, continue_to: int | None = None, ev: J5Eval | None = None, runs: Path = RUNS5) -> dict:
    import cma
    if seed not in SEEDS:
        raise SystemExit(f"seed {seed} is not a v5 restart seed (§B9)")
    ev = ev or evaluator()
    n = len(C.NAMES)
    runs.mkdir(parents=True, exist_ok=True)
    state = runs / f"cma_state_{seed}.pkl"
    if continue_to:
        if not state.exists():
            raise RuntimeError(f"no CMA state for seed {seed}: a continuation never cold-starts")
        es, hist, cnt, best = pickle.loads(state.read_bytes())
        budget = continue_to
    else:
        rng = np.random.default_rng(seed)
        x0 = rng.uniform(0.25, 0.75, n)
        es = cma.CMAEvolutionStrategy(x0, 0.25, C.cma_options(seed, n))
        hist, best = [], (np.inf, None, None)
        cnt = {"a3": 0, "inadm": 0, "evals_with_credit_B1": 0, "flat_generations": 0, "first_a3_feasible": None}
        budget = BUDGET
    t0 = time.time()
    while es.countevals < budget:
        X = np.array(es.ask())
        J, parts = ev(X, return_parts=True)
        cnt["a3"] += int((J > J_INADMISSIBLE).sum())                 # 10 + A3 shortfall (not simulated)
        cnt["inadm"] += int((J == J_INADMISSIBLE).sum())             # clipping / non-finite
        cnt["evals_with_credit_B1"] += int(sum(1 for p in parts if p and p["any_creditable_B1"]))
        adm = J[J < J_INADMISSIBLE]
        if adm.size >= 2 and np.ptp(adm) == 0.0:
            cnt["flat_generations"] += 1
        if cnt["first_a3_feasible"] is None and (J <= J_INADMISSIBLE).any():
            cnt["first_a3_feasible"] = int(es.countevals) + int(np.flatnonzero(J <= J_INADMISSIBLE)[0]) + 1
        es.tell(list(X), list(J))
        i = int(np.argmin(J))
        if J[i] < best[0]:
            best = (float(J[i]), X[i].tolist(), parts[i])
        hist.append((int(es.countevals), float(J.min()), float(best[0]), float(es.sigma)))
    state.write_bytes(pickle.dumps((es, hist, cnt, best)))
    evs = np.array([h[0] for h in hist])
    bj = np.array([h[2] for h in hist])
    cut = evs.max() * 0.8
    j80 = bj[evs <= cut][-1] if (evs <= cut).any() else bj[0]
    bx = np.array(best[1]) if best[1] is not None else None
    res = {"protocol": PROTOCOL, "objective": "J5", "T_s": C.T_RUN, "seed": seed, "evals": int(es.countevals),
           "best_J5": best[0], "best_x": best[1], "best_rows": best[2],
           "best_params": ({k: float(v[0]) for k, v in C.to_params(bx[None]).items()} if bx is not None else None),
           "bound_active": ([C.NAMES[j] for j in range(n) if bx[j] <= 1e-3 or bx[j] >= 1 - 1e-3]
                            if bx is not None else None),
           "admissible": bool(best[0] < J_INADMISSIBLE), "final_sigma": float(es.sigma), "counts": cnt,
           "share_evals_with_credit_B1": cnt["evals_with_credit_B1"] / max(1, int(es.countevals)),
           "rel_improvement_last20pct": float((j80 - best[0]) / j80) if j80 > 0 else None,
           "facts_sha256": hashlib.sha256(FACTS5.read_bytes()).hexdigest() if FACTS5.exists() else None,
           "wall_s": round(time.time() - t0, 1), "history": hist}
    (runs / f"cma_restart_{seed}{'_cont' if continue_to else ''}.json").write_text(json.dumps(res, default=float))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["restart"])
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--continue-to", type=int, default=None)
    a = ap.parse_args(argv)
    r = restart(a.seed, a.continue_to)
    print(json.dumps({k: r[k] for k in ("seed", "evals", "best_J5", "admissible", "wall_s")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
