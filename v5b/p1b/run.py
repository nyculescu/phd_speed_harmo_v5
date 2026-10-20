"""P1b runner (docs/research/protocols/p1b_addendum.md, approved V108, on top of p1_incident_information.md V99 + the
V100 addenda). Everything is P1's runner (v5b/p1/run.py) except:
- episode v5b/p1b/episode.py: amber 3 s, red >= 2 s, q clipped to [200, 2618] in every law (B1, R2);
- seeds (B5, decision 5): tool checks 7,400,260-279, tuning 7,400,300-339, evaluation 7,400,600-699, replicates
  seed + k x 10,000,000; smoke only on 7,400,000-009 (tool checks 000-002, tuning 003-005, evaluation 006-009);
- the V100 author decisions are fixed (no flags): continuous clock (with amber), the T3 replicate pair runs
  (17,400,260), TV-T0 on the page window, gates in both views;
- tool checks as P1 with A = G x {stay, back} (G_PI is tuned later; PI is not run on the tool-check seeds, P1 I1);
  T3 adds a PI-plan switch pair and a runner pair;
- tuning: G and the PI grid fixed (as P1), then G_PI(q) = the 10 PI controllers with the lowest pooled median per q
  (R1), then the switch runs over A(q) = (G u G_PI(q)) x {stay, back} (120 actions) and AD (as P1);
- evaluation: as P1 over A(q), plus the runner rows (R5: s in {10 %, 30 %}, every L0 arm, ID and IP, main runs);
- run-once sentinel <runs root>/P1B_EVAL_STARTED.json and record <runs root>/P1B_TCHECK_RECORD.json; the runs root is
  /home/catalin/work/phd/v5b1_runs or $V5B1_RUNS; --out defaults to <runs root>/p1b/v108.

  run:   (from a detached worktree at the run commit) systemd-run --user --unit p1b-run --working-directory=<worktree> \
           env -u SUMO_HOME OMP_NUM_THREADS=1 nice -n 19 <venv>/bin/python -m v5b.p1b.run --confirm-run-once \
           --workers 32 --cpu-limit 0.90
  smoke: python -m v5b.p1b.run --smoke --out <runs root>/p1b_smoke_<tag> --workers 8 --cpu-limit 0.70
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from collections import Counter
from pathlib import Path

import numpy as np

from v5b.d1 import netgen_bn4 as net
from v5b.d1.config import REPO_ROOT, RUNS_ROOT
from v5b.d2.incidents import INCIDENTS, NONE
from v5b.d2.run_screen import make_verify, tree_state
from v5b.p1 import family as fam
from v5b.p1 import run as p1run
from v5b.p1 import stats as st
from v5b.p1.run import (_first, _git, _keep, _pct, _sub, append_tcheck_record, check_sentinel, check_tcheck_record,
                        same_run, tcheck_decision, write_sentinel)
from v5b.p1b import analysis as an
from v5b.p1b import family as fb
from v5b.p1b.analysis import CONDITIONS, QS, RMAX, TV_B0, VSL_B, cell_name, fixed, qk, sw
from v5b.p1b.episode import SPEC_FIELDS, make_spec
from v5b.p1b.meters import SIGNAL
from v5b.p1b.runners import SHARES

PAGE = "docs/research/protocols/p1b_addendum.md"
BASE_PAGE = "docs/research/protocols/p1_incident_information.md"
SEEDS = {"tcheck": tuple(range(7_400_260, 7_400_280)), "tune": tuple(range(7_400_300, 7_400_340)),
         "eval": tuple(range(7_400_600, 7_400_700))}
SMOKE_SEEDS = {"tcheck": tuple(range(7_400_000, 7_400_003)), "tune": tuple(range(7_400_003, 7_400_006)),
               "eval": tuple(range(7_400_006, 7_400_010))}
CALIB_ONLY = range(7_400_000, 7_400_010)
DECISIONS = {"meter_signal": SIGNAL, "t3_replicate": "run", "tv_t0_window": "page", "gate_views": "both"}  # V100
SENTINEL = RUNS_ROOT / "P1B_EVAL_STARTED.json"
TCHECK_RECORD = RUNS_ROOT / "P1B_TCHECK_RECORD.json"
DEFAULT_OUT = RUNS_ROOT / "p1b" / "v108"
ALLOWED_ROOTS = (Path("/home/catalin/work/phd"), RUNS_ROOT)
CPU_LIMIT_DEFAULT = 0.90
G_SMOKE, PI_SMOKE = p1run.G_SMOKE, p1run.PI_SMOKE
N_GPI_SMOKE = 2
T3_Q = 2000.0
KEEP = p1run.KEEP + ("rs", "max_queue_m", "max_queue_halted_veh", "avail_m", "crossings", "runner_crossings",
                     "red_cross_share", "runner_red_cross_share", "discharge_vph", "commanded_mean_vph",
                     "approach_red_mps", "emergency_meter", "emergency_stops", "collisions", "n_runners")


class Pool(p1run.Pool):
    MODULE, FIELDS, KEEP_FIELDS, SIGNAL_SET = "v5b.p1b.episode", SPEC_FIELDS, KEEP, (SIGNAL,)


def t3_specs(seed, *, replicate: bool = True) -> list:
    """P1's 13 pairs (P1b episode), plus a switch into a PI plan with switch-back and a runner run (s = 30 %)."""
    q, base = T3_Q, []
    for pre, post, inc, back in (("c1200", None, "block", False), ("f20_8", None, "slow", False),
                                 ("NC", None, "block", False), ("c1600", "f40_10", "block", False),
                                 ("f20_8", "c800", "slow", False), ("c1600", "c800", "block", True)):
        base.append(dict(pre=pre, post=post, back=back, incident=inc))
    base += [dict(pre="p40_20_8_e4", incident="block"), dict(pre="p40_20_6_e5", incident="slow"),
             dict(pre="ad1_f20_8", incident="block"),
             dict(pre="c1600", post="c800", back=True, incident="block", d=60.0, c=60.0),
             dict(pre="c1600", post="c800", back=True, incident="slow", vsl_b=0.4),
             dict(pre="c1600", post="c800", back=True, incident="block", k=1),
             dict(pre="c1600", post="c800", incident=NONE, fa=True),
             dict(pre="c1600", post="p40_20_8_e4", back=True, incident="block"),
             dict(pre="c1600", post="p40_20_6_e5", back=False, incident="slow", rs=0.3)]
    if not replicate:
        base = [b for b in base if not b.get("k")]
    return [[make_spec(q=q, seed=seed, rep=r, **b) for r in (0, 1)] for b in base]


