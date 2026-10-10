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


def timing_worker(gens: int, wid: int) -> dict:
    """§B12 re-measurement on SYNTHETIC model inputs (no candidate plant scored on real days): wall per generation
    of λ = 12 near the v4 nominal (A3-feasible), after a warm-up call."""
    data = C.load_data()
    net = M.build_network(C.VARIANT)
    syn = C.synthetic_inputs(net, D=len(data["days"]), seed=0)
    data = dict(data, d0=syn.d0, d_o=syn.d_o, beta=syn.beta)
    ev = evaluator(data, net) if FACTS5_SHA.exists() else _dev_evaluator(data, net)
    rng = np.random.default_rng(1000 + wid)                   # non-protocol synthetic seed
    x0 = np.array(Q.plant_record(None)["best_x"])
    ev(np.clip(x0 + rng.normal(0, 0.01, (2, 17)), 0, 1))
    walls = []
    for _ in range(gens):
        X = np.clip(x0 + rng.normal(0, 0.01, (12, 17)), 0, 1)
        t0 = time.time()
        ev(X)
        walls.append(time.time() - t0)
    return {"worker": wid, "walls": walls}


def _dev_evaluator(data, net):
    """Before the facts commit: the facts built in the raw directory (development and timing only)."""
    f = RUNS5 / "metanet_v5_precal_facts.json"
    return J5Eval(f, hashlib.sha256(f.read_bytes()).hexdigest(), data, net, Q.part1()["c_s"])


def timing(n_proc: int = 8, gens: int = 3, gate_ok: bool = False) -> dict:
    from vsl_lab.ops.scheduler import Job, run_batch
    root = RUNS5 / f"timing_{int(time.time())}"
    root.mkdir(parents=True, exist_ok=True)
    jobs = [Job(f"t{w}", ["vsl_lab.jobs.metanet_v5_calibrate", "timing-worker", "--gens", str(gens), "--wid", str(w)])
            for w in range(n_proc)]
    rep = run_batch(jobs, root / "batch", n_proc, gate_ok=gate_ok)
    walls = [w for r in rep.results if r["result"] for w in r["result"]["walls"]]
    per_gen = float(np.median(walls))
    gens_base, gens_cont = int(np.ceil(BUDGET / 12)), int(np.ceil(8000 / 12))
    out = {"n_proc": n_proc, "per_generation_s_median": per_gen, "per_generation_s": walls,
           "restart_h_base": per_gen * gens_base / 3600, "restart_h_with_continuation": per_gen * gens_cont / 3600,
           "max_temp_c": rep.max_temp_c, "n_pauses": rep.n_pauses, "note": "synthetic model inputs; guard pauses excluded"}
    (root / "timing.json").write_text(json.dumps(out, indent=1))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["restart", "timing", "timing-worker"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--continue-to", type=int, default=None)
    ap.add_argument("--gens", type=int, default=3)
    ap.add_argument("--wid", type=int, default=0)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "timing-worker":
        print(json.dumps(timing_worker(a.gens, a.wid)))
        return 0
    if a.what == "timing":
        print(json.dumps({k: v for k, v in timing(gens=a.gens, gate_ok=a.gate_ok).items() if k != "per_generation_s"}))
        return 0
    r = restart(a.seed, a.continue_to)
    print(json.dumps({k: r[k] for k in ("seed", "evals", "best_J5", "admissible", "wall_s")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
