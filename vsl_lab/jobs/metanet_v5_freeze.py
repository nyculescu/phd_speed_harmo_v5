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


def build_screen_data() -> dict:
    """calib_screen_data.npz (with exit flows, for P9); arrays shared with calib_data.npz must be equal bit for bit."""
    cal = C.load_data()
    out = screen_data_path()
    V5.RUNS5.mkdir(parents=True, exist_ok=True)
    C.build_data([str(d) for d in cal["days"]], out, exit_flows=True)
    z = np.load(out)
    same = {k: bool(np.array_equal(z[k], cal[k])) for k in cal if k in z.files}
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["premise", "stephalving"])
    ap.add_argument("--seed", type=int, default=None)
    a = ap.parse_args(argv)
    if a.what == "premise":
        r = premise()
        (V5.RUNS5 / "premise_check.json").write_text(json.dumps(r, indent=1, default=float))
        print(json.dumps({"anchor": r["anchor"], "d412": r["d412_comparison"]}, default=float))
        return 0 if r["anchor"]["PASS"] else 3
    raise SystemExit("stephalving runs from the freeze job at the committed nominal (slice D, pending)")


if __name__ == "__main__":
    sys.exit(main())
