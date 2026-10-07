"""U.S.169 SB METANET calibration, protocol v4 (= v3 §4.1-4.4 with the v4 amendments; binding). v3's code is at
git tag metanet-v3-stop.

python -m vsl_lab.jobs.metanet_calibrate prep                    # inputs + fit targets (rebuilt; must equal v3's)
python -m vsl_lab.jobs.metanet_calibrate restart --seed 7191010  # one CMA-ES restart (4,000 evaluations)
python -m vsl_lab.jobs.metanet_calibrate restart --seed 7191010 --continue-to 8000
python -m vsl_lab.jobs.metanet_calibrate run --gate-ok           # 8 restarts in parallel, convergence rule, summary
python -m vsl_lab.jobs.metanet_calibrate time                    # synthetic-input timing (§A9; no real day)

Geometry: v4 §A1/§A4 step (b) -> 'v4' network (39 cells, G4 = cells 36-39, E15 lane-adding); T = 0.75 s (§A2);
n = 17 (v_f,G1-G3, rho_cr,G1-G3, a_G1-G3, tau, nu, kappa, delta_m, phi, theta1, rho_cr,G4, a_G4); §A3 speed at capacity.
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

PROTOCOL = "v4"
V3_RUNS = Path("/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet")       # v3 raw dir: read-only (§A9)
RUNS = Path("/home/catalin/work/phd/vsl_lab_runs/day_pattern/metanet_v4")
REPO = Path(__file__).resolve().parents[2]
FACTS = REPO / "docs" / "lab" / "day_pattern" / "metanet_precal_facts.json"         # v3 facts, reused read-only
FACTS_V4 = REPO / "docs" / "lab" / "day_pattern" / "metanet_v4_precal_facts.json"
V3_MANIFEST = REPO / "docs" / "lab" / "day_pattern" / "metanet_v3_raw_manifest.sha256"
NAMES = M.PARAM_NAMES + ["rc4", "a4"]
LOG_SCALED = {"tau", "nu", "kappa"}
SEEDS = list(range(7191010, 7191018))       # §A8
SEEDS_F1 = list(range(7191018, 7191026))
BUDGET = 4000
VARIANT = "v4"
T_RUN = M.T_S_V4
J_INADMISSIBLE = 10.0
MPH = 1.609344


# ---------------------------------------------------------------- v3 inputs (read-only, verified, §A9)
def verify_v3(names: list[str] | None = None) -> None:
    """sha256 of the reused v3 raw files against the committed manifest; a mismatch stops the run."""
    import hashlib
    man = {}
    for line in V3_MANIFEST.read_text().splitlines():
        h, f = line.split(None, 1)
        man[f.lstrip("./").strip()] = h
    for f in (names if names is not None else man):
        h = hashlib.sha256((V3_RUNS / f).read_bytes()).hexdigest()
        if man.get(f) != h:
            raise RuntimeError(f"v3 raw file changed or missing: {f}")


def part1() -> dict:
    verify_v3(["precal_part1.json"])
    return json.loads((V3_RUNS / "precal_part1.json").read_text())


# ---------------------------------------------------------------- §A3 speed at capacity
def a3_thresholds(net: M.Net, cs: dict | None = None) -> dict:
    """thr_g (km/h) = max over event-layer stations read in FD group g of 40 mph x c_s (full precision)."""
    from vsl_lab.data import metanet_inputs as I
    cs = cs if cs is not None else part1()["c_s"]
    thr = {}
    for s in net.stations:
        if s["id"] not in I.EVENT_STATIONS or s["id"] not in cs:
            continue
        g = int(net.group[s["cell"]])
        thr[g] = max(thr.get(g, 0.0), 40.0 * MPH * cs[s["id"]]["c_s"])
    return thr


def a3_shortfall(params: dict, thr: dict) -> np.ndarray:
    """Sum over groups of max(0, thr_g - v_c,g)/thr_g; v_c,g = v_f,g exp(-1/a_g); G4 ties v_f to G3."""
    vf = {0: params["vf1"], 1: params["vf2"], 2: params["vf3"], 3: params["vf3"]}
    a = {0: params["a1"], 1: params["a2"], 2: params["a3"], 3: params["a4"]}
    out = 0.0
    for g, t in thr.items():
        vc = np.asarray(vf[g], float) * np.exp(-1.0 / np.asarray(a[g], float))
        out = out + np.maximum(0.0, t - vc) / t
    return np.atleast_1d(out)


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
    """§A9: rebuild calib_data.npz into the v4 directory; it must equal v3's array for array."""
    p1 = part1()
    RUNS.mkdir(parents=True, exist_ok=True)
    out = build_data(p1["usable"]["calibration"], RUNS / "calib_data.npz")
    verify_v3(["calib_data.npz"])
    a, b = np.load(out), np.load(V3_RUNS / "calib_data.npz")
    diff = [k for k in sorted(set(a.files) | set(b.files))
            if k not in a.files or k not in b.files or not np.array_equal(a[k], b[k], equal_nan=True)]
    if diff:
        raise RuntimeError(f"rebuilt calib_data.npz differs from v3's in {diff}: logged deviation, author decides")
    return out


