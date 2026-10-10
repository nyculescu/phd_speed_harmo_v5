"""METANET v5 freeze stage (protocol v5 §B4-§B8, §B11): route labels, step-halving on J5 and J_v4, premise check,
in-sample screen, ensemble members. Calibration days only.

python -m vsl_lab.jobs.metanet_v5_freeze premise          # §B7 (after the facts commit, before CMA-ES)
python -m vsl_lab.jobs.metanet_v5_freeze stephalving      # §B4 at the nominal (after CMA-ES)
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np

from vsl_lab.jobs import metanet_calibrate as C
from vsl_lab.jobs import metanet_postcal as Q
from vsl_lab.jobs import metanet_v5_calibrate as V5
from vsl_lab.plants import metanet as M

T, T_HALF = C.T_RUN, C.T_RUN / 2
STOPS = ["no admissible restart", "step-halving", "P11-k", "in-sample screen", "§4.7 (7)(b)"]
J_V4_ANCHOR = 0.17801580823665977          # committed v4 nominal J (metanet_v4_calibration.json)
D412_LEDGER = {"2400": 0.187, "2100": 0.224, "1900": 0.455}


# ---------------------------------------------------------------- pure rules (tests 37, 39)
def stephalving_pass(j5: tuple, jv4: tuple, sets_T: dict, sets_T2: dict, tol: float = 0.05) -> dict:
    """§B4: PASS iff |ΔJ5|/J5 ≤ 0.05, |ΔJ_v4|/J_v4 ≤ 0.05 and identical P_1/P_2 model-episode day sets."""
    r5 = abs(j5[1] - j5[0]) / j5[0]
    r4 = abs(jv4[1] - jv4[0]) / jv4[0]
    same = all(sorted(sets_T[k]) == sorted(sets_T2[k]) for k in ("B1", "B2"))
    return {"rel_dJ5": r5, "rel_dJv4": r4, "day_sets_identical": same,
            "PASS": bool(r5 <= tol and r4 <= tol and same)}


def route(results: dict) -> dict:
    """§B8 step 6: stops in order; the first failure sets 'STOP (<stop>)'; later ones are 'not run'.
    results: stop name -> True (passed) / False (failed); missing = not evaluated."""
    out, label = {}, None
    for s in STOPS:
        if label is not None:
            out[s] = f"not run (route stopped at {label})"
        elif s not in results:
            raise ValueError(f"stop '{s}' not evaluated")
        elif results[s]:
            out[s] = "PASS"
        else:
            label = s
            out[s] = "FAIL"
    return {"route": f"STOP ({label})" if label else "continue to the ensemble step", "stops": out}


# ---------------------------------------------------------------- step-halving (§B4)
def stephalving(x: list, ev=None, data=None, net=None) -> dict:
    data = data if data is not None else C.load_data()
    net = net or M.build_network(C.VARIANT)
    ev = ev or V5.evaluator(data, net)
    X = np.array([x])
    res = {}
    for name, ts in (("T", T), ("T2", T_HALF)):
        j5, parts = ev(X, T_s=ts, return_parts=True)
        jv4 = C.objective(X, data, net, T_s=ts)
        res[name] = {"J5": float(j5[0]), "J_v4": float(jv4[0]),
                     "sets": parts[0]["model_active_days"] if parts[0] else {"B1": [], "B2": []}}
    v = stephalving_pass((res["T"]["J5"], res["T2"]["J5"]), (res["T"]["J_v4"], res["T2"]["J_v4"]),
                         res["T"]["sets"], res["T2"]["sets"])
    return {"T": res["T"], "T2": res["T2"], **v}


# ---------------------------------------------------------------- premise check (§B7)
def premise() -> dict:
    """J5 and J_v4 at the v4 nominal (anchor, blocking) and the three D4.12 plants (report-only)."""
    data = C.load_data()
    net = M.build_network(C.VARIANT)
    ev = V5.evaluator(data, net)
    rec = Q.plant_record(None)
    x_nom = np.array(rec["best_x"])
    facts = json.loads(V5.FACTS5.read_text())
    p0 = Q.plant_params()
    plants = {"v4_nominal": x_nom}
    for t, rc3 in facts["d412_rho_cr_G3"].items():
        if t in D412_LEDGER:
            p = dict(p0, rc3=rc3)
            plants[f"d412_{t}"] = C.to_norm(p)
    X = np.array(list(plants.values()))
    j5, parts = ev(X, return_parts=True)
    jv4 = C.objective(X, data, net)
    out = {}
    for i, k in enumerate(plants):
        out[k] = {"J5": float(j5[i]), "J_v4": float(jv4[i]), "rows": parts[i]["rows"] if parts[i] else None}
    rel = abs(out["v4_nominal"]["J_v4"] - J_V4_ANCHOR) / J_V4_ANCHOR
    out["anchor"] = {"J_v4": out["v4_nominal"]["J_v4"], "committed": J_V4_ANCHOR, "rel_diff": rel,
                     "PASS": bool(rel <= 1e-9)}
    out["d412_comparison"] = {t: {"J_v4": out[f"d412_{t}"]["J_v4"], "ledger": v,
                                  "consistent": abs(out[f"d412_{t}"]["J_v4"] - v) <= 0.0015}
                              for t, v in D412_LEDGER.items()}
    return out


# ---------------------------------------------------------------- in-sample screen (§B5)
SCREEN_BOOT = 7192099
MINIMA = {"n_val": 16, "n_A": 8, "n_H": 6, "n_H_first": 6}          # v3 §5.2, at the calibration n


def screen_data_path():
    return V5.RUNS5 / "calib_screen_data.npz"


def same_array(a, b) -> bool:
    """Bit-identical arrays; NaN equals NaN for float arrays (the calibration q and v contain NaN)."""
    return bool(np.array_equal(a, b, equal_nan=np.asarray(a).dtype.kind == "f"))


def build_screen_data() -> dict:
    """calib_screen_data.npz (with exit flows, for P9); arrays shared with calib_data.npz must be equal bit for bit."""
    cal = C.load_data()
    out = screen_data_path()
    V5.RUNS5.mkdir(parents=True, exist_ok=True)
    C.build_data([str(d) for d in cal["days"]], out, exit_flows=True)
    z = np.load(out)
    same = {k: same_array(z[k], cal[k]) for k in cal if k in z.files}
    if not all(same.values()):
        raise RuntimeError(f"screen data differ from calib_data: {same}")
    return same


def screen(x: list, stephalving_PASS: bool, seed: int | None = None) -> dict:
    """Every deterministic gate row on the 22 calibration days at c = 1, with the gate's code and thresholds;
    calibration-derived substitutes for every F11 field; leave-one-day-out P1c nulls; bootstrap seed 7,192,099."""
    from vsl_lab.jobs import metanet_gate as G
    from vsl_lab.jobs.metanet_v5_facts import loo_nulls
    z = np.load(screen_data_path())
    data = {k: z[k] for k in z.files}
    p = {k: float(v[0]) for k, v in C.to_params(np.array([x])).items()}
    f8 = json.loads(C.FACTS.read_text())["F8"]                         # calibration-day facts (no F11 field read)
    n = len(data["days"])
    f11_sub = {"P8_tolerance": max(2, int(np.ceil(0.10 * n))),
               "floors": {k: {"L_r": f8[k]["ci_r"][0]} for k in ("B1", "B2")},
               "flow_null_N2_q": {"median_nrmse_q": None}}
    ctx = {"seed": seed, "p": p, "data": data, "f11": f11_sub, "stephalving_PASS": stephalving_PASS,
           "nulls_for": lambda i: dict(zip(("N1", "N2"), loo_nulls(data["v"], data["mv"], i))),
           "boot_seed": SCREEN_BOOT, "write": False}
    res = G.deterministic(seed, ctx=ctx)
    facts = json.loads(V5.FACTS5.read_text())
    q = facts["qualifying"]
    ev = {d: facts["per_day"][d] for d in facts["days"]}
    n_a = {k: sum(1 for d in ev if ev[d][k]) for k in ("B1", "B2")}
    n_h = {k: len(q["heavy"][k]) for k in ("B1", "B2")}
    n_hf = sum(1 for d in ev if ev[d]["heavy_first"])
    unmet = set()
    if n < MINIMA["n_val"]:
        unmet |= {"P6-1", "P6-2"}
    for kk, k in ((1, "B1"), (2, "B2")):
        if n_a[k] < MINIMA["n_A"]:
            unmet |= {f"P3-{kk}", f"P4-{kk}"}
        if n_h[k] < MINIMA["n_H"]:
            unmet |= {f"P5a-{kk}", f"P5b-{kk}", f"P7a-{kk}"}
    if n_hf < MINIMA["n_H_first"]:
        unmet.add("P9")
    screened = [r for r in res["rows"] if r not in unmet and (r != "P5c" or res["rows"]["P5c"]["gated"])]
    failed = [r for r in screened if not res["rows"][r]["PASS"]]
    return {"rows": res["rows"], "screened": screened, "reported_not_screened": sorted(unmet), "failed": failed,
            "counts": {"n": n, "n_A": n_a, "n_H": n_h, "n_H_first": n_hf}, "P8_tolerance": f11_sub["P8_tolerance"],
            "Lc_k": {k: v["L_r"] for k, v in f11_sub["floors"].items()}, "PASS": not failed}


# ---------------------------------------------------------------- §4.7 reports (§B3, report-only)
def c1_inert(rows: list, c2_max: float) -> dict:
    """c1-inert days: at every c2 ≤ c2*, E_1 and O_1 equal at every c1, and no cell of 28-31 congested in a P_1
    qualifying bin at any grid point. Upper-half c1-inert: at c2 = 1.00, E_1 and O_1 equal for every c1 in [1, 1.2]."""
    days = sorted({r["day"] for r in rows})
    inert, upper = [], []
    for d in days:
        rd = [r for r in rows if r["day"] == d]
        lines = {}
        for r in rd:
            if r["c2"] <= c2_max + 1e-9:
                lines.setdefault(r["c2"], set()).add((r["E1"], r["O1"]))
        if all(len(v) == 1 for v in lines.values()) and not any(r.get("b1cells_qual") for r in rd):
            inert.append(d)
        up = {(r["E1"], r["O1"]) for r in rd if abs(r["c2"] - 1.0) < 1e-9 and r["c1"] >= 1.0 - 1e-9}
        if len(up) == 1:
            upper.append(d)
    return {"c1_inert_days": inert, "upper_half_c1_inert_days": upper}


# ---------------------------------------------------------------- freeze orchestration (§B8 step 6)
CORR_BOOT = 7192098
RECORD = C.REPO / "docs" / "lab" / "day_pattern" / "metanet_v5_calibration.json"


def restarts() -> list:
    """The restart results named by the batch driver's summary (no mixing of stale and current files)."""
    summ = V5.RUNS5 / "cma_summary.json"
    if not summ.exists():
        raise SystemExit("cma_summary.json missing: run the v5 batch driver first")
    files = json.loads(summ.read_text())["files"]
    out = []
    for s in V5.SEEDS:
        f = V5.RUNS5 / files[str(s)]
        if not f.exists():
            raise SystemExit(f"restart {s}: {f.name} missing")
        out.append(json.loads(f.read_text()))
    return out