# ---------------------------------------------------------------- stage 1: tool checks (P1's, see the docstring)
def stage_tcheck(pool, seeds, G_, *, gate_views: str, tv_window: str, t3_replicate: bool, force_tv: bool = False) -> dict:
    """Decision D4 (gate_views): T0, T4, TV-T0 and TV entry are computed in both views of page §5; the hindsight arm
    (T0's best, T4's g*) is the one chosen on all seeds. 'all_seeds' gates on all seeds (the valid-only view is
    reported); 'both' needs every cell in both views (T0, T4) or one cell / (b, cell) passing in both (TV-T0, entry)."""
    if gate_views not in DECISIONS["gate_views"] or tv_window not in DECISIONS["tv_t0_window"]:
        raise ValueError((gate_views, tv_window))
    both = gate_views == "both"
    A_ = fb.actions(G_)   # G x {stay, back}: G_PI is tuned later (docstring)
    t3 = t3_specs(seeds[0], replicate=t3_replicate)
    resA, failA = pool.run(an.fixed_specs(tuple(G_) + (fam.NC,), CONDITIONS, seeds) + [x for p in t3 for x in p],
                           "tcheck-A")
    fx = {qk(q): an.fit_fixed(resA, seeds, G_, (), q) for q in QS}
    N_t = {k: v["N"] for k, v in fx.items()}
    spB = an.switch_specs(N_t, {qk(q): A_ for q in QS}, seeds)
    for q in QS:
        ad = fam.ad_id(1.0, fx[qk(q)]["FB"])
        spB += [fixed(ad, inc, q, s) for s in seeds for inc in INCIDENTS]
        spB += [fixed(fam.NC, inc, q, s, vsl=TV_B0) for s in seeds for inc in INCIDENTS]
    resB, failB = pool.run(spB, "tcheck-B")
    res = {**resA, **resB}
    arms = {}
    for q in QS:
        f = fx[qk(q)]
        s_ = an.fit_switch(res, seeds, A_, q, f["N"])
        arms[qk(q)] = {"N": f["N"], "FX": f["FX"], "FB": f["FB"], "AD": fam.ad_id(1.0, f["FB"]), "IP": s_["IP"],
                       "ID": s_["ID"]}
    order = ("ID", "IP", "N", "FX", "FB", "AD")
    fld = TV_FIELD[tv_window]
    fld_o = TV_FIELD["ext120" if tv_window == "page" else "page"]
    best, ncs, best_name, t4, tad, tv_nc, tv_v, tv_alone = {}, {}, {}, {}, {}, {}, {}, {}
    best_v, ncs_v, t4_v, tvv_nc, tvv_v, tvo_nc, tvo_v = {}, {}, {}, {}, {}, {}, {}
    for inc in INCIDENTS:
        for q in QS:
            name, a = cell_name(inc, q), arms[qk(q)]
            kk = {x: (lambda s, x=x: sw(a["N"], a[x] if x == "ID" else a["IP"][inc], inc, q, s)["key"]) if x in ("ID", "IP")
                  else (lambda s, x=x: fixed(a[x], inc, q, s)["key"]) for x in order}
            kk["NC"] = lambda s: fixed(fam.NC, inc, q, s)["key"]
            ok = [s for s in seeds if all(f(s) in res for f in kk.values())]
            if not ok:
                raise SystemExit(f"tool checks: no seed with all runs in cell {name} (failed runs: {failA + failB})")
            D = {x: np.array([res[f(s)]["delay_s"] for s in ok], float) for x, f in kk.items()}
            V = {x: [res[f(s)]["valid"] for s in ok] for x, f in kk.items()}
            b = _first(order, D)
            best[name], ncs[name], best_name[name] = D[b], D["NC"], b
            kv = _keep([V[b], V["NC"]])
            best_v[name], ncs_v[name] = _sub(D[b], kv), _sub(D["NC"], kv)
            okf = [s for s in seeds if all(fixed(g, inc, q, s)["key"] in res for g in G_)]
            per = {g: [res[fixed(g, inc, q, s)["key"]]["delay_s"] for s in okf] for g in G_}
            gstar = fam.best_by_median(per, G_)
            t4[name] = st.t4_cell(per[a["N"]], per[gstar], a["N"], gstar)
            kf = _keep([[res[fixed(g, inc, q, s)["key"]]["valid"] for s in okf] for g in (a["N"], gstar)])
            t4_v[name] = st.t4_cell(_sub(per[a["N"]], kf), _sub(per[gstar], kf), a["N"], gstar)
            tad[name] = [res[k]["ad_max_dev"] for s in seeds if (k := fixed(a["AD"], inc, q, s)["key"]) in res]
            okv = [s for s in seeds if fixed(fam.NC, inc, q, s)["key"] in res and
                   fixed(fam.NC, inc, q, s, vsl=TV_B0)["key"] in res]
            rn = [res[fixed(fam.NC, inc, q, s)["key"]] for s in okv]
            rv = [res[fixed(fam.NC, inc, q, s, vsl=TV_B0)["key"]] for s in okv]
            tv_nc[name], tv_v[name] = [r[fld] for r in rn], [r[fld] for r in rv]
            tvo_nc[name], tvo_v[name] = [r[fld_o] for r in rn], [r[fld_o] for r in rv]
            kt = _keep([[r["valid"] for r in rn], [r["valid"] for r in rv]])
            tvv_nc[name], tvv_v[name] = _sub(tv_nc[name], kt), _sub(tv_v[name], kt)
            tv_alone[name] = st.paired([r["delay_s"] for r in rn], [r["delay_s"] for r in rv])
    tele = {}
    for k, r in res.items():
        if r.get("rep") is None:
            tele.setdefault(f"{r['incident']}_q{qk(r['q'])}", []).append(r["teleports"])
    t3r = {p[0]["key"]: (p[0]["key"] in res and p[1]["key"] in res and same_run(pool.out, p[0]["key"], p[1]["key"]))
           for p in t3}
    t0a, t0v = st.t0_cells(best, ncs, best_name), st.t0_cells(best_v, ncs_v, best_name)
    t4a, t4v = st.t4_overall(t4), st.t4_overall(t4_v)
    tba, tbv = st.tv_binding(tv_nc, tv_v), st.tv_binding(tvv_nc, tvv_v)
    bind_cells = [c for c, r in tba["cells"].items() if r["binds"] and (not both or tbv["cells"][c]["binds"])]
    tv_pass = bool(bind_cells)
    T0 = {**t0a, "pass_all_seeds": t0a["pass"], "valid_only": t0v, "gate_views": gate_views,
          "pass": bool(t0a["pass"] and (t0v["pass"] or not both))}
    T4 = {**t4a, "pass_all_seeds": t4a["pass"], "valid_only": t4v, "gate_views": gate_views,
          "pass": bool(t4a["pass"] and (t4v["pass"] or not both))}
    TVT0 = {**tba, "pass_all_seeds": tba["pass"], "valid_only": tbv, "gate_views": gate_views, "window": tv_window,
            "count_field": fld, "binding_cells": bind_cells, "pass": tv_pass,
            "text": "" if tv_pass else st.TV_NO_BIND_TEXT,
            f"other_window_{fld_o}_report_only": st.tv_binding(tvo_nc, tvo_v)}
    if tv_window == "page" and tv_pass and not TVT0[f"other_window_{fld_o}_report_only"]["pass"]:
        TVT0["caveat"] = ("binds in the onset-clearance window but not over [onset, clearance + 120 s): the change may "
                          "be a travel-time shift of arrivals (VSL slows edges 2-3), not a flow restriction")
    out = {"seeds": [seeds[0], seeds[-1]], "arms": arms, "T0": T0,
           "T1": st.t1_cells(tele), "T3": t3r, "T3_pass": all(t3r.values()), "T4": T4,
           "T_AD": st.tad_cells(tad), "TV_T0": TVT0, "TV_alone_vs_NC_delay_b0.4_report_only": tv_alone,
           "failed_runs": failA + failB,
           "PI_note": "PI and G_PI are not run on the tool-check seeds (P1 I1); T0's best-of excludes them"}
    if tv_pass or force_tv:
        spC = [sw(arms[qk(q)]["N"], arms[qk(q)]["IP"][inc], inc, q, s, vsl=b) for b in VSL_B for q in QS
               for inc in INCIDENTS for s in seeds]
        resC, failC = pool.run(spC, "tcheck-C")
        res.update(resC)
        out["failed_runs"] += failC
        ip, ipv, ip_v, ipv_v = {}, {}, {}, {}
        for b in VSL_B:
            for inc in INCIDENTS:
                for q in QS:
                    a = arms[qk(q)]
                    ok = [s for s in seeds if sw(a["N"], a["IP"][inc], inc, q, s)["key"] in res and
                          sw(a["N"], a["IP"][inc], inc, q, s, vsl=b)["key"] in res]
                    key = f"b{b:g}_{cell_name(inc, q)}"
                    r0 = [res[sw(a["N"], a["IP"][inc], inc, q, s)["key"]] for s in ok]
                    r1 = [res[sw(a["N"], a["IP"][inc], inc, q, s, vsl=b)["key"]] for s in ok]
                    ip[key], ipv[key] = [r["delay_s"] for r in r0], [r["delay_s"] for r in r1]
                    ke = _keep([[r["valid"] for r in r0], [r["valid"] for r in r1]])
                    ip_v[key], ipv_v[key] = _sub(ip[key], ke), _sub(ipv[key], ke)
        ea, ev_ = st.tv_entry(ip, ipv), st.tv_entry(ip_v, ipv_v)
        entering = [k for k, r in ea["cells"].items() if r["pass"] and (not both or ev_["cells"][k]["pass"])]
        out["TV_entry"] = {**ea, "enters_all_seeds": ea["enters"], "valid_only": ev_, "gate_views": gate_views,
                           "entering": entering, "enters": bool(entering),
                           "text": "" if entering else st.TV_NO_ENTRY_TEXT}
        out["TV_entry"]["forced_in_smoke"] = bool(force_tv and not tv_pass)
    else:
        out["TV_entry"] = {"enters": False, "text": "TV ended at TV-T0 (not binding)"}
    out["vsl_enters"] = bool(tv_pass and out["TV_entry"]["enters"])
    out["n_runs"] = len(res)
    out["pass"] = bool(out["T0"]["pass"] and out["T1"]["pass"] and out["T3_pass"] and out["T4"]["pass"])
    return out



