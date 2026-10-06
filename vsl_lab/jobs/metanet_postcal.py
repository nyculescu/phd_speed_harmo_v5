"""U.S.169 SB METANET post-calibration stage (protocol v3 §2.5 step-halving, §4.5 profiles, §4.7 capacity-factor
grid). Calibration days only; no validation day is touched here. The freeze itself is in metanet_freeze.

python -m vsl_lab.jobs.metanet_postcal stephalving [--plant SEED]
python -m vsl_lab.jobs.metanet_postcal grid --plant SEED --c2-index I   # one c2 value x all 41 c1 values x all days
python -m vsl_lab.jobs.metanet_postcal grid-run --plant SEED --gate-ok  # the 41 grid jobs in parallel
python -m vsl_lab.jobs.metanet_postcal profile --param P --point J
python -m vsl_lab.jobs.metanet_postcal profile-run --gate-ok            # 8 x 9 profile jobs
A plant is identified by its CMA-ES restart seed (the nominal plant = the best restart).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time

import numpy as np

from vsl_lab.data import metanet_events as V
from vsl_lab.data import metanet_inputs as I
from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.plants import metanet as M

RUNS = C.RUNS
GRID = np.round(np.arange(0.80, 1.2001, 0.01), 2)          # G: 41 values
EV0 = M.SCORE_FROM_BIN                                       # event bin 0 (05:00) = model bin 12
NEV = 216                                                    # event bins 05:00-23:00
PROFILE_PARAMS = ["vf3", "rc3", "tau", "nu", "kappa", "delta_m", "phi", "theta1"]
RELOC_PAIR = ("S1141", "S1610")                              # (Old Shakopee Rd, T.H.101), §4.7 (b)
PAIR = {"B1": I.P1, "B2": I.P2}
DOWN = {"B1": "S1140", "B2": "S1141"}
EXIT_IN = {"B1": "X12", "B2": "X13"}
OVERLAP_BINS = 12                                            # +-60 min


# ---------------------------------------------------------------- plants
def summary() -> dict:
    return json.loads((RUNS / "cma_summary.json").read_text())


def plant_params(seed: int | None = None) -> dict:
    """Frozen parameters of a restart (None = the nominal plant)."""
    s = summary()
    seed = s["nominal_seed"] if seed is None else seed
    r = next(r for r in s["restarts"] if r["seed"] == seed)
    return {k: float(v) for k, v in r["best_params"].items()}


def part1() -> dict:
    return json.loads((RUNS / "precal_part1.json").read_text())


def cell_rc(net: M.Net, p: dict, c1: float = 1.0, c2: float = 1.0) -> np.ndarray:
    """Per-cell critical density as simulate() applies it (G-group rc, c1 on B1, theta1 on the head, c2 on B2)."""
    rc = np.array([p.get(f"rc{g + 1}", p["rc3"]) for g in net.group], float)
    rc[net.b1_cells] *= c1
    rc[net.head1] *= p["theta1"]
    rc[net.b2_cells] *= c2
    return rc


# ---------------------------------------------------------------- model-side events (§5.1)
def model_pairs(day: str, v_st: np.ndarray, net: M.Net, cs: dict) -> dict:
    """Corridor rule (EA-2) on the model through the observation operator v / c_s (computed c_s, dropped stations
    included, §3.2.4); masked per bin by the real event-layer series and per station-day by real event validity.
    The boundary station has no c_s (it is not in any §3.2.4 group): c = 1 (disclosed)."""
    sids = [s["id"] for s in net.stations]
    speeds, valid = {}, {}
    for sid in I.EVENT_STATIONS:
        real = I.event_station(day, sid)
        c = cs[sid]["c_s"] if sid in cs else 1.0
        speeds[sid] = V.observe(v_st[sids.index(sid)][EV0:EV0 + NEV], c, real["v"], real["valid"])
        valid[sid] = real["valid"]
    return {k: e for k, e in I.event_pairs(day, speeds=speeds, valid=valid).items() if e}


def longest_run(b: np.ndarray) -> int:
    best = run = 0
    for x in b:
        run = run + 1 if x else 0
        best = max(best, run)
    return best


def relocation(pairs: dict, rho_bins: np.ndarray, rc_cells: np.ndarray, first_cell: int, n_consec: int = 3) -> dict:
    """§4.7: (a) a cell downstream of B2 with 5-min mean density > rho_cr for >= 3 consecutive bins, or (b) a model
    episode at (Old Shakopee Rd, T.H.101). rho_bins (N, bins) over the scored day."""
    cells = [i for i in range(first_cell, rho_bins.shape[0]) if longest_run(rho_bins[i] > rc_cells[i]) >= n_consec]
    pair = bool(pairs.get(RELOC_PAIR))
    return {"flag": bool(cells) or pair, "cells": cells, "pair": pair}


def c2_star(reloc_by_c2: dict, grid=GRID):
    """Largest g in the grid such that no pair with c2 <= g relocates on any day (reloc_by_c2: c2 -> bool, already
    OR-ed over c1 and days). None if the smallest grid value relocates (c2* < grid minimum)."""
    best = None
    for g in grid:
        if reloc_by_c2[float(g)]:
            break
        best = float(g)
    return best


def spurious(model: dict, real: dict) -> list:
    """P8 (i)-(ii): model episodes at pairs outside {P_1, P_2} with no real episode that day at that pair or at any
    pair sharing a station with it. Returns the offending pairs."""
    out = []
    for p, eps in model.items():
        if p in (I.P1, I.P2) or not eps:
            continue
        if not [q for q, e in real.items() if e and (set(q) & set(p))]:
            out.append(p)
    return out


def overlaps(a: list, b: list, tol: int = OVERLAP_BINS) -> bool:
    return any(s <= e2 + tol and s2 <= e + tol for s, e in a for s2, e2 in b)


def model_day(day: str, q_st: np.ndarray, v_st: np.ndarray, x_flow: np.ndarray, net: M.Net, cs: dict,
              real_ev: dict) -> dict:
    """Model side of one day for the §4.8 diagnostics and the gate: episodes, B_k-active agreement (P3 rule),
    C4 block on the model episode matched to the real longest episode (B1 censored at the real t_c), and the
    merge-section discharge. real_ev = metanet_facts.day_events(day)."""
    sids = [s["id"] for s in net.stations]
    xids = [x["id"] for x in net.exits]
    mp = model_pairs(day, v_st, net, cs)
    out = {"pairs": mp}
    for k in ("B1", "B2"):
        me, re = mp.get(PAIR[k], []), [tuple(e) for e in real_ev[k]]
        agree = overlaps(me, re) if re else not me
        r = {"episodes": me, "active": bool(me), "agree": bool(agree), "c4": None, "merge": None}
        lg = real_ev[k + "_long"]
        if lg is not None and me:
            ri = re.index(tuple(lg["ep"]))
            m = V.match_episodes(re, me)
            if ri in m:
                mep = me[m[ri]]
                cap = real_ev["censor"].get(ri) if k == "B1" else None
                real_q = I.event_station(day, DOWN[k])
                qm = np.where(np.isfinite(real_q["q"]), q_st[sids.index(DOWN[k])][EV0:EV0 + NEV], np.nan)
                c = V.c4(qm, tuple(mep), 2, end_cap=cap)
                r.update({"matched": list(mep), "c4": c})
                if c is not None:
                    a, b = c["window"]
                    xm = x_flow[xids.index(EXIT_IN[k])][EV0:EV0 + NEV]
                    r["merge"] = float(np.nanmean((qm[a:b] + xm[a:b]) / 2.0))
        out[k] = r
    return out


# ---------------------------------------------------------------- capacity-factor grid (§4.7)
def grid_job(seed: int, c2_index: int):
    data = C.load_data()
    days = [str(d) for d in data["days"]]
    net = M.build_network(C.VARIANT)
    cs = part1()["c_s"]
    p = plant_params(seed)
    c2 = float(GRID[c2_index])
    P, D = len(GRID), len(days)
    o = M.simulate(net, {k: np.full(P, v) for k, v in p.items()}, M.Inputs(data["d0"], data["d_o"], data["beta"]),
                   n_param_sets=P, c1=GRID.copy(), c2=np.full(P, c2), record_cells=True)
    real = {d: {k: e for k, e in I.event_pairs(d).items() if e} for d in days}
    res = []
    for pi, c1 in enumerate(GRID):
        rc = cell_rc(net, p, float(c1), c2)
        for di, day in enumerate(days):
            b = pi * D + di
            mp = model_pairs(day, o.v_st[b], net, cs)
            rl = relocation(mp, o.rho_cell[b][:, EV0:], rc, net.b2_cells[-1] + 1)
            sp = spurious(mp, real[day])
            row = {"day": day, "c1": float(c1), "c2": c2, "Z": bool(sp) or rl["flag"], "reloc": rl["flag"],
                   "reloc_cells": [int(i) + 1 for i in rl["cells"]], "reloc_pair": rl["pair"],
                   "spurious": [list(x) for x in sp],
                   "L": V.nrmse(o.v_st[b], data["v"][di], data["mc"][di]),
                   "clip": float(o.clipped_share[b])}
            for k in ("B1", "B2"):
                me = mp.get(PAIR[k], [])
                row["E" + k[1]] = bool(me)
                row["O" + k[1]] = overlaps(me, real[day].get(PAIR[k], []))
            res.append(row)
    out = RUNS / f"grid_{seed}_c2_{c2_index:02d}.json"
    out.write_text(json.dumps(res))
    return out


# ---------------------------------------------------------------- step-halving (§2.5, gated as part of N0)
def stephalving(seed: int | None = None) -> dict:
    data = C.load_data()
    days = [str(d) for d in data["days"]]
    net = M.build_network(C.VARIANT)
    cs = part1()["c_s"]
    p = plant_params(seed)
    x = C.to_norm(p)[None, :]
    sids = [s["id"] for s in net.stations]
    out = {}
    for T in (5.0, 2.5):
        J = C.objective(x, data, net, T_s=T)
        o = M.simulate(net, C.to_params(x), M.Inputs(data["d0"], data["d_o"], data["beta"]), record_cells=False, T_s=T)
        mp = [model_pairs(d, o.v_st[i], net, cs) for i, d in enumerate(days)]
        out[T] = {"J": float(J[0]), "v": o.v_st, "clip_max": float(o.clipped_share.max()),
                  "P1": sorted(d for d, m in zip(days, mp) if m.get(I.P1)),
                  "P2": sorted(d for d, m in zip(days, mp) if m.get(I.P2))}
    rel = abs(out[2.5]["J"] - out[5.0]["J"]) / out[5.0]["J"]
    same = out[2.5]["P1"] == out[5.0]["P1"] and out[2.5]["P2"] == out[5.0]["P2"]
    dv = out[2.5]["v"][:, :, EV0:] - out[5.0]["v"][:, :, EV0:]
    rms = {sid: float(np.sqrt(np.nanmean(dv[:, j] ** 2))) for j, sid in enumerate(sids)}
    res = {"plant_seed": seed if seed is not None else summary()["nominal_seed"],
           "J_5s": out[5.0]["J"], "J_2p5s": out[2.5]["J"], "rel_change": rel, "episode_day_sets_unchanged": same,
           "P1_days_5s": out[5.0]["P1"], "P1_days_2p5s": out[2.5]["P1"],
           "P2_days_5s": out[5.0]["P2"], "P2_days_2p5s": out[2.5]["P2"],
           "clip_max_5s": out[5.0]["clip_max"], "clip_max_2p5s": out[2.5]["clip_max"],
           "rms_speed_change_kmh_by_station": rms, "PASS": bool(rel <= 0.05 and same)}
    (RUNS / f"stephalving_{res['plant_seed']}.json").write_text(json.dumps(res, indent=1))
    return res


# ---------------------------------------------------------------- profiles (§4.5)
def profile_job(pi: int, j: int) -> dict:
    import cma
    data = C.load_data()
    net = M.build_network(C.VARIANT)
    name = PROFILE_PARAMS[pi]
    k = C.NAMES.index(name)
    x_nom = C.to_norm(plant_params())
    fixed = j / 8.0                                   # 9 equally spaced points across the bound (normalised)
    free = [i for i in range(len(C.NAMES)) if i != k]
    seed = (7190100 + j) if name == "theta1" else (7190030 + 9 * pi + j)
    es = cma.CMAEvolutionStrategy(x_nom[free], 0.1, C.cma_options(seed, len(free)))   # lambda = 4 + floor(3 ln(n-1))
    best, n_inadm = (np.inf, None), 0
    while es.countevals < 600:
        Xf = np.array(es.ask())
        X = np.repeat(x_nom[None, :], len(Xf), axis=0)
        X[:, free] = Xf
        X[:, k] = fixed
        J = C.objective(X, data, net)
        n_inadm += int((J >= C.J_INADMISSIBLE).sum())
        es.tell(list(Xf), list(J))
        i = int(np.argmin(J))
        if J[i] < best[0]:
            best = (float(J[i]), np.clip(X[i], 0, 1).tolist())
    res = {"param": name, "point": j, "fixed_norm": fixed, "seed": seed, "popsize": es.popsize,
           "evals": int(es.countevals), "best_J": best[0], "best_x": best[1], "inadmissible_evals": n_inadm}
    (RUNS / f"profile_{name}_{j}.json").write_text(json.dumps(res))
    return res


def _batch(jobs, tag, gate_ok):
    from vsl_lab.ops.scheduler import run_batch
    return run_batch(jobs, RUNS / f"batch_{tag}_{int(time.time())}", max_workers=32, gate_ok=gate_ok)


def main(argv=None) -> int:
    from vsl_lab.ops import ledger
    from vsl_lab.ops.scheduler import Job
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["stephalving", "grid", "grid-run", "profile", "profile-run"])
    ap.add_argument("--plant", type=int, default=None)
    ap.add_argument("--c2-index", type=int, default=0)
    ap.add_argument("--param", type=int, default=0)
    ap.add_argument("--point", type=int, default=0)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "stephalving":
        r = stephalving(a.plant)
        print(json.dumps({k: r[k] for k in ("plant_seed", "J_5s", "J_2p5s", "rel_change", "episode_day_sets_unchanged",
                                            "PASS")}))
        ledger.append("DP", "metanet-calib", "S", "metanet_stephalving", {"T_s": [5.0, 2.5], "plant": r["plant_seed"]},
                      "none (deterministic); calibration days", 1, {},
                      {"rel_change": round(r["rel_change"], 4), "same_episode_days": r["episode_day_sets_unchanged"],
                       "PASS": r["PASS"]}, notes=str(RUNS / f"stephalving_{r['plant_seed']}.json"))
    elif a.what == "grid":
        seed = a.plant if a.plant is not None else summary()["nominal_seed"]
        print(grid_job(seed, a.c2_index))
    elif a.what == "grid-run":
        seed = a.plant if a.plant is not None else summary()["nominal_seed"]
        jobs = [Job(jid=f"grid_{seed}_{i:02d}", argv=["vsl_lab.jobs.metanet_postcal", "grid", "--plant", str(seed),
                                                      "--c2-index", str(i)]) for i in range(len(GRID))]
        rep = _batch(jobs, f"grid_{seed}", a.gate_ok)
        print(json.dumps({"jobs": rep.n_jobs, "failed": rep.n_failed_proc, "wall_s": rep.wall_s}))
        ledger.append("DP", "metanet-calib", "S", "metanet_capacity_grid", {"plant": seed, "grid": "0.80:0.01:1.20 x2"},
                      "none (deterministic); calibration days", rep.n_jobs, {"proc_failed": rep.n_failed_proc},
                      {"wall_s": round(rep.wall_s, 1)}, notes=str(RUNS / f"grid_{seed}_c2_*.json"))
    elif a.what == "profile":
        print(json.dumps(profile_job(a.param, a.point)))
    else:
        jobs = [Job(jid=f"prof_{p}_{j}", argv=["vsl_lab.jobs.metanet_postcal", "profile", "--param", str(p),
                                               "--point", str(j)]) for p in range(len(PROFILE_PARAMS)) for j in range(9)]
        rep = _batch(jobs, "profiles", a.gate_ok)
        print(json.dumps({"jobs": rep.n_jobs, "failed": rep.n_failed_proc, "wall_s": rep.wall_s}))
        ledger.append("DP", "metanet-calib", "S", "metanet_profiles", {"params": PROFILE_PARAMS, "points": 9, "evals": 600},
                      "7190030-7190092, 7190100-7190108 (optimizer)", rep.n_jobs, {"proc_failed": rep.n_failed_proc},
                      {"wall_s": round(rep.wall_s, 1)}, notes=str(RUNS / "profile_*.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