def params_of(x: list) -> dict:
    return {k: float(v[0]) for k, v in C.to_params(np.array([x])).items()}


def p11_freeze(x: list, data: dict, net) -> dict:
    cs = Q.part1()["c_s"]
    days = [str(d) for d in data["days"]]
    p = params_of(x)
    o = Q.simf(net, {k: np.array([v]) for k, v in p.items()}, M.Inputs(data["d0"], data["d_o"], data["beta"]),
               record_cells=True)
    per = {d: Q.p11_day(d, o.v_st[i], o.rho_cell[i], o.rc_cell[i], net, cs) for i, d in enumerate(days)}
    v = Q.p11_verdict(per)
    v["head_cells"] = head_report(days, o, net, cs)
    return v


def head_report(days: list, o, net, cs) -> dict:
    """§B5 (report-only): per day, the head cell of each model P_1 and P_2 episode; days whose P_1 head lies
    outside cells 28-31; days flagged 'residual not excluded' (head at B_k's first cell, 28 or 33)."""
    from vsl_lab.jobs import metanet_j5 as Jm
    out, outside, residual = {}, [], []
    for i, d in enumerate(days):
        sp, _ = Q.model_speeds(d, o.v_st[i], net, cs)
        mp = Q.model_pairs(d, o.v_st[i], net, cs)
        cong = o.rho_cell[i][:, Q.EV0:Q.EV0 + Q.NEV] > o.rc_cell[i][:, Q.EV0:Q.EV0 + Q.NEV]
        rec = {}
        for k in ("B1", "B2"):
            u, dn = Q.PAIR[k]
            with np.errstate(invalid="ignore"):
                cond = np.nan_to_num((sp[u] < 40.0) & ((sp[dn] - sp[u]) >= 20.0)).astype(bool)
            rec[k] = [Jm.head_cell(tuple(e), cond, cong, k) for e in mp.get(Q.PAIR[k], [])]
        out[d] = rec
        if any(h is None or not 28 <= h <= 31 for h in rec["B1"]):
            outside.append(d)
        if any(h == Jm.FIRST_CELL[k] for k in ("B1", "B2") for h in rec[k]):
            residual.append(d)
    return {"per_day": out, "days_P1_head_outside_28_31": outside, "days_residual_not_excluded": residual,
            "note": "in METANET's acceleration zone the reported head can lie 1-2 cells downstream of the true head"}