# ---------------------------------------------------------------- stage 2: tuning
def gpi_select(res, seeds, PI_, q, n: int) -> tuple:
    """R1: G_PI(q) = the n PI controllers with the lowest pooled (slow + block) median delay on the tuning seeds."""
    pooled = {g: [res[k]["delay_s"] for inc in INCIDENTS for s in seeds if (k := fixed(g, inc, q, s)["key"]) in res]
              for g in PI_}
    return fb.top_pi(pooled, PI_, n), {g: float(np.median(v)) for g, v in pooled.items() if v}


def grid_edges(cid: str) -> list:
    return fam.grid_edges(cid[: -len(fb.BACK)] if cid.endswith(fb.BACK) else cid)


def stage_tune(pool, seeds, G_, PI_, vsl: bool, n_gpi: int = fb.N_GPI) -> dict:
    resA, failA = pool.run(an.fixed_specs(G_, CONDITIONS, seeds) + an.fixed_specs(PI_, CONDITIONS, seeds), "tune-A")
    fx = {qk(q): an.fit_fixed(resA, seeds, G_, PI_, q) for q in QS}
    gpi = {qk(q): gpi_select(resA, seeds, PI_, q, n_gpi)[0] for q in QS}
    A_q = {k: fb.actions(G_, v) for k, v in gpi.items()}
    spB = an.switch_specs({k: v["N"] for k, v in fx.items()}, A_q, seeds)
    for q in QS:
        spB += an.fixed_specs(an.ad_candidates(fx[qk(q)]["FB"]), CONDITIONS, seeds, (q,))
    resB, failB = pool.run(spB, "tune-B")
    res = {**resA, **resB}
    arms, tables = {}, {}
    for q in QS:
        f = fx[qk(q)]
        s_ = an.fit_switch(res, seeds, A_q[qk(q)], q, f["N"])
        ad = an.fit_ad(res, seeds, q, f["FB"])
        arms[qk(q)] = {"N": f["N"], "FX": f["FX"], "FB": f["FB"], "PI": f["PI"], "AD": ad["AD"], "IP": s_["IP"],
                       "ID": s_["ID"], "G_PI": list(gpi[qk(q)])}
        tables[qk(q)] = {"median_none": f["median_none"], "median_incident_pooled": f["median_incident_pooled"],
                         "median_switch": s_["median_switch"], "AD": ad["median_incident_pooled"]}
    failC = []
    if vsl:
        spC = [sw(arms[qk(q)]["N"], arms[qk(q)]["IP"][inc], inc, q, s, vsl=b) for b in VSL_B for q in QS
               for inc in INCIDENTS for s in seeds]
        resC, failC = pool.run(spC, "tune-C")
        res.update(resC)
        for q in QS:
            arms[qk(q)]["VSL_b"] = an.fit_vsl_b(res, seeds, q, arms[qk(q)]["N"], arms[qk(q)]["IP"])
    for q in QS:
        arms[qk(q)]["prev"] = an.fit_prevalence(res, seeds, q, an.prevalence_families(arms[qk(q)], G_, PI_))
    edges = {}
    for k, a in arms.items():
        chosen = {x: a[x] for x in ("N", "FX", "FB", "PI", "AD", "ID")}
        chosen.update({f"IP_{i}": c for i, c in a["IP"].items()})
        chosen.update({f"{x}_pi{p}": g for p, v in a["prev"].items() for x, g in v.items()})
        edges[k] = {x: grid_edges(c) for x, c in chosen.items() if grid_edges(c)}
    return {"seeds": [seeds[0], seeds[-1]], "arms": arms, "tables": tables, "grid_edges_report_only": edges,
            "G_PI": {k: list(v) for k, v in gpi.items()}, "A_size": {k: len(v) for k, v in A_q.items()},
            "failed_runs": failA + failB + failC, "n_runs": len(res)}


