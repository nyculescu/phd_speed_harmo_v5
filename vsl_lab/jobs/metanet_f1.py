"""F1, the single pre-registered structural fallback (protocol v3 §6.1, under protocol v4: seeds §A8, cells B1 u B2 =
28-31 u 33-34, T = 0.75 s, the §A3 rule, P11-k at F1's freeze, §A12). Runs ONLY if the base plant gate FAILs with the
§6.1 trigger; it is coded before any gate run so that its design does not postdate validation results.

python -m vsl_lab.jobs.metanet_f1 restart --seed 7191018 [--continue-to 8000]
python -m vsl_lab.jobs.metanet_f1 run --gate-ok          # 8 cold-start restarts (n + 2 = 19), continuation rule

Kept separate from metanet_calibrate.py so that the running base calibration never imports changed code.
"""
from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
import time

import numpy as np

from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.plants import metanet as M

NAMES_F1 = C.NAMES + ["Delta", "eta"]          # §A5 order, then Delta, eta
SEEDS_F1 = C.SEEDS_F1                          # 7,191,018-025 (§A8)
DELTA_ZERO_TOL = 0.01                          # §6.1: bound-active at 0 within 1 % of its range
PREFIX = "f1_"


def bounds() -> list:
    return M.param_bounds(NAMES_F1)


def to_params(X: np.ndarray) -> dict:
    X = np.atleast_2d(np.clip(X, 0.0, 1.0))
    out = {}
    for j, (n, (lo, hi)) in enumerate(zip(NAMES_F1, bounds())):
        x = X[:, j]
        out[n] = np.exp(np.log(lo) + x * (np.log(hi) - np.log(lo))) if n in C.LOG_SCALED else lo + x * (hi - lo)
    return out


def split_f1(params: dict) -> tuple:
    """(base parameters, f1 dict or None)."""
    if "Delta" not in params:
        return params, None
    base = {k: v for k, v in params.items() if k not in ("Delta", "eta")}
    return base, {"Delta": params["Delta"], "eta": params["eta"]}


def objective(X: np.ndarray, data: dict, net: M.Net, T_s: float = C.T_RUN, return_parts: bool = False):
    """§4.3 J with the F1 switch; §A3 pre-simulation check and graded penalty exactly as the base objective."""
    if net.variant not in C._THR:
        C._THR[net.variant] = C.a3_thresholds(net)
    params_all = to_params(X)
    short = C.a3_shortfall(params_all, C._THR[net.variant])
    feas = short <= 0.0
    J = 10.0 + short
    parts = {"Jd": None, "parts": None, "clip": None, "unscored_terms": 0, "inadmissible": ~feas,
             "a3_violation": ~feas, "a3_shortfall": short}
    if feas.any():
        idx = np.flatnonzero(feas)
        P, D = len(idx), data["d0"].shape[0]
        p = {k: v[idx] for k, v in params_all.items()}
        base, f1 = split_f1(p)
        o = M.simulate(net, base, M.Inputs(data["d0"], data["d_o"], data["beta"]), n_param_sets=P,
                       record_cells=False, T_s=T_s, f1=f1)
        qh = o.q_st.reshape(P, D, *o.q_st.shape[1:])
        vh = o.v_st.reshape(P, D, *o.v_st.shape[1:])
        nq, nv, nc = (C.nrmse_batch(qh, data["q"], data["mq"]), C.nrmse_batch(vh, data["v"], data["mv"]),
                      C.nrmse_batch(vh, data["v"], data["mc"]))
        w = np.array([0.25, 0.25, 0.5])
        pr = np.stack([nq, nv, nc], axis=-1)
        ok = np.isfinite(pr)
        Jd = (np.where(ok, pr, 0.0) * w).sum(-1) / (ok * w).sum(-1)
        Jf = Jd.mean(axis=1)
        bad = (o.clipped_share.reshape(P, D) > 0.01).any(axis=1) | o.nonfinite.reshape(P, D).any(axis=1) | \
            ~np.isfinite(Jf)
        J[idx] = np.where(bad, C.J_INADMISSIBLE, Jf)
        parts.update({"Jd": Jd, "parts": pr, "clip": o.clipped_share.reshape(P, D), "unscored_terms": int((~ok).sum()),
                      "feasible_index": idx})
        parts["inadmissible"] = ~feas
        parts["inadmissible"][idx] = bad
    return (J, parts) if return_parts else J


