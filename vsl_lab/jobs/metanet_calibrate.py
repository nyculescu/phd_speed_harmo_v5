"""U.S.169 SB METANET calibration (protocol v3 §4.1-4.4; binding).

python -m vsl_lab.jobs.metanet_calibrate prep                    # inputs + fit targets of the usable calibration days
python -m vsl_lab.jobs.metanet_calibrate restart --seed 7190011  # one CMA-ES restart (4,000 evaluations)
python -m vsl_lab.jobs.metanet_calibrate restart --seed 7190011 --continue-to 8000
python -m vsl_lab.jobs.metanet_calibrate run --gate-ok           # 8 restarts in parallel, convergence rule, summary

Geometry: §1.7 step (b) (F16 flagged, no lane check, D3.7) -> 'step_b' network with G4 on cells 33-36;
n = 15 + 2 = 17 parameters (rc4, a4; v_f,G4 tied to G3). F7 gave 'base' at both bottlenecks: no EXIT branch.
"""
from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
import time
from pathlib import Path

import numpy as np

from vsl_lab.plants import metanet as M

RUNS = Path("/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet")
REPO = Path(__file__).resolve().parents[2]
FACTS = REPO / "docs" / "lab" / "day_pattern" / "metanet_precal_facts.json"
NAMES = M.PARAM_NAMES + ["rc4", "a4"]
LOG_SCALED = {"tau", "nu", "kappa"}
SEEDS = list(range(7190011, 7190019))
BUDGET = 4000
VARIANT = "step_b"
J_INADMISSIBLE = 10.0


# ---------------------------------------------------------------- parameter mapping (§4.4)
def bounds():
    return M.param_bounds(NAMES)


def to_params(X: np.ndarray) -> dict:
    """Normalised [0,1]^n (rows = population) -> parameter dict of arrays."""
    X = np.atleast_2d(np.clip(X, 0.0, 1.0))
    out = {}
    for j, (n, (lo, hi)) in enumerate(zip(NAMES, bounds())):
        x = X[:, j]
        out[n] = np.exp(np.log(lo) + x * (np.log(hi) - np.log(lo))) if n in LOG_SCALED else lo + x * (hi - lo)
    return out


def to_norm(p: dict) -> np.ndarray:
    v = []
    for n, (lo, hi) in zip(NAMES, bounds()):
        x = float(np.asarray(p[n]).ravel()[0])
        v.append((math.log(x) - math.log(lo)) / (math.log(hi) - math.log(lo)) if n in LOG_SCALED else (x - lo) / (hi - lo))
    return np.array(v)


# ---------------------------------------------------------------- data (calibration days only)
def prep() -> Path:
    p1 = json.loads((RUNS / "precal_part1.json").read_text())
    return build_data(p1["usable"]["calibration"], RUNS / "calib_data.npz")


def build_data(days: list, out: Path, exit_flows: bool = False) -> Path:
    """Replay inputs and fit-layer targets for a day list (frozen §3 references from part 1)."""
    from vsl_lab.data import metanet_inputs as I
    p1 = json.loads((RUNS / "precal_part1.json").read_text())
    net = M.build_network(VARIANT)
    sl, cs, unrel, src = p1["speed_lanes"], p1["c_s"], set(p1["unreliable"]), p1["sources"]
    st_ids = [s["id"] for s in net.stations]
    d0, d_o, beta, q, v, mq, mv, mc, xq = ([] for _ in range(9))
    for d in days:
        mi = I.model_inputs(d, src, unrel, net)
        if not mi["valid"]:
            raise RuntimeError(f"usable day {d} has invalid inputs: {mi['why']}")
        ft = I.fit_targets(d, sl, cs, unrel)
        d0.append(mi["d0"])
        d_o.append(mi["d_o"])
        beta.append(mi["beta"])
        xq.append(mi["x_q"])
        rows = {k: [] for k in ("q", "v", "mq", "mv", "mc")}
        for sid in st_ids:
            s = ft["stations"].get(sid)
            if s is None:
                rows["q"].append(np.full(M.N_BINS, np.nan))
                rows["v"].append(np.full(M.N_BINS, np.nan))
                for k in ("mq", "mv", "mc"):
                    rows[k].append(np.zeros(M.N_BINS, bool))
            else:
                rows["q"].append(s["q"])
                rows["v"].append(s["v"])
                rows["mq"].append(s["q_mask"])
                rows["mv"].append(s["v_mask"])
                rows["mc"].append(s["c_mask"])
        q.append(rows["q"]); v.append(rows["v"]); mq.append(rows["mq"]); mv.append(rows["mv"]); mc.append(rows["mc"])
    extra = {"x_q": np.array(xq)} if exit_flows else {}
    np.savez_compressed(out, d0=np.array(d0), d_o=np.array(d_o), beta=np.array(beta), q=np.array(q, float),
                        v=np.array(v, float), mq=np.array(mq), mv=np.array(mv), mc=np.array(mc),
                        days=np.array(days), stations=np.array(st_ids), **extra)
    return out