def a_by_q(G_, arms: dict) -> dict:
    return {k: fb.actions(G_, tuple(a["G_PI"])) for k, a in arms.items()}


# ---------------------------------------------------------------- stage 3: evaluation
def stage_eval(pool, seeds, G_, arms, vsl: bool, shares=SHARES) -> dict:
    A_q = a_by_q(G_, arms)
    sp = an.eval_specs(arms, A_q, seeds, RMAX, vsl, shares)
    res, failed = pool.run(sp, "eval")
    ev = an.evaluate(res, seeds, A_q, arms, RMAX, vsl, log=pool.log, shares=shares)
    mism = 0
    for q in QS:
        N = arms[qk(q)]["N"]
        for inc in INCIDENTS:
            for s in seeds:
                k1, k2 = fixed(N, inc, q, s)["key"], sw(N, N, inc, q, s)["key"]
                if k1 in res and k2 in res and res[k1]["hash"] != res[k2]["hash"]:
                    mism += 1
    ev.update({"seeds": [seeds[0], seeds[-1]], "failed_runs": failed, "n_runs": len(sp),
               "teleport_runs": int(sum(r["teleports"] > 0 for r in res.values())),
               "invalid_runs": int(sum(not r["valid"] for r in res.values())),
               "collision_runs": int(sum(r["collisions"] > 0 for r in res.values())),
               "N_fixed_vs_switch_hash_mismatches": mism})
    return ev