def restart(seed: int, continue_to: int | None = None) -> dict:
    """§6.1 refit: all base parameters plus Delta, eta, cold start (v3 §4.4 initial-mean rule), 4,000 evaluations."""
    import cma
    data = C.load_data()
    net = M.build_network(C.VARIANT)
    n = len(NAMES_F1)
    state = C.RUNS / f"{PREFIX}cma_state_{seed}.pkl"
    if continue_to:
        if not state.exists():
            raise RuntimeError(f"no F1 CMA state for seed {seed}: a continuation never cold-starts")
        es, hist, n_inadm, best, n_a3, first_feas = pickle.loads(state.read_bytes())
        budget = continue_to
    else:
        rng = np.random.default_rng(seed)
        es = cma.CMAEvolutionStrategy(rng.uniform(0.25, 0.75, n), 0.25, C.cma_options(seed, n))
        hist, n_inadm, best, n_a3, first_feas = [], 0, (np.inf, None), 0, None
        budget = C.BUDGET
    t0 = time.time()
    while es.countevals < budget:
        X = np.array(es.ask())
        J, parts = objective(X, data, net, return_parts=True)
        a3 = parts["a3_violation"]
        n_a3 += int(a3.sum())
        n_inadm += int(((J >= C.J_INADMISSIBLE) & ~a3).sum())
        if first_feas is None and (~a3).any():
            first_feas = int(es.countevals) + int(np.flatnonzero(~a3)[0]) + 1
        es.tell(list(X), list(J))
        i = int(np.argmin(J))
        if J[i] < best[0]:
            best = (float(J[i]), X[i].tolist())
        hist.append((int(es.countevals), float(J.min()), float(best[0]), float(es.sigma)))
    assert es.countevals >= budget
    state.write_bytes(pickle.dumps((es, hist, n_inadm, best, n_a3, first_feas)))
    evs = np.array([h[0] for h in hist])
    bj = np.array([h[2] for h in hist])
    j80 = bj[evs <= evs.max() * 0.8][-1] if (evs <= evs.max() * 0.8).any() else bj[0]
    bp = {k: float(v[0]) for k, v in to_params(np.array(best[1])).items()}
    lo, hi = M.BOUNDS["Delta"]
    res = {"protocol": C.PROTOCOL, "structure": "F1", "T_s": C.T_RUN, "seed": seed, "evals": int(es.countevals),
           "best_J": best[0], "best_x": best[1], "best_params": bp, "admissible": bool(best[0] < C.J_INADMISSIBLE),
           "delta_bound_active_at_zero": bool(bp["Delta"] - lo <= DELTA_ZERO_TOL * (hi - lo)),
           "final_sigma": float(es.sigma), "inadmissible_evals": n_inadm, "inadmissible_a3_evals": n_a3,
           "a3_violating_share": n_a3 / max(1, int(es.countevals)), "first_a3_feasible_eval": first_feas,
           "rel_improvement_last20pct": float((j80 - best[0]) / j80) if j80 > 0 else None,
           "wall_s": round(time.time() - t0, 1), "history": hist}
    (C.RUNS / f"{PREFIX}cma_restart_{seed}{'_cont' if continue_to else ''}.json").write_text(json.dumps(res))
    return res