def load_data():
    z = np.load(RUNS / "calib_data.npz")
    return {k: z[k] for k in z.files}


# ---------------------------------------------------------------- objective (§4.2-4.3)
def nrmse_batch(xhat, x, mask):
    """xhat (P, D, ns, bins), x/mask (D, ns, bins) -> (P, D) NRMSE; NaN where < 100 pairs."""
    m = mask[None] & np.isfinite(xhat) & np.isfinite(x)[None]
    n = m.sum(axis=(2, 3))
    xx = np.where(m, x[None], 0.0)
    se = np.where(m, (xhat - x[None]) ** 2, 0.0).sum(axis=(2, 3))
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.sqrt(se / n) / (xx.sum(axis=(2, 3)) / n)
    return np.where(n >= 100, r, np.nan)


def objective(X: np.ndarray, data: dict, net: M.Net, T_s: float = M.T_S, return_parts: bool = False):
    P = X.shape[0]
    D = data["d0"].shape[0]
    params = to_params(X)
    inp = M.Inputs(data["d0"], data["d_o"], data["beta"])
    o = M.simulate(net, params, inp, n_param_sets=P, record_cells=False, T_s=T_s)
    qh = o.q_st.reshape(P, D, *o.q_st.shape[1:])
    vh = o.v_st.reshape(P, D, *o.v_st.shape[1:])
    nq = nrmse_batch(qh, data["q"], data["mq"])
    nv = nrmse_batch(vh, data["v"], data["mv"])
    nc = nrmse_batch(vh, data["v"], data["mc"])
    w = np.array([0.25, 0.25, 0.5])
    parts = np.stack([nq, nv, nc], axis=-1)                       # (P, D, 3)
    ok = np.isfinite(parts)
    Jd = (np.where(ok, parts, 0.0) * w).sum(-1) / (ok * w).sum(-1)   # renormalised over scored terms (counted)
    J = Jd.mean(axis=1)
    clip = o.clipped_share.reshape(P, D)
    nonfin = o.nonfinite.reshape(P, D)
    bad = (clip > 0.01).any(axis=1) | nonfin.any(axis=1) | ~np.isfinite(J)
    J = np.where(bad, J_INADMISSIBLE, J)
    if return_parts:
        return J, {"Jd": Jd, "parts": parts, "clip": clip, "unscored_terms": int((~ok).sum()), "inadmissible": bad}
    return J


# ---------------------------------------------------------------- one restart (§4.4)
def cma_options(seed: int, n: int) -> dict:
    lam = 4 + int(math.floor(3 * math.log(n)))
    return {"bounds": [0.0, 1.0], "seed": seed, "popsize": lam, "verbose": -9, "tolfun": 0, "tolx": 0,
            "tolfunhist": 0, "tolstagnation": 10 ** 9, "tolflatfitness": 10 ** 9, "tolconditioncov": np.inf,
            "tolupsigma": np.inf, "tolfunrel": 0}