# ---------------------------------------------------------------- run counts and report
def run_counts(n_g: int = len(fam.G), n_pi: int = len(fam.PI), n_gpi: int = fb.N_GPI, seeds: dict = None,
               vsl: bool = True, tv_binds: bool = True, shares=SHARES) -> dict:
    """Runs per stage (upper bounds as P1's run_counts: every d / c / combined run distinct, every prevalence arm new,
    VSL entering; runner rows with ID != IP)."""
    S = {k: len(v) for k, v in (seeds or SEEDS).items()}
    nq, ni, nc = len(QS), len(INCIDENTS), len(CONDITIONS)
    na_t, na = 2 * n_g, 2 * (n_g + n_gpi)
    tc = (n_g + 1) * nc * nq * S["tcheck"] + 2 * len(t3_specs(0)) + na_t * ni * nq * S["tcheck"] + \
        2 * ni * nq * S["tcheck"] + (len(VSL_B) * ni * nq * S["tcheck"] if tv_binds else 0)
    tu = (n_g + n_pi) * nc * nq * S["tune"] + na * ni * nq * S["tune"] + len(fam.ETA_GRID) * nc * nq * S["tune"] + \
        (len(VSL_B) * ni * nq * S["tune"] if vsl else 0)
    ev_main = na * ni * nq * S["eval"]
    ev_reps = RMAX * ev_main
    ev_l0 = 6 * nc * nq * S["eval"]
    ev_imp = ni * nq * S["eval"] * (len(an.D_GRID) - 1 + len(an.C_GRID) - 1 + 2 + 1)
    ev_run = len(shares) * len(an.RUNNER_ARMS) * ni * nq * S["eval"]
    ev_prev = 5 * len(an.PIS) * nc * nq * S["eval"]
    ev_vsl = ni * nq * S["eval"] if vsl else 0
    ev = ev_main + ev_reps + ev_l0 + ev_imp + ev_vsl + ev_run
    return {"tcheck": tc, "tune": tu, "eval": ev, "eval_replicates": ev_reps, "eval_runner_rows": ev_run,
            "total": tc + tu + ev, "eval_prevalence_upper_extra": ev_prev, "total_upper": tc + tu + ev + ev_prev}