def grid_rows(seed: int) -> list:
    rows = []
    for i in range(len(Q.GRID)):
        f = V5.RUNS5 / f"grid_{seed}_c2_{i:02d}.json"
        if not f.exists():
            raise SystemExit(f"grid file missing: {f.name} (run the grid batch first)")
        rows += json.loads(f.read_text())
    return rows


def spread_v5(seed: int, data: dict) -> dict:
    """v3 §4.7 unchanged on the v5 grid rows, selector J_d, correlation bootstrap seed 7,192,098."""
    from vsl_lab.data import metanet_facts as F
    from vsl_lab.jobs import metanet_freeze as FZ
    days = [str(d) for d in data["days"]]
    real_ev = {d: F.day_events(d) for d in days}
    real_active = {d: {k: bool(real_ev[d][k]) for k in ("B1", "B2")} for d in days}
    demand = {d: float(data["d0"][i, M.SCORE_FROM_BIN:].sum() * 5 / 60) for i, d in enumerate(days)}
    rows = grid_rows(seed)
    saved = FZ.SEED_BOOT
    FZ.SEED_BOOT = CORR_BOOT
    try:
        cap = FZ.capacity_factors(seed, days, real_active, demand, real_ev, rows=rows, selector="J_d")
    finally:
        FZ.SEED_BOOT = saved
    if cap.get("c2_star") is not None:
        cap["reports_c1"] = c1_inert(rows, cap["c2_star"])
    cap["usable_spread"] = cap.get("spread_used") in ("KM", "Tobit")
    return cap