def _batch(tag: str, suffix: str, extra: list, gate_ok: bool, commit: str) -> list:
    from vsl_lab.ops import ledger
    from vsl_lab.ops.scheduler import Job, run_batch
    for s in SEEDS_F1:
        (C.RUNS / f"{PREFIX}cma_restart_{s}{suffix}.json").unlink(missing_ok=True)
    jobs = [Job(jid=f"f1_cma_{s}{suffix}", argv=["vsl_lab.jobs.metanet_f1", "restart", "--seed", str(s)] + extra)
            for s in SEEDS_F1]
    rep, res, missing = None, [], []
    try:
        rep = run_batch(jobs, C.RUNS / f"batch_f1_cma{suffix}_{int(time.time())}", max_workers=8, gate_ok=gate_ok)
    finally:
        for s in SEEDS_F1:
            f = C.RUNS / f"{PREFIX}cma_restart_{s}{suffix}.json"
            (res.append(json.loads(f.read_text())) if f.exists() else missing.append(s))
        C.verify_v3()
        ledger.append("DP", "metanet-v4-f1", "S", f"metanet_v4_f1_cmaes{suffix or '_base'}",
                      {"seeds": SEEDS_F1, "budget": C.BUDGET, "T_s": C.T_RUN, "extra": extra, "code_commit": commit},
                      f"{SEEDS_F1[0]}-{SEEDS_F1[-1]} (optimizer); 22 calibration days; T = {C.T_RUN} s", len(SEEDS_F1),
                      {"proc_failed": rep.n_failed_proc if rep else None},
                      {"missing_seeds": missing, "J_by_seed": {r["seed"]: round(r["best_J"], 5) for r in res},
                       "v3_manifest_ok": True}, notes=f"F1 {tag}; second look on the same validation days")
    if missing:
        raise RuntimeError(f"F1 {tag}: no result for seeds {missing}")
    return res


def run(gate_ok: bool, continue_only: bool = False) -> dict:
    commit = C._code_commit()
    C.verify_v3()
    if continue_only:
        res_base = json.loads((C.RUNS / f"{PREFIX}cma_base_summary.json").read_text())["restarts_base"]
    else:
        res_base = _batch("base", "", [], gate_ok, commit)
        (C.RUNS / f"{PREFIX}cma_base_summary.json").write_text(json.dumps(
            {"code_commit": commit, "restarts_base": [{k: r[k] for k in r if k != "history"} for r in res_base]}))
    best = min(res_base, key=lambda r: r["best_J"])
    continued = bool(best["rel_improvement_last20pct"] is not None and best["rel_improvement_last20pct"] > 0.01)
    res = res_base
    if continued:
        if not (continue_only or C._wait_for_load()):
            raise SystemExit("F1 continuation pending: load gate (resume with run --continue-only --gate-ok)")
        res = _batch("continuation", "_cont", ["--continue-to", "8000"], continue_only and gate_ok, commit)
        best = min(res, key=lambda r: r["best_J"])
    summary = {"protocol": C.PROTOCOL, "structure": "F1", "label": "second look on the same validation days",
               "T_s": C.T_RUN, "names": NAMES_F1, "n_params": len(NAMES_F1), "budget": C.BUDGET,
               "continued_to_8000": continued, "code_commit": commit,
               "no_admissible_restart": bool(best["best_J"] >= C.J_INADMISSIBLE),
               "delta_bound_active_at_zero": best["delta_bound_active_at_zero"],
               "outcome_if_delta_zero": "base structure, second optimisation (a FAIL by default, §6.1)",
               "restarts": [{k: r[k] for k in r if k != "history"} for r in res],
               "restarts_base": [{k: r[k] for k in r if k != "history"} for r in res_base],
               "nominal_seed": best["seed"], "nominal_J": best["best_J"], "nominal_params": best["best_params"],
               "nominal_x": best["best_x"]}
    (C.RUNS / f"{PREFIX}cma_summary.json").write_text(json.dumps(summary, indent=1))
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["restart", "run"])
    ap.add_argument("--seed", type=int, default=SEEDS_F1[0])
    ap.add_argument("--continue-to", type=int, default=None)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--continue-only", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "restart":
        r = restart(a.seed, a.continue_to)
        print(json.dumps({k: r[k] for k in ("seed", "evals", "best_J", "wall_s", "delta_bound_active_at_zero")}))
    else:
        s = run(a.gate_ok, a.continue_only)
        print(json.dumps({k: s[k] for k in ("nominal_seed", "nominal_J", "delta_bound_active_at_zero")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