def _f(x, fmt="{:.1f}"):
    return "-" if x is None else fmt.format(x)


def summary_md(result: dict) -> str:
    txt = p1run.summary_md(result)
    txt = txt.replace("# P1 ", "# P1b ", 1).replace(f"|A| = {2 * len(result['G'])}", "|A(q)| = 2 (|G| + |G_PI(q)|)")
    L = ["", "## P1b additions", "", f"Decisions fixed (V100): {DECISIONS}. Meter: amber 3 s, red >= 2 s, "
         "q in [200, 2618] veh/h.", ""]
    if "tune" in result:
        L += [f"- G_PI(q): {result['tune']['G_PI']}; |A(q)| = {result['tune']['A_size']}", ""]
    if "eval" in result:
        ev = result["eval"]
        L += ["### Meter safety, discharge and queue (Table 1 arms; medians over seeds)", "",
              "| cell | arm | EB meter (sum) | approach at red med / max m/s | red-cross share | commanded | G / y / r veh/h"
              " | max queue m med / max (avail) | spill share | collisions |", "|---|---|---|---|---|---|---|---|---|---|"]
        for c, m in ev["table1_operating_map"].items():
            for x, r in m["arms"].items():
                dv = r["median_discharge_vph"]
                L.append(f"| {c} | {x} | {r['emergency_meter_total']} | {_f(r['approach_red_mps_median'])} / "
                         f"{_f(r['approach_red_mps_max'])} | {_f(r['median_red_cross_share'], '{:.3f}')} | "
                         f"{_f(r['median_commanded_vph'], '{:.0f}')} | {_f(dv['G'], '{:.0f}')} / {_f(dv['y'], '{:.0f}')}"
                         f" / {_f(dv['r'], '{:.0f}')} | {r['median_max_queue_m']:.0f} / {r['max_max_queue_m']:.0f} "
                         f"({r['avail_m']:.0f}) | {_f(r['spill_share'], '{:.2f}')} | {r['collisions_total']} |")
        L += ["", f"Queue limit flags (B4, > 5 % of runs reach the entry): {ev['queue_limit_flags'] or 'none'}", "",
              "### Runner rows (R5; descriptive, 95 % CI, all seeds; rel % = median(r - t) / median(r))", "",
              "| s, cell | ID vs N / FX / FB / PI / AD | IP vs ID | arm vs itself at s = 0 (N FX FB PI AD ID IP) |"
              " red-cross share (all / runners) |", "|---|---|---|---|---|"]
        for c, v in ev["runner_rows"].items():
            if not v.get("n_seeds"):
                L.append(f"| {c} | no seeds | | | |")
                continue
            idv = " / ".join(_pct(v["ID_vs"][r]["all_seeds"]["rel"]) for r in an.L0)
            slf = " ".join(_pct(v["vs_self_s0"][x]["all_seeds"]["rel"]) for x in an.RUNNER_ARMS)
            rcs = v["arms"]["N"]
            L.append(f"| {c} | {idv} | {_pct(v['IP_vs_ID']['all_seeds']['rel'])} | {slf} | "
                     f"{_f(rcs['median_red_cross_share'], '{:.3f}')} / "
                     f"{_f(rcs['median_runner_red_cross_share'], '{:.3f}')} (N) |")
        L += ["", f"Collision runs {ev['collision_runs']}."]
    return txt + "\n".join(L) + "\n"


def smoke_p1_compare(out: Path, workers: int, cpu_limit: float, log, commit: str, seeds, G_) -> dict:
    """Smoke only: the tool-check A fixed runs again with P1's episode (continuous signal, no amber), paired by key
    with the P1b runs: emergency stops / braking at the meter and network-wide, with and without amber."""
    from v5b.p1 import analysis as p1an
    pool = p1run.Pool(out / "p1_compare", workers, cpu_limit, log, signal="continuous", commit=commit)
    pool.run(p1an.fixed_specs(tuple(G_) + (fam.NC,), CONDITIONS, seeds), "smoke-p1-compare")
    rows = {"p1_no_amber": Counter(), "p1b_amber": Counter()}
    for p in (out / "p1_compare" / "runs").glob("*.json"):
        b = out / "runs" / p.name
        if not b.exists():
            continue
        r1, r2 = json.loads(p.read_text()), json.loads(b.read_text())
        if r1["pre"] == fam.NC:
            continue
        e1 = (r1.get("emergency_by_edge") or {}).get("all", {})
        rows["p1_no_amber"].update({"runs": 1, "eb_meter": sum(v for e, v in e1.items() if e == "2" or e.startswith(":3")),
                                    "emergency_stops": r1["emergency_stops"], "teleports": r1["teleports"],
                                    "collisions": r1["collisions"], "runs_with_eb_meter": int(any(
                                        v for e, v in e1.items() if e == "2" or e.startswith(":3")))})
        rows["p1b_amber"].update({"runs": 1, "eb_meter": r2["emergency_meter"] or 0,
                                  "emergency_stops": r2["emergency_stops"], "teleports": r2["teleports"],
                                  "collisions": r2["collisions"], "runs_with_eb_meter": int(bool(r2["emergency_meter"]))})
    return {k: dict(v) for k, v in rows.items()}


