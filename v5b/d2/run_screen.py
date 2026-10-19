"""Screen D2 runner (docs/research/protocols/screen_D2_incidents.md, V91).

Stages (each a set of one-process SUMO runs, v5b/d2/episode.py, at most --workers at a time under the CPU guard):
1. Tool checks on seeds 7,400,080-099 (Rule 1), before any tuning. The arms are formed in hindsight on these
   seeds: N_t = best of G without incident; FX_t / FB_t = best constant / feedback controller on the pooled slow +
   block runs (no switching); IP_t = best switch target per incident type; OR_t = per-seed best switch target.
   A: every g in G and NC x {none, slow, block} x q x seed (fixed controllers), plus the T3 repeat pairs;
   B: 'N_t before onset, g after onset' for every g x {slow, block} x q x seed.
   T0 every incident cell: the best arm by median beats NC by >= 10 % (CI of the median difference > 0);
   T1 every (condition, q) cell: share of runs with a teleport < 5 %; T3 the repeat pairs are identical;
   T4 >= 1 incident cell: N_t's delay exceeds the hindsight-best fixed controller's by >= 10 % (paired median).
   Any failure ends the screen (STOP; T3: FIX CODE) before the tuning and evaluation seeds are touched.
2. Tuning on seeds 7,400,120-139: N per q (no-incident runs); FX, FB per q (pooled slow + block runs, the whole
   episode, no switching); IP per (type, q) from the runs 'N before onset, g after onset'.
3. Evaluation on seeds 7,400,140-189 (run once: the global sentinel is written first). Runs 'N before onset, g after
   onset' for every g (IP, OR and N itself are read from these), FX, FB and NC per incident cell, and N, FX, FB, NC
   without incident (report-only cell). Rule 5: HD_f = (f - OR) / f for f in {FX, FB, IP}; CONTINUE if some
   incident cell has HD >= 10 % with CI lower bound > 0 against every f, with and without invalid seeds.
Raw runs and results go to --out under /home/catalin/work/phd/ (never in the repo).

  screen: python -m v5b.d2.run_screen --out /home/catalin/work/phd/v5b1_runs/screen_d2/<tag> --confirm-run-once \
            --workers 16 --cpu-limit 0.70
  smoke:  python -m v5b.d2.run_screen --smoke --out /home/catalin/work/phd/v5b1_runs/d2_smoke_<tag> --workers 8
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from collections import Counter, deque
from pathlib import Path

import numpy as np

from v5b.d1 import netgen_bn4 as net
from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.d1.run_screen import CpuSampler, pkg_temp, same_run
from v5b.d2 import controllers as ctl
from v5b.d2 import stats
from v5b.d2.episode import run_key
from v5b.d2.incidents import CONDITIONS, INCIDENTS, NONE
from v5b.ops.guard import ComputeGuard

PAGE = "docs/research/protocols/screen_D2_incidents.md"
QS = (1600.0, 2000.0)
SEEDS = {"smoke": tuple(range(7_400_000, 7_400_004)), "tcheck": tuple(range(7_400_080, 7_400_100)),
         "tune": tuple(range(7_400_120, 7_400_140)), "eval": tuple(range(7_400_140, 7_400_190))}
CALIB_ONLY = range(7_400_000, 7_400_010)
SENTINEL = Path("/home/catalin/work/phd/v5b1_runs/D2_EVAL_STARTED.json")
ALLOWED_ROOT = Path("/home/catalin/work/phd")
G_SMOKE = ("c800", "c1200", "c1600", "c2000", "f10_6", "f20_8", "f70_12")
T3_RUNS = (("c1200", None, "block"), ("f20_8", None, "slow"), ("NC", None, "block"),
           ("c1600", "f40_10", "block"), ("f20_8", "c800", "slow"))
T3_Q = 2000.0
ARMS = ("OR", "IP", "N", "FX", "FB", "NC")
SPEC_FIELDS = ("pre", "post", "incident", "q", "seed")


def qk(q) -> str:
    return str(int(q))


def spec(pre, post, incident, q, seed, rep=None) -> dict:
    return {"key": run_key(pre, post, incident, q, seed, rep), "pre": pre, "post": post, "incident": incident,
            "q": float(q), "seed": int(seed)}


def uniq(specs: list) -> list:
    seen, out = set(), []
    for s in specs:
        if s["key"] not in seen:
            seen.add(s["key"])
            out.append(s)
    return out


def fixed_specs(G_, conds, seeds, with_nc: bool) -> list:
    pres = tuple(G_) + ((ctl.NC,) if with_nc else ())
    return [spec(g, None, c, q, s) for q in QS for s in seeds for c in conds for g in pres]


def switch_specs(N: dict, G_, seeds) -> list:
    return [spec(N[qk(q)], g, inc, q, s) for q in QS for s in seeds for inc in INCIDENTS for g in G_]


def t3_specs(seed) -> list:
    return [[spec(p, po, inc, T3_Q, seed, rep=r) for r in (0, 1)] for p, po, inc in T3_RUNS]


def eval_specs(arms: dict, G_, seeds) -> list:
    """arms: q -> {'N', 'FX', 'FB', 'IP': {inc: cid}}."""
    sp = switch_specs({k: v["N"] for k, v in arms.items()}, G_, seeds)
    for q in QS:
        a = arms[qk(q)]
        for s in seeds:
            for inc in INCIDENTS:
                sp += [spec(a["FX"], None, inc, q, s), spec(a["FB"], None, inc, q, s), spec(ctl.NC, None, inc, q, s)]
            sp += [spec(c, None, NONE, q, s) for c in (a["N"], a["FX"], a["FB"], ctl.NC)]
    return uniq(sp)


def reuse_mismatch(stored: dict, s: dict, commit: str) -> list:
    """The fields in which a stored run differs from this invocation's spec (empty: reusable). As D1 A6."""
    want = {k: s[k] for k in SPEC_FIELDS}
    want["code_commit"] = commit
    return [k for k, v in want.items() if stored.get(k) != v]