def finalize(partial_reason: str | None = None) -> dict:
    data = C.load_data()
    net = M.build_network(C.VARIANT)
    rs = restarts()
    adm = [r for r in rs if r["admissible"]]
    res = {"protocol": V5.PROTOCOL, "stage": "freeze", "T_s": T, "objective": "J5",
           "facts_sha256": V5.FACTS5_SHA.read_text().split()[0],
           "restarts": [{k: r.get(k) for k in ("seed", "evals", "best_J5", "admissible", "final_sigma", "counts",
                                               "share_evals_with_credit_B1", "bound_active",
                                               "rel_improvement_last20pct", "wall_s")} for r in rs]}
    results, detail = {"no admissible restart": bool(adm)}, {}
    nom = min(adm, key=lambda r: r["best_J5"]) if adm else None
    if nom:
        x = nom["best_x"]
        res.update({"nominal": nom["seed"], "nominal_J5": nom["best_J5"], "nominal_rows": nom["best_rows"],
                    "frozen_params": params_of(x), "nominal_x": x})
        steps = [("step-halving", lambda: stephalving(x, data=data, net=net)),
                 ("P11-k", lambda: p11_freeze(x, data, net)),
                 ("in-sample screen", lambda: screen(x, True, nom["seed"])),
                 ("§4.7 (7)(b)", lambda: spread_v5(nom["seed"], data))]
        for name, fn in steps:
            r = fn()
            detail[name] = r
            if name == "§4.7 (7)(b)":
                res["capacity_factors"] = {"nominal": r}
            ok = r["usable_spread"] if name == "§4.7 (7)(b)" else r["PASS"]
            results[name] = bool(ok)
            if not ok:
                break
    rt = route(_complete(results))
    from vsl_lab.data import metanet_facts as Fm
    from vsl_lab.jobs import metanet_freeze as FZ
    if data.get("d0") is not None:
        days = [str(d) for d in data["days"]]
        rev = {d: Fm.day_events(d) for d in days}
        dem = {d: float(data["d0"][i, M.SCORE_FROM_BIN:].sum() * 5 / 60) for i, d in enumerate(days)}
        res["benchmarks"] = FZ.benchmarks(days, rev, dem)
    res.update({"route": rt["route"], "stops": rt["stops"], "stop_detail": _clean(detail)})
    if not rt["route"].startswith("STOP"):
        f = V5.RUNS5 / "ensemble_checks.json"
        if not f.exists():
            raise SystemExit("ensemble_checks.json missing: run the ensemble step (§B6) before finalize")
        ens = json.loads(f.read_text())
        mem, mchk, mpar = [], {}, {}
        for sd in ens["gridded"]:
            cap_m = spread_v5(sd, data)
            ok = cap_m["usable_spread"]
            mchk[str(sd)] = dict(ens["checks"][str(sd)], F_hat=ok)
            res["capacity_factors"][str(sd)] = cap_m
            if ok:
                mem.append(sd)
                mpar[str(sd)] = params_of(next(r for r in rs if r["seed"] == sd)["best_x"])
        res.update({"candidates": ens["candidates"], "members": mem, "member_checks": mchk, "member_params": mpar})
    else:
        res.update({"members": [], "candidates": "not run (route stopped)"})
    if partial_reason:
        res["not_run"] = {"reason": partial_reason}
    return res