def smoke_report(out: Path, pool, compare: dict) -> dict:
    runs = [json.loads(p.read_text()) for p in (out / "runs").glob("*.json")]
    walls = np.array([r["wall_s"] for r in runs], float)
    n_runs = sum(v["runs"] for v in pool.stage_wall.values())
    wall = sum(v["wall_s"] for v in pool.stage_wall.values())
    thr = n_runs / wall if wall else float("nan")
    rc = run_counts()
    med = float(np.median(walls))
    rr = {}
    for s in SHARES:
        sub = [r for r in runs if r.get("rs") == s and r["pre"] != fam.NC]
        rr[str(s)] = {"runs": len(sub), "median_red_cross_share": an._med([r["red_cross_share"] for r in sub]),
                      "median_runner_red_cross_share": an._med([r["runner_red_cross_share"] for r in sub]),
                      "median_runner_share_realised": an._med([r["n_runners"] / r["generated"] for r in sub]),
                      "collisions": int(sum(r["collisions"] for r in sub)),
                      "eb_meter": int(sum(r["emergency_meter"] or 0 for r in sub))}
    base = [r for r in runs if not r.get("rs") and r["pre"] != fam.NC]
    rr["0"] = {"runs": len(base), "median_red_cross_share": an._med([r["red_cross_share"] for r in base])}
    return {"n_runs": len(runs), "wall_s_per_run": {"median": med, "p90": float(np.percentile(walls, 90)),
                                                    "max": float(walls.max())},
            "wall_s_by_kind": {k: float(np.median([r["wall_s"] for r in runs if p1run._kind(r) == k]))
                               for k in sorted({p1run._kind(r) for r in runs})},
            "teleport_runs": int(sum(r["teleports"] > 0 for r in runs)),
            "teleports_total": int(sum(r["teleports"] for r in runs)),
            "invalid_runs": int(sum(not r["valid"] for r in runs)), "health": dict(Counter(r["health"] for r in runs)),
            "collision_runs": int(sum(r["collisions"] > 0 for r in runs)),
            "emergency_with_without_amber": compare, "red_crossing": rr,
            "throughput_runs_per_s": thr, "workers": pool.workers, "full_run_counts": rc,
            "full_wall_estimate_32w_linear_h": rc["total"] * med / 32 / 3600.0,
            "full_wall_estimate_32w_from_smoke_throughput_h": rc["total"] / (thr * 32 / pool.workers) / 3600.0}


# ---------------------------------------------------------------- run-once and launch rules
def check_out_dir(out: Path, resume: bool) -> None:
    out = out.resolve()
    if not any(out.is_relative_to(r.resolve()) for r in ALLOWED_ROOTS) or out.is_relative_to(REPO_ROOT.resolve()):
        raise SystemExit(f"--out must be under {[str(r) for r in ALLOWED_ROOTS]} and outside the repo")
    if (out / "result.json").exists():
        raise SystemExit(f"{out} already holds a result: P1b runs once")
    if (out / "runs").exists() and any((out / "runs").iterdir()) and not resume:
        raise SystemExit(f"{out}/runs is not empty; pass --resume to reuse finished runs of an interrupted run")