def build_data(days: list, out: Path, exit_flows: bool = False) -> Path:
    """Replay inputs and fit-layer targets for a day list (frozen §3 references from part 1)."""
    from vsl_lab.data import metanet_inputs as I
    p1 = part1()
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


_THR: dict = {}


def objective(X: np.ndarray, data: dict, net: M.Net, T_s: float = T_RUN, return_parts: bool = False):
    """§4.3 J; §A3: violators are not simulated and get J = 10 + sum of relative shortfalls."""
    if net.variant not in _THR:
        _THR[net.variant] = a3_thresholds(net)
    params_all = to_params(X)
    short = a3_shortfall(params_all, _THR[net.variant])
    feas = short <= 0.0
    J = 10.0 + short
    parts_out = {"Jd": None, "parts": None, "clip": None, "unscored_terms": 0,
                 "inadmissible": ~feas, "a3_violation": ~feas, "a3_shortfall": short}
    if feas.any():
        Jf, pf = _objective_sim(X[feas], data, net, T_s)
        J[feas] = Jf
        parts_out.update({k: pf[k] for k in ("Jd", "parts", "clip", "unscored_terms")})
        parts_out["inadmissible"] = ~feas
        parts_out["inadmissible"][np.flatnonzero(feas)] = pf["inadmissible"]
        parts_out["feasible_index"] = np.flatnonzero(feas)
    if return_parts:
        return J, parts_out
    return J


def _objective_sim(X: np.ndarray, data: dict, net: M.Net, T_s: float):
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
    return J, {"Jd": Jd, "parts": parts, "clip": clip, "unscored_terms": int((~ok).sum()), "inadmissible": bad}


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
    RUNS.mkdir(parents=True, exist_ok=True)
    if continue_to and state.exists():
        es, hist, n_inadm, best, n_a3, first_feas = pickle.loads(state.read_bytes())
        budget = continue_to
    else:
        rng = np.random.default_rng(seed)
        x0 = rng.uniform(0.25, 0.75, n)
        es = cma.CMAEvolutionStrategy(x0, 0.25, cma_options(seed, n))
        hist, n_inadm, best, n_a3, first_feas = [], 0, (np.inf, None), 0, None
        budget = BUDGET
    t0 = time.time()
    while es.countevals < budget:
        X = np.array(es.ask())
        J, parts = objective(X, data, net, return_parts=True)
        a3 = parts["a3_violation"]
        n_a3 += int(a3.sum())                                     # inadmissible (A3), counted separately (§A3 (b))
        n_inadm += int(((J >= J_INADMISSIBLE) & ~a3).sum())       # clipping / non-finite
        if first_feas is None and (~a3).any():
            first_feas = int(es.countevals) + int(np.flatnonzero(~a3)[0]) + 1
        es.tell(list(X), list(J))
        i = int(np.argmin(J))
        if J[i] < best[0]:
            best = (float(J[i]), X[i].tolist())
        hist.append((int(es.countevals), float(J.min()), float(best[0]), float(es.sigma)))
    state.write_bytes(pickle.dumps((es, hist, n_inadm, best, n_a3, first_feas)))
    evs = np.array([h[0] for h in hist])
    bj = np.array([h[2] for h in hist])
    cut = evs.max() * 0.8
    j80 = bj[evs <= cut][-1] if (evs <= cut).any() else bj[0]
    try:
        cond = float(es.D.max() ** 2 / es.D.min() ** 2)
    except Exception:
        cond = None
    bp = {k: float(v[0]) for k, v in to_params(np.array(best[1])).items()}
    thr = a3_thresholds(net)
    vf = {0: bp["vf1"], 1: bp["vf2"], 2: bp["vf3"], 3: bp["vf3"]}
    aa = {0: bp["a1"], 1: bp["a2"], 2: bp["a3"], 3: bp["a4"]}
    a3rep = {f"G{g + 1}": {"vc_minus_thr": vf[g] * math.exp(-1 / aa[g]) - t,
                           "a3_active": bool(vf[g] * math.exp(-1 / aa[g]) - t <= 0.01 * t)} for g, t in thr.items()}
    res = {"protocol": PROTOCOL, "T_s": T_RUN, "seed": seed, "evals": int(es.countevals), "best_J": best[0],
           "best_x": best[1], "best_params": bp, "admissible": bool(best[0] < J_INADMISSIBLE),
           "final_sigma": float(es.sigma), "cov_condition": cond, "inadmissible_evals": n_inadm,
           "inadmissible_a3_evals": n_a3, "a3_violating_share": n_a3 / max(1, int(es.countevals)),
           "first_a3_feasible_eval": first_feas, "a3_at_best": a3rep,
           "rel_improvement_last20pct": float((j80 - best[0]) / j80) if j80 > 0 else None,
           "wall_s": round(time.time() - t0, 1), "history": hist}
    (RUNS / f"cma_restart_{seed}{'_cont' if continue_to else ''}.json").write_text(json.dumps(res))
    return res