def restart(seed: int, continue_to: int | None = None) -> dict:
    import cma
    data = load_data()
    net = M.build_network(VARIANT)
    n = len(NAMES)
    state = RUNS / f"cma_state_{seed}.pkl"
    if continue_to and state.exists():
        es, hist, n_inadm, best = pickle.loads(state.read_bytes())
        budget = continue_to
    else:
        rng = np.random.default_rng(seed)
        x0 = rng.uniform(0.25, 0.75, n)
        es = cma.CMAEvolutionStrategy(x0, 0.25, cma_options(seed, n))
        hist, n_inadm, best = [], 0, (np.inf, None)
        budget = BUDGET
    t0 = time.time()
    while es.countevals < budget:
        X = np.array(es.ask())
        J = objective(X, data, net)
        n_inadm += int((J >= J_INADMISSIBLE).sum())
        es.tell(list(X), list(J))
        i = int(np.argmin(J))
        if J[i] < best[0]:
            best = (float(J[i]), X[i].tolist())
        hist.append((int(es.countevals), float(J.min()), float(best[0]), float(es.sigma)))
    state.write_bytes(pickle.dumps((es, hist, n_inadm, best)))
    evs = np.array([h[0] for h in hist])
    bj = np.array([h[2] for h in hist])
    cut = evs.max() * 0.8
    j80 = bj[evs <= cut][-1] if (evs <= cut).any() else bj[0]
    try:
        cond = float(es.D.max() ** 2 / es.D.min() ** 2)
    except Exception:
        cond = None
    res = {"seed": seed, "evals": int(es.countevals), "best_J": best[0], "best_x": best[1],
           "best_params": {k: float(v[0]) for k, v in to_params(np.array(best[1])).items()},
           "final_sigma": float(es.sigma), "cov_condition": cond, "inadmissible_evals": n_inadm,
           "rel_improvement_last20pct": float((j80 - best[0]) / j80) if j80 > 0 else None,
           "wall_s": round(time.time() - t0, 1), "history": hist}
    (RUNS / f"cma_restart_{seed}{'_cont' if continue_to else ''}.json").write_text(json.dumps(res))
    return res


# ---------------------------------------------------------------- driver
def run(gate_ok: bool) -> dict:
    from vsl_lab.ops import ledger
    from vsl_lab.ops.scheduler import Job, run_batch
    jobs = [Job(jid=f"cma_{s}", argv=["vsl_lab.jobs.metanet_calibrate", "restart", "--seed", str(s)]) for s in SEEDS]
    rep = run_batch(jobs, RUNS / f"batch_cma_{int(time.time())}", max_workers=8, gate_ok=gate_ok)
    res = [json.loads((RUNS / f"cma_restart_{s}.json").read_text()) for s in SEEDS]
    best = min(res, key=lambda r: r["best_J"])
    continued = False
    if best["rel_improvement_last20pct"] is not None and best["rel_improvement_last20pct"] > 0.01:
        continued = True
        jobs = [Job(jid=f"cma_{s}_c", argv=["vsl_lab.jobs.metanet_calibrate", "restart", "--seed", str(s),
                                             "--continue-to", "8000"]) for s in SEEDS]
        run_batch(jobs, RUNS / f"batch_cma_cont_{int(time.time())}", max_workers=8, gate_ok=True)
        res = [json.loads((RUNS / f"cma_restart_{s}_cont.json").read_text()) for s in SEEDS]
        best = min(res, key=lambda r: r["best_J"])
    summary = {"variant": VARIANT, "n_params": len(NAMES), "names": NAMES, "budget": BUDGET, "continued_to_8000": continued,
               "restarts": [{k: r[k] for k in r if k != "history"} for r in res], "nominal_seed": best["seed"],
               "nominal_J": best["best_J"], "nominal_params": best["best_params"]}
    (RUNS / "cma_summary.json").write_text(json.dumps(summary, indent=1))
    ledger.append("DP", "metanet-calib", "S", "metanet_cmaes_restarts", {"seeds": SEEDS, "budget": BUDGET, "variant": VARIANT},
                  "7190011-7190018 (optimizer); 22 calibration days", len(SEEDS),
                  {"proc_failed": rep.n_failed_proc},
                  {"nominal_seed": best["seed"], "nominal_J": round(best["best_J"], 5), "continued": continued,
                   "J_by_seed": {r["seed"]: round(r["best_J"], 5) for r in res}}, notes=str(RUNS / "cma_summary.json"))
    return summary


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["prep", "restart", "run", "time"])
    ap.add_argument("--seed", type=int, default=SEEDS[0])
    ap.add_argument("--continue-to", type=int, default=None)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "prep":
        print(prep())
    elif a.what == "restart":
        r = restart(a.seed, a.continue_to)
        print(json.dumps({k: r[k] for k in ("seed", "evals", "best_J", "wall_s", "inadmissible_evals")}))
    elif a.what == "time":
        data = load_data()
        net = M.build_network(VARIANT)
        X = np.random.default_rng(0).uniform(0.25, 0.75, (12, len(NAMES)))
        t = time.time()
        J, parts = objective(X, data, net, return_parts=True)
        print(json.dumps({"s_per_generation": round(time.time() - t, 1), "J": [round(x, 4) for x in J],
                          "unscored_terms": parts["unscored_terms"]}))
    else:
        s = run(a.gate_ok)
        print(json.dumps({k: s[k] for k in ("nominal_seed", "nominal_J", "continued_to_8000")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