def ensemble_checks() -> dict:
    """§B6 checks 1-3 per candidate (calibration days only), in candidate order; the first 2 passing get a grid
    (run by the grid batch), check 4 (usable spread) is read at finalize. Written to the v5 raw directory."""
    from vsl_lab.jobs import metanet_freeze as FZ
    from vsl_lab.jobs.metanet_v5_gate import candidates
    data = C.load_data()
    net = M.build_network(C.VARIANT)
    rs = restarts()
    nom = min((r for r in rs if r["admissible"]), key=lambda r: r["best_J5"])
    ki = [C.NAMES.index(k) for k in FZ.ENS_KEYS]
    cands = candidates(rs, nom["seed"], ki)
    checks, gridded = {}, []
    for c in cands:
        if len(gridded) >= 2:
            break
        x = next(r for r in rs if r["seed"] == c["seed"])["best_x"]
        ch = {"stephalving": stephalving(x, data=data, net=net)["PASS"]}
        ch["P11"] = ch["stephalving"] and p11_freeze(x, data, net)["PASS"]
        ch["screen"] = ch["P11"] and screen(x, True, c["seed"])["PASS"]
        checks[str(c["seed"])] = ch
        if ch["screen"]:
            gridded.append(c["seed"])
    out = {"nominal": nom["seed"], "candidates": cands, "checks": checks, "gridded": gridded}
    (V5.RUNS5 / "ensemble_checks.json").write_text(json.dumps(_clean(out), indent=1))
    return out


def _complete(results: dict) -> dict:
    """Stops after the first failure are not evaluated; route() labels them 'not run'."""
    out, failed = {}, False
    for s_ in STOPS:
        if failed:
            out[s_] = True                     # placeholder; route() reports it as 'not run' after the failure
            continue
        out[s_] = results.get(s_, True)
        failed = s_ in results and not results[s_]
    return out


def _clean(x):
    if isinstance(x, dict):
        return {str(k): _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if isinstance(x, (np.floating, np.integer)):
        return x.item()
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, float) and not np.isfinite(x):
        return None
    return x


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["premise", "stephalving", "grid", "ensemble", "finalize"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--c2-index", type=int, default=None)
    ap.add_argument("--partial", default=None)
    a = ap.parse_args(argv)
    if a.what == "grid":
        rs = {r["seed"]: r for r in restarts()}
        Q.grid_job(a.seed, a.c2_index, p=params_of(rs[a.seed]["best_x"]), runs=V5.RUNS5, jd=V5.evaluator())
        return 0
    if a.what == "ensemble":
        print(json.dumps({k: v for k, v in ensemble_checks().items() if k != "candidates"}))
        return 0
    if a.what == "finalize":
        r = finalize(a.partial)
        RECORD.write_text(json.dumps(_clean(r), indent=1, allow_nan=False))
        print(json.dumps({"route": r["route"]}))
        return 0
    if a.what == "premise":
        r = premise()
        (V5.RUNS5 / "premise_check.json").write_text(json.dumps(r, indent=1, default=float))
        print(json.dumps({"anchor": r["anchor"], "d412": r["d412_comparison"]}, default=float))
        return 0 if r["anchor"]["PASS"] else 3
    raise SystemExit("stephalving runs from the freeze job at the committed nominal (slice D, pending)")


if __name__ == "__main__":
    sys.exit(main())