# ---------------------------------------------------------------- synthetic timing (§A9; no real day)
def synthetic_inputs(net: M.Net, D: int = 22, seed: int = 0) -> M.Inputs:
    """Smooth synthetic days (AM/PM peaks); rng seed 0 is a timing-only stream, not a protocol seed."""
    rng = np.random.default_rng(seed)
    h = 4.0 + np.arange(M.N_BINS) / 12.0
    prof = 0.55 + 0.25 * np.exp(-((h - 7.5) / 1.2) ** 2) + 0.45 * np.exp(-((h - 16.8) / 1.5) ** 2)
    lvl = rng.uniform(0.9, 1.1, (D, 1))
    ne, nx = len(net.entrances), len(net.exits)
    return M.Inputs(d0=3200.0 * lvl * prof, d_o=np.full((D, ne, M.N_BINS), 350.0) * (lvl * prof)[:, None, :],
                    beta=np.full((D, nx, M.N_BINS), 0.08))


def timing_params(P: int) -> dict:
    """A3-feasible synthetic parameter sets (v_c,g well above every threshold)."""
    p = M.midpoint_params()
    p.update({"vf1": 125.0, "vf2": 125.0, "vf3": 120.0, "a1": 2.5, "a2": 2.5, "a3": 2.5, "rc4": 30.0, "a4": 2.5})
    return {k: np.full(P, v) for k, v in p.items()}


V3_TIMING = {"s_per_generation": 6.8, "calibration_wall_h": 53 / 60, "profiles_wall_h": 85 / 60,
             "grid_wall_h": 7 / 60}       # v3 measurements, 2026-10-06 (cma_run.log, postcal_driver.log)


def timing() -> dict:
    """Seconds per CMA-ES generation (12 sets x 22 synthetic days) at T = 0.75 s, single process, after the cached
    von Neumann scan; projections scale v3's measured wall times (which include parallel slow-down) by the ratio."""
    net = M.build_network(VARIANT)
    inp = synthetic_inputs(net)
    M.assert_numerics(net, timing_params(1), T_RUN)               # warm the §A2 (e) cache
    t = time.time()
    M.simulate(net, timing_params(12), inp, n_param_sets=12, record_cells=False, T_s=T_RUN)
    t_gen = time.time() - t
    r = t_gen / V3_TIMING["s_per_generation"]
    cal, prof, grid = (r * V3_TIMING[k] for k in ("calibration_wall_h", "profiles_wall_h", "grid_wall_h"))
    proj = {"calibration_h": cal, "profiles_h": prof, "grid_h": grid, "base_h": cal + prof + grid,
            "with_continuation_h": 2 * cal + prof + grid,
            "with_f1_and_continuation_h": 4 * cal + prof + 2 * grid}
    return {"protocol": PROTOCOL, "T_s": T_RUN, "s_per_generation": round(t_gen, 2), "ratio_to_v3": round(r, 2),
            "projection_h": {k: round(v, 1) for k, v in proj.items()},
            "assumptions": "v3 wall times x the single-process per-generation ratio; F1 (19 parameters) assumed to cost "
                           "one base calibration plus its continuation; synthetic inputs only"}


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
    summary = {"protocol": PROTOCOL, "T_s": T_RUN, "variant": VARIANT, "n_params": len(NAMES), "names": NAMES,
               "budget": BUDGET, "continued_to_8000": continued,
               "no_admissible_restart": bool(best["best_J"] >= J_INADMISSIBLE),
               "restarts": [{k: r[k] for k in r if k != "history"} for r in res], "nominal_seed": best["seed"],
               "nominal_J": best["best_J"], "nominal_params": best["best_params"]}
    (RUNS / "cma_summary.json").write_text(json.dumps(summary, indent=1))
    ledger.append("DP", "metanet-v4-calib", "S", "metanet_v4_cmaes_restarts",
                  {"protocol": PROTOCOL, "seeds": SEEDS, "budget": BUDGET, "variant": VARIANT, "T_s": T_RUN},
                  "7191010-7191017 (optimizer); 22 calibration days; T = 0.75 s", len(SEEDS),
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
        print(json.dumps(timing()))
    else:
        s = run(a.gate_ok)
        print(json.dumps({k: s[k] for k in ("nominal_seed", "nominal_J", "continued_to_8000")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