class Pool:
    """D1's pool (v5b/d1/run_screen.py) for the D2 episode; launches up to max(2, workers // 4) runs per 0.25 s."""

    def __init__(self, out: Path, workers: int, cpu_limit: float, log, commit: str = ""):
        self.out, self.workers, self.log, self.commit = out, workers, log, commit
        self.guard = ComputeGuard(overrides={"cpu_limit": cpu_limit})
        self.cpu = CpuSampler()
        (out / "runs").mkdir(parents=True, exist_ok=True)
        (out / "sumo").mkdir(parents=True, exist_ok=True)
        self.temp_max = float("nan")
        self.n_pauses = 0
        self.stage_wall = {}

    def _launch(self, s: dict, attempt: int) -> dict:
        rd = self.out / "sumo" / s["key"]
        rd.mkdir(parents=True, exist_ok=True)
        fh = open(rd / f"child_a{attempt}.log", "w")
        cmd = [PYTHON_BIN, "-m", "v5b.d2.episode", "--spec", json.dumps({**s, "code_commit": self.commit}),
               "--out", str(self.out / "runs" / f"{s['key']}.json"), "--run-dir", str(rd)]
        p = subprocess.Popen(cmd, cwd=REPO_ROOT, env=clean_sumo_env(), stdout=fh, stderr=subprocess.STDOUT)
        return {"proc": p, "spec": s, "attempt": attempt, "paused": False, "t0": time.time(), "fh": fh}

    def run(self, specs: list, stage: str):
        res, todo, running, failed = {}, deque(), [], []
        for s in uniq(specs):
            p = self.out / "runs" / f"{s['key']}.json"
            if p.exists():
                stored = json.loads(p.read_text())
                bad = reuse_mismatch(stored, s, self.commit)
                if bad:
                    raise SystemExit(f"{s['key']}: the stored run differs in {bad}; refusing to mix configurations: "
                                     "start a fresh --out")
                res[s["key"]] = stored
            else:
                todo.append((s, 0))
        n_total, t_start, t_log = len(todo), time.time(), 0.0
        burst = max(2, self.workers // 4)
        self.log(f"[{stage}] {n_total} runs to do ({len(res)} reused), workers {self.workers}")
        while todo or running:
            for r in list(running):
                rc = r["proc"].poll()
                if rc is None:
                    continue
                running.remove(r)
                r["fh"].close()
                key = r["spec"]["key"]
                p = self.out / "runs" / f"{key}.json"
                if rc == 0 and p.exists():
                    res[key] = json.loads(p.read_text())
                elif r["attempt"] == 0:
                    self.log(f"[{stage}] OPS failure {key} rc={rc}: re-run once")
                    todo.appendleft((r["spec"], 1))
                else:
                    self.log(f"[{stage}] FAILED twice {key} rc={rc}")
                    failed.append(key)
            now = time.time()
            util = self.cpu.util()
            dec = self.guard.update(now, util, float("nan"), n_paused=sum(r["paused"] for r in running))
            if dec.pause_one:
                act = [r for r in running if not r["paused"]]
                if act:
                    r = max(act, key=lambda x: x["t0"])
                    os.kill(r["proc"].pid, signal.SIGSTOP)
                    r["paused"] = True
                    self.n_pauses += 1
                    self.log(f"[{stage}] guard: CPU {util:.2f} > limit for 2 min, paused {r['spec']['key']}")
            elif dec.resume_one:
                ps = [r for r in running if r["paused"]]
                if ps:
                    r = min(ps, key=lambda x: x["t0"])
                    os.kill(r["proc"].pid, signal.SIGCONT)
                    r["paused"] = False
                    self.log(f"[{stage}] guard: resumed {r['spec']['key']}")
            n_new = 0
            while dec.allow_launch and todo and n_new < burst and \
                    sum(not r["paused"] for r in running) < self.workers:
                s, att = todo.popleft()
                running.append(self._launch(s, att))
                n_new += 1
            if now - t_log >= 60.0:
                t = pkg_temp()
                if t == t and not self.temp_max >= t:
                    self.temp_max = t
                self.log(f"[{stage}] done {len(res)}/{len(specs)} running {len(running)} cpu {util:.2f} pkg {t:.0f} C")
                t_log = now
            time.sleep(0.25)
        wall = time.time() - t_start
        self.stage_wall[stage] = {"runs": n_total, "wall_s": round(wall, 1)}
        self.log(f"[{stage}] finished {n_total} runs in {wall:.0f} s, failed {len(failed)}")
        return res, failed


# ---------------------------------------------------------------- arms (pure, on stored run dicts)
def _d(res, key, m="delay_s"):
    return res[key][m]


def fit_fixed_arms(res, seeds, G_, q) -> dict:
    """N (no incident), FX and FB (pooled slow + block runs, no switching) by median delay; plus the tables."""
    none = {g: [_d(res, k) for s in seeds if (k := run_key(g, None, NONE, q, s)) in res] for g in G_}
    pooled = {g: [_d(res, k) for inc in INCIDENTS for s in seeds if (k := run_key(g, None, inc, q, s)) in res]
              for g in G_}
    return {"N": ctl.best_by_median(none, G_),
            "FX": ctl.best_by_median(pooled, [g for g in G_ if g in ctl.CONST]),
            "FB": ctl.best_by_median(pooled, [g for g in G_ if g in ctl.FEEDBACK]),
            "median_none": {g: float(np.median(v)) for g, v in none.items() if v},
            "median_incident_pooled": {g: float(np.median(v)) for g, v in pooled.items() if v}}


def fit_ip(res, seeds, G_, q, N) -> dict:
    """IP per incident type: the switch target g with the lowest median delay of 'N before onset, g after'."""
    out, tab = {}, {}
    for inc in INCIDENTS:
        per = {g: [_d(res, k) for s in seeds if (k := run_key(N, g, inc, q, s)) in res] for g in G_}
        out[inc] = ctl.best_by_median(per, G_)
        tab[inc] = {g: float(np.median(v)) for g, v in per.items() if v}
    return {"IP": out, "median_switch": tab}


def cell_keys(res, seeds, G_, q, inc, arms) -> tuple:
    """Per seed: the run keys of every arm in one incident cell; OR = per-seed best of the switch runs.
    A seed enters only if all its runs exist (all |G| switch runs, FX, FB, NC). Returns (seeds, keys, or_pick)."""
    N, ip = arms["N"], arms["IP"][inc]
    ok, keys, pick = [], {a: [] for a in ARMS}, []
    for s in seeds:
        sw = {g: run_key(N, g, inc, q, s) for g in G_}
        k = {"N": sw[N], "IP": sw[ip], "FX": run_key(arms["FX"], None, inc, q, s),
             "FB": run_key(arms["FB"], None, inc, q, s), "NC": run_key(ctl.NC, None, inc, q, s)}
        if not all(x in res for x in list(sw.values()) + list(k.values())):
            continue
        g_or, _ = ctl.oracle_pick({g: _d(res, x) for g, x in sw.items()})
        k["OR"] = sw[g_or]
        ok.append(s)
        pick.append(g_or)
        for a in ARMS:
            keys[a].append(k[a])
    return ok, keys, pick


def arm_row(res, keys) -> dict:
    v = lambda m: np.array([_d(res, k, m) for k in keys], float)
    return {"median_delay_s": float(np.median(v("delay_s"))), "median_served_vph": float(np.median(v("served_ctrl_vph"))),
            "median_ttt_ctrl_vehh": float(np.median(v("ttt_ctrl_vehh"))),
            "median_ttt_full_vehh": float(np.median(v("ttt_full_vehh"))),
            "n_invalid": int(sum(not res[k]["valid"] for k in keys)),
            "n_teleport_runs": int(sum(res[k]["teleports"] > 0 for k in keys))}


def incident_cells(res, seeds, G_, arms_by_q) -> tuple:
    """Rule 5 cells and the operating map for every incident type x demand."""
    cells, opmap = {}, {}
    for inc in INCIDENTS:
        for q in QS:
            name, arms = f"{inc}_q{qk(q)}", arms_by_q[qk(q)]
            ok, keys, pick = cell_keys(res, seeds, G_, q, inc, arms)
            if not ok:
                cells[name] = {"n": 0, "pass": False, "note": "no seed with all runs"}
                opmap[name] = {"n_seeds": 0, "arms": {}}
                continue
            dl = {a: np.array([_d(res, k) for k in keys[a]], float) for a in ARMS}
            invalid = [any(not res[keys[a][i]]["valid"] for a in ("OR",) + stats.FALLBACKS) for i in range(len(ok))]
            cells[name] = stats.cell_with_invalid_check(dl["OR"], {a: dl[a] for a in stats.FALLBACKS}, invalid)
            rows = {a: arm_row(res, keys[a]) for a in ARMS}
            for a in ARMS:
                if a != "OR":
                    rows[a]["vs_OR"] = stats.paired(dl[a], dl["OR"])   # rel = (arm - OR) / arm
            sw_med = {g: float(np.median([_d(res, run_key(arms["N"], g, inc, q, s)) for s in ok])) for g in G_}
            opmap[name] = {"n_seeds": len(ok), "controllers": {a: (arms[a] if a != "IP" else arms["IP"][inc])
                                                               for a in ("N", "FX", "FB", "IP")},
                           "arms": rows, "or_picks": dict(Counter(pick).most_common()),
                           "median_switch_by_target": sw_med,
                           "n_invalid_switch_runs": int(sum(not res[run_key(arms["N"], g, inc, q, s)]["valid"]
                                                            for g in G_ for s in ok))}
    return cells, opmap


def none_cell(res, seeds, arms_by_q) -> dict:
    """Report-only no-incident cell: N (= IP = OR without incident), FX, FB, NC."""
    out = {}
    for q in QS:
        a = arms_by_q[qk(q)]
        src = {"N": a["N"], "FX": a["FX"], "FB": a["FB"], "NC": ctl.NC}
        ok = [s for s in seeds if all(run_key(c, None, NONE, q, s) in res for c in src.values())]
        if not ok:
            out[f"none_q{qk(q)}"] = {"n_seeds": 0}
            continue
        keys = {k: [run_key(c, None, NONE, q, s) for s in ok] for k, c in src.items()}
        rows = {k: arm_row(res, v) for k, v in keys.items()}
        dn = np.array([_d(res, x) for x in keys["N"]], float)
        for k in ("FX", "FB", "NC"):
            rows[k]["vs_N"] = stats.paired(np.array([_d(res, x) for x in keys[k]], float), dn)
        out[f"none_q{qk(q)}"] = {"n_seeds": len(ok), "controllers": src, "arms": rows}
    return out


# ---------------------------------------------------------------- stages
def stage_tcheck(pool, seeds, G_) -> dict:
    t3 = t3_specs(seeds[0])
    resA, failA = pool.run(fixed_specs(G_, CONDITIONS, seeds, True) + [x for p in t3 for x in p], "tcheck-A")
    fixed = {qk(q): fit_fixed_arms(resA, seeds, G_, q) for q in QS}
    N_t = {k: v["N"] for k, v in fixed.items()}
    resB, failB = pool.run(switch_specs(N_t, G_, seeds), "tcheck-B")
    res = {**resA, **resB}
    arms = {}
    for q in QS:
        f = fixed[qk(q)]
        arms[qk(q)] = {"N": f["N"], "FX": f["FX"], "FB": f["FB"], **fit_ip(res, seeds, G_, q, f["N"])}
    best, ncs, best_name, t4 = {}, {}, {}, {}
    for inc in INCIDENTS:
        for q in QS:
            name, a = f"{inc}_q{qk(q)}", arms[qk(q)]
            ok, keys, _ = cell_keys(res, seeds, G_, q, inc, a)
            if not ok:
                raise SystemExit(f"tool checks: no seed with all runs in cell {name} (failed runs: {failA + failB})")
            dl = {x: np.array([_d(res, k) for k in keys[x]], float) for x in ARMS}
            b = min(("OR", "IP", "N", "FX", "FB"), key=lambda x: (float(np.median(dl[x])), x))
            best[name], ncs[name], best_name[name] = dl[b], dl["NC"], b
            # T4: hindsight-best fixed controller in this cell's incident runs vs the no-incident tuned N_t
            okf = [s for s in seeds if all(run_key(g, None, inc, q, s) in res for g in G_)]
            per = {g: [_d(res, run_key(g, None, inc, q, s)) for s in okf] for g in G_}
            gstar = ctl.best_by_median(per, G_)
            t4[name] = stats.t4_cell(per[a["N"]], per[gstar], a["N"], gstar)
    tele = {}
    for k, r in res.items():
        if "_rep" not in k:
            tele.setdefault(f"{r['incident']}_q{qk(r['q'])}", []).append(r["teleports"])
    t3r = {p[0]["key"]: (p[0]["key"] in res and p[1]["key"] in res and same_run(res[p[0]["key"]], res[p[1]["key"]]))
           for p in t3}
    out = {"seeds": [seeds[0], seeds[-1]], "arms": {k: {x: v[x] for x in ("N", "FX", "FB", "IP")} for k, v in arms.items()},
           "T0": stats.t0_cells(best, ncs, best_name), "T1": stats.t1_cells(tele), "T3": t3r,
           "T3_pass": all(t3r.values()), "T4": stats.t4_overall(t4), "failed_runs": failA + failB,
           "n_runs": len(res), "wall_s_median": float(np.median([r["wall_s"] for r in res.values()])),
           "tables": {k: {"median_none": v["median_none"], "median_incident_pooled": v["median_incident_pooled"],
                          "median_switch": arms[k]["median_switch"]} for k, v in fixed.items()}}
    out["cells"], out["operating_map"] = incident_cells(res, seeds, G_, arms)
    out["pass"] = out["T0"]["pass"] and out["T1"]["pass"] and out["T3_pass"] and out["T4"]["pass"]
    return out


def tcheck_decision(tc) -> str:
    if not tc["T3_pass"]:
        return "FIX CODE (T3 determinism), then repeat the checks"
    fails = [t for t in ("T0", "T1", "T4") if not tc[t]["pass"]]
    if "T1" in fails:
        return f"STOP (tool check {', '.join(fails)}; T1: or fix the incident code with a test and re-run the checks)"
    return f"STOP (tool check {', '.join(fails)})"


def stage_tune(pool, seeds, G_) -> dict:
    resA, failA = pool.run(fixed_specs(G_, CONDITIONS, seeds, False), "tune-A")
    fixed = {qk(q): fit_fixed_arms(resA, seeds, G_, q) for q in QS}
    resB, failB = pool.run(switch_specs({k: v["N"] for k, v in fixed.items()}, G_, seeds), "tune-B")
    res = {**resA, **resB}
    arms, tables = {}, {}
    for q in QS:
        f = fixed[qk(q)]
        ip = fit_ip(res, seeds, G_, q, f["N"])
        arms[qk(q)] = {"N": f["N"], "FX": f["FX"], "FB": f["FB"], "IP": ip["IP"]}
        tables[qk(q)] = {"median_none": f["median_none"], "median_incident_pooled": f["median_incident_pooled"],
                         "median_switch": ip["median_switch"]}
    edge = {c for c in (ctl.CONST[0], ctl.CONST[-1])}
    at_edge = sorted({f"{k}:{x}={v[x]}" for k, v in arms.items() for x in ("N", "FX") if v[x] in edge} |
                     {f"{k}:IP_{i}={c}" for k, v in arms.items() for i, c in v["IP"].items() if c in edge})
    return {"seeds": [seeds[0], seeds[-1]], "arms": arms, "tables": tables, "grid_edge_report_only": at_edge,
            "failed_runs": failA + failB, "n_runs": len(res)}


def stage_eval(pool, seeds, G_, arms) -> dict:
    sp = eval_specs(arms, G_, seeds)
    res, failed = pool.run(sp, "eval")
    cells, opmap = incident_cells(res, seeds, G_, arms)
    return {"seeds": [seeds[0], seeds[-1]], "cells": cells, "operating_map": opmap,
            "none_cell_report_only": none_cell(res, seeds, arms), "failed_runs": failed, "n_runs": len(sp),
            "teleport_runs": int(sum(r["teleports"] > 0 for r in res.values())),
            "invalid_runs": int(sum(not r["valid"] for r in res.values())), "decision": stats.decide(cells)}


# ---------------------------------------------------------------- report
def _pct(x):
    return f"{100 * x:.1f}"


def summary_md(result: dict) -> str:
    smoke = result["args"]["smoke"]
    L = [f"# Screen D2 {'SMOKE (build check, not a result)' if smoke else 'result'}: **{result.get('decision', '-')}**",
         "", f"Page `{PAGE}` (sha256 {result['page_sha256'][:12]}), code {result['code_commit'][:10]}"
         f"{' (dirty)' if result['code_dirty'] else ''}. G = {len(result['G'])} controllers. Metric: door-to-door "
         "delay (s) incl. origin and ramp (meter) queue; served = arrivals in the control period (veh/h); TTT ctrl "
         "= veh h in [0, control end].", ""]
    tc = result["tcheck"]
    L += ["## Tool checks (hindsight arms on the tool-check seeds)", "",
          "| cell | best arm | its median | NC median | rel (NC-best)/NC | CI diff (s) | T0 | T4: N_t / best fixed | "
          "T4 rel [CI] | T4 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for name, r in tc["T0"]["cells"].items():
        t4 = tc["T4"]["cells"][name]
        L.append(f"| {name} | {r['best_arm']} | {r['med_treat']:.1f} | {r['med_base']:.1f} | {_pct(r['rel'])} % | "
                 f"[{r['diff_ci'][0]:.1f}, {r['diff_ci'][1]:.1f}] | {'PASS' if r['pass'] else 'FAIL'} | "
                 f"{t4['N']} / {t4['best_fixed']} | {_pct(t4['rel'])} [{_pct(t4['rel_ci'][0])}, {_pct(t4['rel_ci'][1])}] | "
                 f"{'PASS' if t4['pass'] else 'fail'} |")
    t1 = tc["T1"]["cells"]
    L += ["", "T0 must pass in every incident cell; T4 in at least one. T1 teleport runs per cell: " +
          ", ".join(f"{c} {v['n_with_teleports']}/{v['n_runs']}" for c, v in t1.items()) +
          f" ({'PASS' if tc['T1']['pass'] else 'FAIL'}). T3 {'PASS' if tc['T3_pass'] else 'FAIL'}. "
          f"Tool-check arms: {tc['arms']}", ""]
    if "tune" in result:
        t = result["tune"]
        L += ["## Tuning", ""] + [f"- q = {k}: N = {v['N']}, FX = {v['FX']}, FB = {v['FB']}, IP = {v['IP']}"
                                  for k, v in t["arms"].items()]
        L += [f"- at a grid edge (report only): {t['grid_edge_report_only'] or 'none'}", ""]
    if "eval" in result:
        ev = result["eval"]

        def hd(c, a):
            p = c["per_fallback"][a]
            return f"{_pct(p['HD'])} [{_pct(p['HD_ci'][0])}, {_pct(p['HD_ci'][1])}]"

        yn = lambda b: "yes" if b else "no"
        L += ["## Headroom HD_f = (f - OR) / f, % [95 % CI] (Rule 5)", "",
              "A cell passes only if HD >= 10 % with CI lower bound > 0 against every fallback (FX, FB, IP), with and "
              "without seeds that have an invalid OR/FX/FB/IP run.", "",
              "| cell | n | OR | vs FX | vs FB | vs IP | binding | inv seeds | pass all | pass valid | pass |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for name, c in ev["cells"].items():
            if not c["n"]:
                L.append(f"| {name} | 0 | " + " | ".join(["-"] * 8) + " | no |")
                continue
            L.append(f"| {name} | {c['n']} | {c['med_OR']:.1f} | {hd(c, 'FX')} | {hd(c, 'FB')} | {hd(c, 'IP')} | "
                     f"{c['binding']} | {c['n_invalid_seeds']} | {yn(c['pass_all_seeds'])} | "
                     f"{yn(c['pass_valid_only'])} | {yn(c['pass'])} |")
        L += ["", "## Operating map (median delay s / served veh/h / TTT ctrl veh h; invalid runs)", "",
              "| cell | " + " | ".join(ARMS) + " | controllers | OR picks (top 3) |", "|---" * (len(ARMS) + 3) + "|"]

        def cell(r):
            inv = f"; inv {r['n_invalid']}" if r["n_invalid"] else ""
            return f"{r['median_delay_s']:.1f} / {r['median_served_vph']:.0f} / {r['median_ttt_ctrl_vehh']:.1f}{inv}"

        for name, m in ev["operating_map"].items():
            if m["arms"]:
                top = dict(list(m["or_picks"].items())[:3])
                L.append(f"| {name} | " + " | ".join(cell(m["arms"][a]) for a in ARMS) +
                         f" | {m['controllers']} | {top} |")
        L += ["", "No-incident cell (report only; IP = OR = N):", ""]
        for name, m in ev["none_cell_report_only"].items():
            if m.get("n_seeds"):
                L.append(f"- {name} (n {m['n_seeds']}): " + ", ".join(
                    f"{k} {m['controllers'][k]} {cell(r)}" for k, r in m["arms"].items()))
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- run-once and directory rules
def _git(*args) -> str:
    return subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True).stdout.strip()


def check_out_dir(out: Path, resume: bool) -> None:
    out = out.resolve()
    if not out.is_relative_to(ALLOWED_ROOT) or out.is_relative_to(REPO_ROOT.resolve()):
        raise SystemExit(f"--out must be under {ALLOWED_ROOT} and outside the repo")
    if (out / "result.json").exists():
        raise SystemExit(f"{out} already holds a result: screen D2 runs once")
    if (out / "runs").exists() and any((out / "runs").iterdir()) and not resume:
        raise SystemExit(f"{out}/runs is not empty; pass --resume to reuse finished runs of an interrupted run")


def check_sentinel(out: Path, resume: bool, commit: str, sentinel: Path = None) -> None:
    """Once the evaluation stage has started anywhere, refuse every non-smoke invocation except --resume of the
    same --out at the same commit."""
    sentinel = sentinel or SENTINEL
    if not sentinel.exists():
        return
    d = json.loads(sentinel.read_text())
    if not (resume and Path(d["out"]) == out.resolve()):
        raise SystemExit(f"screen D2 evaluation already started ({sentinel}: out {d['out']}, commit "
                         f"{d['code_commit'][:10]}): it runs once; only --resume of that --out is allowed")
    if d["code_commit"] != commit:
        raise SystemExit(f"--resume refused: commit {commit[:10]} differs from {d['code_commit'][:10]} in {sentinel}")


def write_sentinel(out: Path, commit: str, page_sha: str, args: dict, sentinel: Path = None) -> None:
    sentinel = sentinel or SENTINEL
    if sentinel.exists():
        return   # check_sentinel already allowed this invocation (same --out, --resume, same commit)
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    with open(sentinel, "x") as fh:
        json.dump({"out": str(out.resolve()), "code_commit": commit, "page_sha256": page_sha, "args": args,
                   "time": time.strftime("%Y-%m-%d %H:%M:%S %z")}, fh, indent=1)


def check_launch(a, dirty: bool) -> None:
    if not 1 <= a.workers <= 100:
        raise SystemExit("--workers must be in 1..100")
    if a.smoke:
        if a.workers > 8:
            raise SystemExit("--smoke uses at most 8 workers")
        if not all(s in CALIB_ONLY for s in SEEDS["smoke"]):
            raise SystemExit("smoke seeds must be calibration seeds 7,400,000-009")
        return
    if not a.confirm_run_once:
        raise SystemExit("the screen touches the evaluation seeds once: pass --confirm-run-once")
    if dirty:
        raise SystemExit("the work tree is dirty: commit first")


def run_counts(n_g: int = len(ctl.G)) -> dict:
    """Runs per stage of the real screen (before de-duplication of coinciding eval controllers)."""
    nq, ninc, ncond = len(QS), len(INCIDENTS), len(CONDITIONS)
    s = {k: len(v) for k, v in SEEDS.items()}
    tc = (n_g + 1) * ncond * nq * s["tcheck"] + 2 * len(T3_RUNS) + n_g * ninc * nq * s["tcheck"]
    tu = n_g * ncond * nq * s["tune"] + n_g * ninc * nq * s["tune"]
    ev = n_g * ninc * nq * s["eval"] + 3 * ninc * nq * s["eval"] + 4 * nq * s["eval"]
    return {"tcheck": tc, "tune": tu, "eval": ev, "total": tc + tu + ev}


def smoke_report(out: Path, pool) -> dict:
    runs = [json.loads(p.read_text()) for p in (out / "runs").glob("*.json")]
    by_key = {r["key"]: r for r in runs}
    walls = np.array([r["wall_s"] for r in runs], float)
    eff = {}
    for q in QS:   # incident effect: fixed controllers and NC, paired per seed, delay(incident) / delay(none)
        for inc in INCIDENTS:
            rat = []
            for r in runs:
                if r["incident"] == inc and r["q"] == q and r["post"] is None and "_rep" not in r["key"]:
                    b = by_key.get(run_key(r["pre"], None, NONE, q, r["seed"]))
                    if b:
                        rat.append(r["delay_s"] / b["delay_s"] - 1.0)
            eff[f"{inc}_q{qk(q)}"] = {"n_pairs": len(rat), "median_rel_increase": float(np.median(rat)),
                                      "share_increase_gt_5pct": float(np.mean(np.array(rat) > 0.05))}
    n_runs = sum(v["runs"] for v in pool.stage_wall.values())
    wall = sum(v["wall_s"] for v in pool.stage_wall.values())
    rc = run_counts()
    thr = n_runs / wall if wall else float("nan")   # runs / s at the smoke's worker count
    return {"n_runs": len(runs), "wall_s_per_run": {"median": float(np.median(walls)), "p90": float(np.percentile(walls, 90)),
                                                     "max": float(walls.max())},
            "teleport_runs": int(sum(r["teleports"] > 0 for r in runs)), "teleports_total": int(sum(r["teleports"] for r in runs)),
            "invalid_runs": int(sum(not r["valid"] for r in runs)),
            "health": dict(Counter(r["health"] for r in runs)),
            "emergency_warnings_median": float(np.median([r["emergency_warnings"] for r in runs])),
            "incident_effect_vs_none": eff, "throughput_runs_per_s": thr, "workers": pool.workers,
            "screen_run_counts": rc,
            "screen_wall_estimate_16w_s": rc["total"] / (thr * 16 / pool.workers) if thr == thr else None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--cpu-limit", type=float, default=0.90)
    ap.add_argument("--nice", type=int, default=19)
    ap.add_argument("--smoke", action="store_true", help="smoke seeds 7,400,000-003, G subset, <= 8 workers")
    ap.add_argument("--confirm-run-once", action="store_true", help="required for the screen (evaluation seeds)")
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args(argv)
    out = Path(a.out)
    commit, dirty = _git("rev-parse", "HEAD"), bool(_git("status", "--porcelain"))
    check_launch(a, dirty)
    check_out_dir(out, a.resume)
    if not a.smoke:
        check_sentinel(out, a.resume, commit)
    os.nice(max(0, a.nice - os.nice(0)))
    out.mkdir(parents=True, exist_ok=True)
    logf = out / "run.log"

    def log(msg):
        line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
        print(line, flush=True)
        with open(logf, "a") as fh:
            fh.write(line + "\n")

    net.build()   # build the cached network once, before any worker starts
    pool = Pool(out, a.workers, a.cpu_limit, log, commit=commit)
    page = REPO_ROOT / PAGE
    G_ = G_SMOKE if a.smoke else ctl.G
    seeds = {k: SEEDS["smoke"] for k in ("tcheck", "tune", "eval")} if a.smoke else SEEDS
    result = {"screen": "D2", "page": PAGE, "page_sha256": hashlib.sha256(page.read_bytes()).hexdigest(),
              "code_commit": commit, "code_dirty": dirty, "args": vars(a), "G": list(G_),
              "seeds": {k: [v[0], v[-1]] for k, v in seeds.items()}, "qs": QS}
    t0 = time.time()
    tc = stage_tcheck(pool, seeds["tcheck"], G_)
    result["tcheck"] = tc
    if not tc["pass"] and not a.smoke:
        result["decision"] = tcheck_decision(tc)
    else:
        if not tc["pass"]:
            result["tcheck_decision_if_real"] = tcheck_decision(tc)
        tune = stage_tune(pool, seeds["tune"], G_)
        result["tune"] = tune
        if not a.smoke:
            write_sentinel(out, commit, result["page_sha256"], vars(a))
            log(f"sentinel {SENTINEL} written: evaluation seeds start now")
        result["eval"] = stage_eval(pool, seeds["eval"], G_, tune["arms"])
        result["decision"] = result["eval"]["decision"]
    result["wall_total_s"] = round(time.time() - t0, 1)
    result["stage_wall"] = pool.stage_wall
    result["guard"] = {"cpu_limit": a.cpu_limit, "pauses": pool.n_pauses, "pkg_temp_max_c": pool.temp_max}
    if a.smoke:
        result["smoke_report"] = smoke_report(out, pool)
        (out / "smoke.json").write_text(json.dumps(result, indent=1))
        (out / "summary.md").write_text(summary_md(result))
        log(f"smoke done: {out / 'smoke.json'}")
        return 0
    (out / "summary.md").write_text(summary_md(result))
    tmp = out / "result.json.tmp"
    tmp.write_text(json.dumps(result, indent=1))
    tmp.replace(out / "result.json")
    log(f"decision: {result['decision']} ({out / 'result.json'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