def check_launch(a, dirty: bool) -> None:
    if not 1 <= a.workers <= 100:
        raise SystemExit("--workers must be in 1..100")
    if not 0.0 < a.cpu_limit <= 0.90:
        raise SystemExit("--cpu-limit must be in (0, 0.90] (author rule: CPU <= 90 %)")
    if a.smoke:
        if a.workers > 8:
            raise SystemExit("--smoke uses at most 8 workers")
        if not all(s in CALIB_ONLY for v in SMOKE_SEEDS.values() for s in v):
            raise SystemExit("smoke seeds must be calibration seeds 7,400,000-009")
        return
    if not a.confirm_run_once:
        raise SystemExit("P1b touches the tool-check, tuning and evaluation seeds once: pass --confirm-run-once")
    if dirty:
        raise SystemExit("the work tree is dirty: commit first")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help=f"default {DEFAULT_OUT} (runs root: $V5B1_RUNS)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--cpu-limit", type=float, default=CPU_LIMIT_DEFAULT)
    ap.add_argument("--nice", type=int, default=19)
    ap.add_argument("--smoke", action="store_true", help="smoke seeds 7,400,000-009, G / PI subsets, <= 8 workers")
    ap.add_argument("--confirm-run-once", action="store_true", help="required for the real run")
    ap.add_argument("--resume", action="store_true")
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    if a.out is None:
        if a.smoke:
            raise SystemExit("--smoke needs an explicit --out (the default is the real run's directory)")
        a.out = str(DEFAULT_OUT)
    out = Path(a.out)
    commit, dirty = _git("rev-parse", "HEAD"), bool(_git("status", "--porcelain"))
    state0 = tree_state()
    check_launch(a, dirty)
    check_out_dir(out, a.resume)
    if not a.smoke:
        check_sentinel(out, a.resume, commit, sentinel=SENTINEL, args=vars(a))
        if not SENTINEL.exists():
            check_tcheck_record(commit, record=TCHECK_RECORD)
    os.nice(max(0, a.nice - os.nice(0)))
    out.mkdir(parents=True, exist_ok=True)
    logf = out / "run.log"

    def log(msg):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        with open(logf, "a") as fh:
            fh.write(line + "\n")

    net.build()
    verify = make_verify(state0, log)
    pool = Pool(out, a.workers, a.cpu_limit, log, signal=SIGNAL, commit=commit, verify=verify)
    G_, PI_ = (G_SMOKE, PI_SMOKE) if a.smoke else (fam.G, fam.PI)
    n_gpi = N_GPI_SMOKE if a.smoke else fb.N_GPI
    seeds = SMOKE_SEEDS if a.smoke else SEEDS
    sha = lambda p: hashlib.sha256((REPO_ROOT / p).read_bytes()).hexdigest()
    result = {"study": "P1b", "page": PAGE, "page_sha256": sha(PAGE), "base_page": BASE_PAGE,
              "base_page_sha256": sha(BASE_PAGE), "code_commit": commit, "code_dirty": dirty, "args": vars(a),
              "G": list(G_), "PI": list(PI_), "n_gpi": n_gpi, "seeds": {k: [v[0], v[-1]] for k, v in seeds.items()},
              "qs": QS, "R_set": list(an.R_SET), "runner_shares": list(SHARES), "decisions": DECISIONS}
    t0 = time.time()
    tc = stage_tcheck(pool, seeds["tcheck"], G_, gate_views=DECISIONS["gate_views"],
                      tv_window=DECISIONS["tv_t0_window"], t3_replicate=True, force_tv=a.smoke)
    tc["decisions"] = DECISIONS
    result["tcheck"] = tc
    if not a.smoke and not SENTINEL.exists():
        append_tcheck_record(out, commit, result["page_sha256"], tc, "PASS" if tc["pass"] else tcheck_decision(tc),
                             record=TCHECK_RECORD)
    if not tc["pass"] and not a.smoke:
        result["decision"] = tcheck_decision(tc)
    else:
        if not tc["pass"]:
            result["tcheck_decision_if_real"] = tcheck_decision(tc)
        vsl = tc["vsl_enters"] or a.smoke
        tune = stage_tune(pool, seeds["tune"], G_, PI_, vsl, n_gpi)
        result["tune"] = tune
        if not a.smoke:
            write_sentinel(out, commit, result["page_sha256"], vars(a), sentinel=SENTINEL)
            log(f"sentinel {SENTINEL} written: evaluation seeds start now")
        result["eval"] = stage_eval(pool, seeds["eval"], G_, tune["arms"], vsl)
        result["decision"] = {"S1a": result["eval"]["S1"]["S1a_pass"], "S1b": result["eval"]["S1"]["S1b_pass"],
                              "S2": {c: v["statements"]["text"] for c, v in result["eval"]["S2"].items()}}
    result["wall_total_s"] = round(time.time() - t0, 1)
    result["stage_wall"] = pool.stage_wall
    result["guard"] = {"cpu_limit": a.cpu_limit, "pauses": pool.n_pauses, "pkg_temp_max_c": pool.temp_max}
    if a.smoke:
        cmp_ = smoke_p1_compare(out, a.workers, a.cpu_limit, log, commit, seeds["tcheck"], G_)
        result["smoke_report"] = smoke_report(out, pool, cmp_)
        (out / "smoke.json").write_text(json.dumps(result, indent=1, default=str))
        (out / "summary.md").write_text(summary_md(result))
        log(f"smoke done: {out / 'smoke.json'}")
        return 0
    verify("before result.json")
    (out / "summary.md").write_text(summary_md(result))
    tmp = out / "result.json.tmp"
    tmp.write_text(json.dumps(result, indent=1, default=str))
    tmp.replace(out / "result.json")
    log(f"done: {result['decision']} ({out / 'result.json'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
