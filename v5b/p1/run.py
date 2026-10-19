"""P1 runner (docs/research/protocols/p1_incident_information.md, approved V99 with A1-A10 = defaults).

Stages (one-process SUMO runs, v5b/p1/episode.py, at most --workers at a time under the CPU guard v5b/ops/guard.py):
1. Tool checks on 7,400,240-259 (A9(a)); arms chosen in hindsight on these seeds (D2-A4 f).
   A: every g in G and NC x {none, slow, block} x q x seed, plus the T3 repeat pairs;
   B: 'N_t before onset, a after' for every a in A; AD (eta = 1, FB_t's values) and NC + VSL (b = 0.4) per incident cell;
   C (only if TV-T0 binds): IP_t + VSL(b), b in {0.8, 0.6, 0.4}.
   T0 (best non-oracle arm among ID_t, IP_t, N_t, FX_t, FB_t, AD_t vs NC, every incident cell), T1, T3, T4: STOP or
   fix as page §3; T-AD and TV are reported (TV decides whether IP + VSL enters). Every non-smoke outcome is appended
   to TCHECK_RECORD (D2-A9 rules: a T0 / T4 failure with T3 passed is final; T1 / T3 failures allow a re-run only at
   another commit).
2. Tuning on 7,400,200-239: N, FX, FB, PI (A: G and the PI grid x {none, slow, block}); IP, ID (B: switch runs from N;
   AD eta grid with FB's values x {none, slow, block}); C (only if VSL entered): IP + VSL(b) per cell; the prevalence
   re-tuning of every L0 arm per pi (no new runs).
3. Evaluation on 7,400,500-599 (the global sentinel is written first: run once): switch runs from N for every a in A,
   the L0 arms and NC (and the prevalence-retuned L0 arms) x {none, slow, block}, the imperfection runs (d, c,
   combined, false alarms), IP + VSL if it entered, then the replicates k = 1..4 of every switch run (A3(a)).
   Statements S1a / S1b / S2 / S3, TP, Fig. 1 ladder data, Table 1 operating map.
Raw runs go to --out under /home/catalin/work/phd/ (never in the repo). HEAD and the work tree are re-checked after
every stage and before result.json (D2-A10).

  run:   systemd-run --user --unit p1-run --working-directory=<repo> env -u SUMO_HOME OMP_NUM_THREADS=1 nice -n 19 \
           <venv>/bin/python -m v5b.p1.run --out /home/catalin/work/phd/v5b1_runs/p1/v99 --confirm-run-once \
           --workers 32 --cpu-limit 0.90
  smoke: python -m v5b.p1.run --smoke --out /home/catalin/work/phd/v5b1_runs/p1_smoke_<tag> --workers 8 --cpu-limit 0.70
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
from v5b.d1.run_screen import CpuSampler, pkg_temp
from v5b.d2.incidents import INCIDENTS, NONE
from v5b.d2.run_screen import make_verify, tcheck_block_reason, tree_state
from v5b.ops.guard import ComputeGuard
from v5b.p1 import analysis as an
from v5b.p1 import family as fam
from v5b.p1 import stats as st
from v5b.p1.analysis import CONDITIONS, QS, RMAX, TV_B0, VSL_B, cell_name, fixed, qk, sw
from v5b.p1.episode import SPEC_FIELDS, make_spec

PAGE = "docs/research/protocols/p1_incident_information.md"
SEEDS = {"tcheck": tuple(range(7_400_240, 7_400_260)), "tune": tuple(range(7_400_200, 7_400_240)),
         "eval": tuple(range(7_400_500, 7_400_600))}
SMOKE_SEEDS = {"tcheck": tuple(range(7_400_000, 7_400_003)), "tune": tuple(range(7_400_003, 7_400_006)),
               "eval": tuple(range(7_400_006, 7_400_010))}
CALIB_ONLY = range(7_400_000, 7_400_010)
SENTINEL = Path("/home/catalin/work/phd/v5b1_runs/P1_EVAL_STARTED.json")
TCHECK_RECORD = Path("/home/catalin/work/phd/v5b1_runs/P1_TCHECK_RECORD.json")
CPU_LIMIT_DEFAULT = 0.90   # page §8 (V93)
ALLOWED_ROOT = Path("/home/catalin/work/phd")
G_SMOKE = ("c400", "c800", "c1200", "c1600", "c2000", "f10_6", "f20_8", "f70_12", "f120_16")
PI_SMOKE = ("p40_20_8_e4", "p20_10_6_e5", "p70_120_16_e4", "p40_40_4_e5")
T3_Q = 2000.0
KEEP = SPEC_FIELDS + ("key", "code_commit", "delay_s", "served_ctrl_vph", "ttt_ctrl_vehh", "ttt_full_vehh", "max_queue",
                      "valid", "teleports", "hash", "wall_s", "entered_e4_incident", "ad_max_dev", "t_on", "t_off",
                      "t_switch", "t_back", "health", "emergency_warnings", "drained")


def t3_specs(seed) -> list:
    """D2's six pairs, plus one pair each for PI (both detector variants), AD, a delayed switch (d and c), a VSL run,
    a replicate (k = 1) and a false alarm."""
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
             dict(pre="c1600", post="c800", incident=NONE, fa=True)]
    return [[make_spec(q=q, seed=seed, rep=r, **b) for r in (0, 1)] for b in base]


def reuse_mismatch(stored: dict, s: dict, commit: str) -> list:
    want = {k: s[k] for k in SPEC_FIELDS}
    want["code_commit"] = commit
    return [k for k, v in want.items() if stored.get(k) != v]


class Pool:
    """D2's pool (v5b/d2/run_screen.py) for the P1 episode; stored runs are slimmed in memory (KEEP)."""

    def __init__(self, out: Path, workers: int, cpu_limit: float, log, commit: str = "", verify=None):
        self.out, self.workers, self.log, self.commit, self.verify = out, workers, log, commit, verify
        self.guard = ComputeGuard(overrides={"cpu_limit": cpu_limit})
        self.cpu = CpuSampler()
        (out / "runs").mkdir(parents=True, exist_ok=True)
        (out / "sumo").mkdir(parents=True, exist_ok=True)
        self.temp_max = float("nan")
        self.n_pauses = 0
        self.stage_wall = {}

    @staticmethod
    def slim(r: dict) -> dict:
        return {k: r.get(k) for k in KEEP}

    def _launch(self, s: dict, attempt: int) -> dict:
        rd = self.out / "sumo" / s["key"]
        rd.mkdir(parents=True, exist_ok=True)
        fh = open(rd / f"child_a{attempt}.log", "w")
        cmd = [PYTHON_BIN, "-m", "v5b.p1.episode", "--spec", json.dumps({**s, "code_commit": self.commit}),
               "--out", str(self.out / "runs" / f"{s['key']}.json"), "--run-dir", str(rd)]
        p = subprocess.Popen(cmd, cwd=REPO_ROOT, env=clean_sumo_env(), stdout=fh, stderr=subprocess.STDOUT)
        return {"proc": p, "spec": s, "attempt": attempt, "paused": False, "t0": time.time(), "fh": fh}

    def run(self, specs: list, stage: str):
        specs = an.uniq(specs)
        res, todo, running, failed = {}, deque(), [], []
        for s in specs:
            p = self.out / "runs" / f"{s['key']}.json"
            if p.exists():
                stored = json.loads(p.read_text())
                bad = reuse_mismatch(stored, s, self.commit)
                if bad:
                    raise SystemExit(f"{s['key']}: the stored run differs in {bad}; refusing to mix configurations: "
                                     "start a fresh --out")
                res[s["key"]] = self.slim(stored)
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
                    res[key] = self.slim(json.loads(p.read_text()))
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
            while dec.allow_launch and todo and n_new < burst and sum(not r["paused"] for r in running) < self.workers:
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
        if self.verify is not None:
            self.verify(stage)
        return res, failed


def same_run(out: Path, k1: str, k2: str) -> bool:
    """T3: the stored outputs of a repeat pair are identical (outcome fields and controller / VSL logs)."""
    try:
        a, b = (json.loads((out / "runs" / f"{k}.json").read_text()) for k in (k1, k2))
    except OSError:
        return False
    return all(a.get(k) == b.get(k) for k in ("hash", "delay_s", "served_ctrl_vph", "ttt_ctrl_vehh", "max_queue",
                                              "entered_e4_incident", "meter_log", "nhat_log", "vsl_log", "t_switch",
                                              "t_back"))


def _first(order, D: dict) -> str:
    return min(order, key=lambda x: (float(np.median(D[x])), order.index(x)))


# ---------------------------------------------------------------- stage 1: tool checks
def stage_tcheck(pool, seeds, G_, force_tv: bool = False) -> dict:
    A_ = fam.actions(G_)
    t3 = t3_specs(seeds[0])
    resA, failA = pool.run(an.fixed_specs(tuple(G_) + (fam.NC,), CONDITIONS, seeds) + [x for p in t3 for x in p],
                           "tcheck-A")
    fx = {qk(q): an.fit_fixed(resA, seeds, G_, (), q) for q in QS}
    N_t = {k: v["N"] for k, v in fx.items()}
    spB = an.switch_specs(N_t, A_, seeds)
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
    best, ncs, best_name, t4, tad, tv_nc, tv_v, tv_alone = {}, {}, {}, {}, {}, {}, {}, {}
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
            b = _first(order, D)
            best[name], ncs[name], best_name[name] = D[b], D["NC"], b
            okf = [s for s in seeds if all(fixed(g, inc, q, s)["key"] in res for g in G_)]
            per = {g: [res[fixed(g, inc, q, s)["key"]]["delay_s"] for s in okf] for g in G_}
            gstar = fam.best_by_median(per, G_)
            t4[name] = st.t4_cell(per[a["N"]], per[gstar], a["N"], gstar)
            tad[name] = [res[k]["ad_max_dev"] for s in seeds if (k := fixed(a["AD"], inc, q, s)["key"]) in res]
            okv = [s for s in seeds if fixed(fam.NC, inc, q, s)["key"] in res and
                   fixed(fam.NC, inc, q, s, vsl=TV_B0)["key"] in res]
            tv_nc[name] = [res[fixed(fam.NC, inc, q, s)["key"]]["entered_e4_incident"] for s in okv]
            tv_v[name] = [res[fixed(fam.NC, inc, q, s, vsl=TV_B0)["key"]]["entered_e4_incident"] for s in okv]
            tv_alone[name] = st.paired([res[fixed(fam.NC, inc, q, s)["key"]]["delay_s"] for s in okv],
                                       [res[fixed(fam.NC, inc, q, s, vsl=TV_B0)["key"]]["delay_s"] for s in okv])
    tele = {}
    for k, r in res.items():
        if r.get("rep") is None:
            tele.setdefault(f"{r['incident']}_q{qk(r['q'])}", []).append(r["teleports"])
    t3r = {p[0]["key"]: (p[0]["key"] in res and p[1]["key"] in res and same_run(pool.out, p[0]["key"], p[1]["key"]))
           for p in t3}
    tvb = st.tv_binding(tv_nc, tv_v)
    out = {"seeds": [seeds[0], seeds[-1]], "arms": arms, "T0": st.t0_cells(best, ncs, best_name),
           "T1": st.t1_cells(tele), "T3": t3r, "T3_pass": all(t3r.values()), "T4": st.t4_overall(t4),
           "T_AD": st.tad_cells(tad), "TV_T0": tvb, "TV_alone_vs_NC_delay_b0.4_report_only": tv_alone,
           "failed_runs": failA + failB,
           "PI_note": "PI is not run on the tool-check seeds (page §8 cost: tool checks 15k); T0's best-of excludes it"}
    if tvb["pass"] or force_tv:
        spC = [sw(arms[qk(q)]["N"], arms[qk(q)]["IP"][inc], inc, q, s, vsl=b) for b in VSL_B for q in QS
               for inc in INCIDENTS for s in seeds]
        resC, failC = pool.run(spC, "tcheck-C")
        res.update(resC)
        out["failed_runs"] += failC
        ip, ipv = {}, {}
        for b in VSL_B:
            for inc in INCIDENTS:
                for q in QS:
                    a = arms[qk(q)]
                    ok = [s for s in seeds if sw(a["N"], a["IP"][inc], inc, q, s)["key"] in res and
                          sw(a["N"], a["IP"][inc], inc, q, s, vsl=b)["key"] in res]
                    key = f"b{b:g}_{cell_name(inc, q)}"
                    ip[key] = [res[sw(a["N"], a["IP"][inc], inc, q, s)["key"]]["delay_s"] for s in ok]
                    ipv[key] = [res[sw(a["N"], a["IP"][inc], inc, q, s, vsl=b)["key"]]["delay_s"] for s in ok]
        out["TV_entry"] = st.tv_entry(ip, ipv)
        out["TV_entry"]["forced_in_smoke"] = bool(force_tv and not tvb["pass"])
    else:
        out["TV_entry"] = {"enters": False, "text": "TV ended at TV-T0 (not binding)"}
    out["vsl_enters"] = bool(tvb["pass"] and out["TV_entry"]["enters"])
    out["n_runs"] = len(res)
    out["pass"] = bool(out["T0"]["pass"] and out["T1"]["pass"] and out["T3_pass"] and out["T4"]["pass"])
    return out


def tcheck_decision(tc) -> str:
    if not tc["T3_pass"]:
        return "FIX CODE (T3 determinism), then repeat the checks"
    fails = [t for t in ("T0", "T1", "T4") if not tc[t]["pass"]]
    if "T1" in fails:
        return f"STOP (tool check {', '.join(fails)}; T1: or fix the incident code with a test and re-run the checks)"
    return f"STOP (tool check {', '.join(fails)})"


# ---------------------------------------------------------------- stage 2: tuning
def stage_tune(pool, seeds, G_, PI_, vsl: bool) -> dict:
    A_ = fam.actions(G_)
    resA, failA = pool.run(an.fixed_specs(G_, CONDITIONS, seeds) + an.fixed_specs(PI_, CONDITIONS, seeds), "tune-A")
    fx = {qk(q): an.fit_fixed(resA, seeds, G_, PI_, q) for q in QS}
    spB = an.switch_specs({k: v["N"] for k, v in fx.items()}, A_, seeds)
    for q in QS:
        spB += an.fixed_specs(an.ad_candidates(fx[qk(q)]["FB"]), CONDITIONS, seeds, (q,))
    resB, failB = pool.run(spB, "tune-B")
    res = {**resA, **resB}
    arms, tables = {}, {}
    for q in QS:
        f = fx[qk(q)]
        s_ = an.fit_switch(res, seeds, A_, q, f["N"])
        ad = an.fit_ad(res, seeds, q, f["FB"])
        arms[qk(q)] = {"N": f["N"], "FX": f["FX"], "FB": f["FB"], "PI": f["PI"], "AD": ad["AD"], "IP": s_["IP"],
                       "ID": s_["ID"]}
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
        edges[k] = {x: fam.grid_edges(c) for x, c in chosen.items() if fam.grid_edges(c)}
    return {"seeds": [seeds[0], seeds[-1]], "arms": arms, "tables": tables, "grid_edges_report_only": edges,
            "failed_runs": failA + failB + failC, "n_runs": len(res)}


# ---------------------------------------------------------------- stage 3: evaluation
def stage_eval(pool, seeds, G_, arms, vsl: bool) -> dict:
    A_ = fam.actions(G_)
    sp = an.eval_specs(arms, A_, seeds, RMAX, vsl)
    res, failed = pool.run(sp, "eval")
    ev = an.evaluate(res, seeds, A_, arms, RMAX, vsl, log=pool.log)
    mism = 0
    for q in QS:   # consistency: N's fixed run and the switch run 'N -> N' are the same trajectory
        N = arms[qk(q)]["N"]
        for inc in INCIDENTS:
            for s in seeds:
                k1, k2 = fixed(N, inc, q, s)["key"], sw(N, N, inc, q, s)["key"]
                if k1 in res and k2 in res and res[k1]["hash"] != res[k2]["hash"]:
                    mism += 1
    ev.update({"seeds": [seeds[0], seeds[-1]], "failed_runs": failed, "n_runs": len(sp),
               "teleport_runs": int(sum(r["teleports"] > 0 for r in res.values())),
               "invalid_runs": int(sum(not r["valid"] for r in res.values())),
               "N_fixed_vs_switch_hash_mismatches": mism})
    return ev


# ---------------------------------------------------------------- run counts and report
def run_counts(n_g: int = len(fam.G), n_pi: int = len(fam.PI), seeds: dict = None, vsl: bool = True,
               tv_binds: bool = True) -> dict:
    """Runs per stage (upper bounds where the page's runs depend on the chosen arms: every d / c / combined run
    distinct, every prevalence arm new, VSL entering)."""
    S = {k: len(v) for k, v in (seeds or SEEDS).items()}
    nq, ni, nc = len(QS), len(INCIDENTS), len(CONDITIONS)
    na = 2 * n_g
    tc = (n_g + 1) * nc * nq * S["tcheck"] + 2 * len(t3_specs(0)) + na * ni * nq * S["tcheck"] + \
        2 * ni * nq * S["tcheck"] + (len(VSL_B) * ni * nq * S["tcheck"] if tv_binds else 0)
    tu = (n_g + n_pi) * nc * nq * S["tune"] + na * ni * nq * S["tune"] + len(fam.ETA_GRID) * nc * nq * S["tune"] + \
        (len(VSL_B) * ni * nq * S["tune"] if vsl else 0)
    ev_main = na * ni * nq * S["eval"]
    ev_reps = RMAX * ev_main
    ev_l0 = 6 * nc * nq * S["eval"]
    ev_imp = ni * nq * S["eval"] * (len(an.D_GRID) - 1 + len(an.C_GRID) - 1 + 2 + 1)   # d, c, combined x2, false alarm
    ev_prev = 5 * len(an.PIS) * nc * nq * S["eval"]
    ev_vsl = ni * nq * S["eval"] if vsl else 0
    ev = ev_main + ev_reps + ev_l0 + ev_imp + ev_vsl
    return {"tcheck": tc, "tune": tu, "eval": ev, "eval_replicates": ev_reps, "total": tc + tu + ev,
            "eval_prevalence_upper_extra": ev_prev, "total_upper": tc + tu + ev + ev_prev}


def _pct(x):
    return "-" if x is None else f"{100 * x:.1f}"


def summary_md(result: dict) -> str:
    smoke = result["args"]["smoke"]
    L = [f"# P1 {'SMOKE (build check, not a result)' if smoke else 'result'}", "",
         f"Page `{PAGE}` (sha256 {result['page_sha256'][:12]}), code {result['code_commit'][:10]}"
         f"{' (dirty)' if result['code_dirty'] else ''}. |G| = {len(result['G'])}, |A| = {2 * len(result['G'])}, "
         f"|PI| = {len(result['PI'])}. Delay: door-to-door s/veh incl. origin and meter queue.", ""]
    tc = result["tcheck"]
    L += ["## Tool checks", "", "| cell | T0 best | rel vs NC | CI diff | T0 | T4 N_t / g* rel | T4 | T-AD med | TV-T0 rel |",
          "|---|---|---|---|---|---|---|---|---|"]
    for name, r in tc["T0"]["cells"].items():
        t4, tad, tv = tc["T4"]["cells"][name], tc["T_AD"][name], tc["TV_T0"]["cells"].get(name, {})
        L.append(f"| {name} | {r['best_arm']} | {_pct(r['rel'])} % | [{r['diff_ci'][0]:.1f}, {r['diff_ci'][1]:.1f}] | "
                 f"{'PASS' if r['pass'] else 'FAIL'} | {t4['N']} / {t4['best_fixed']} {_pct(t4['rel'])} % | "
                 f"{'PASS' if t4['pass'] else 'fail'} | {tad['median_max_dev']:.1f} {tad['note']} | "
                 f"{_pct(tv.get('rel'))} % |")
    L += ["", f"T1 {'PASS' if tc['T1']['pass'] else 'FAIL'}; T3 {'PASS' if tc['T3_pass'] else 'FAIL'}; "
          f"TV-T0 {'binds' if tc['TV_T0']['pass'] else 'does not bind: ' + tc['TV_T0']['text']}; "
          f"TV entry: {'VSL enters' if tc['vsl_enters'] else tc['TV_entry'].get('text', '')}"
          f"{' (forced in smoke)' if tc['TV_entry'].get('forced_in_smoke') else ''}.", ""]
    if "tune" in result:
        L += ["## Tuning (arms per q)", ""] + [f"- q = {k}: " + ", ".join(f"{x} {v[x]}" for x in
                                                                         ("N", "FX", "FB", "PI", "AD", "ID")) +
                                               f", IP {v['IP']}" + (f", VSL b {v['VSL_b']}" if v.get("VSL_b") else "")
                                               for k, v in result["tune"]["arms"].items()]
        L += [f"- grid edges (report only): {result['tune']['grid_edges_report_only']}", ""]
    if "eval" in result:
        ev = result["eval"]
        s1 = ev["S1"]
        L += ["## S1 (information ladder)", "",
              f"- S1a: **{'PASS' if s1['S1a_pass'] else 'FAIL'}**: {s1['S1a_text']}",
              f"- S1b: **{'PASS' if s1['S1b_pass'] else 'FAIL'}**: {s1['S1b_text']}", "",
              "| cell | ID vs N | vs FX | vs FB | vs PI | vs AD | IP vs ID | (rel %, all seeds; S1 level) |",
              "|---|---|---|---|---|---|---|---|"]
        for c, v in s1["per_cell_stats"].items():
            L.append(f"| {c} | " + " | ".join(_pct(v["ID_vs"][r]["all_seeds"]["rel"]) for r in an.L0) +
                     f" | {_pct(v['IP_vs_ID']['all_seeds']['rel'])} | |")
        L += ["", "## S2 (per-incident information beyond IP)", ""]
        for c, v in ev["S2"].items():
            L.append(f"- {c}: {v['statements']['text']}; TP {_pct(ev['TP'][c]['rel'])} %")
        L += ["", "## S3 (break-even, smallest over L0 arms, all seeds)", "", "| cell | d* | c* | p* | combined vs IP |",
              "|---|---|---|---|---|"]
        for c, v in ev["S3"].items():
            if "d_star" not in v:
                continue
            f = lambda b: f"{b['all_seeds']['value']:.2f} ({b['all_seeds']['flag']}, {b['all_seeds']['binding_arm']})"
            L.append(f"| {c} | {f(v['d_star'])} | {f(v['c_star'])} | {f(v['p_star'])} | "
                     f"{_pct(v['combined_row']['vs_IP']['all_seeds']['rel'])} % |")
        L += ["", "Clean day (median delay s; ID = IP = N): " + "; ".join(
            f"q {k}: " + ", ".join(f"{x} {r['median_delay_s']:.1f}" for x, r in v["clean_day"].items() if "median_delay_s" in r)
            for k, v in ev["per_q"].items() if v.get("n_seeds")), ""]
        L += ["", "Per q: false-alarm cost (s/veh) and f*(pi):", ""]
        for k, v in ev["per_q"].items():
            if v.get("n_seeds"):
                fc = v["false_alarm_cost"]["all_seeds"]
                L.append(f"- q {k}: FA cost {fc['diff']:.2f} [{fc['diff_ci'][0]:.2f}, {fc['diff_ci'][1]:.2f}]; f* " +
                         ", ".join(f"pi {p}: {r['f_star']['all_seeds']['value']:.2f}" for p, r in v["prevalence"].items()))
        L += ["", "## Table 1 (median delay s / served veh/h / max queue; invalid)", ""]
        for c, m in ev["table1_operating_map"].items():
            L.append(f"- {c}: " + "; ".join(f"{x} {r['median_delay_s']:.1f}/{r['median_served_vph']:.0f}/"
                                             f"{r['median_max_queue']:.0f}" + (f" inv {r['n_invalid']}" if r['n_invalid'] else "")
                                             for x, r in m["arms"].items()))
        L += ["", f"Runs {ev['n_runs']}, failed {len(ev['failed_runs'])}, teleport runs {ev['teleport_runs']}, invalid "
              f"{ev['invalid_runs']}, N fixed vs N->N hash mismatches {ev['N_fixed_vs_switch_hash_mismatches']}."]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- run-once and directory rules
def _git(*args) -> str:
    return subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True).stdout.strip()


def check_out_dir(out: Path, resume: bool) -> None:
    out = out.resolve()
    if not out.is_relative_to(ALLOWED_ROOT) or out.is_relative_to(REPO_ROOT.resolve()):
        raise SystemExit(f"--out must be under {ALLOWED_ROOT} and outside the repo")
    if (out / "result.json").exists():
        raise SystemExit(f"{out} already holds a result: P1 runs once")
    if (out / "runs").exists() and any((out / "runs").iterdir()) and not resume:
        raise SystemExit(f"{out}/runs is not empty; pass --resume to reuse finished runs of an interrupted run")


def check_sentinel(out: Path, resume: bool, commit: str, sentinel: Path = None) -> None:
    sentinel = sentinel or SENTINEL
    if not sentinel.exists():
        return
    d = json.loads(sentinel.read_text())
    if not (resume and Path(d["out"]) == out.resolve()):
        raise SystemExit(f"P1 evaluation already started ({sentinel}: out {d['out']}, commit {d['code_commit'][:10]}): "
                         "it runs once; only --resume of that --out is allowed")
    if d["code_commit"] != commit:
        raise SystemExit(f"--resume refused: commit {commit[:10]} differs from {d['code_commit'][:10]} in {sentinel}")


def write_sentinel(out: Path, commit: str, page_sha: str, args: dict, sentinel: Path = None) -> None:
    sentinel = sentinel or SENTINEL
    if sentinel.exists():
        return
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    with open(sentinel, "x") as fh:
        json.dump({"out": str(out.resolve()), "code_commit": commit, "page_sha256": page_sha, "args": args,
                   "time": time.strftime("%Y-%m-%d %H:%M:%S %z")}, fh, indent=1)


def _read_record(record: Path) -> list:
    return json.loads(record.read_text()) if record.exists() else []


def check_tcheck_record(commit: str, record: Path = None) -> None:
    why = tcheck_block_reason(_read_record(record or TCHECK_RECORD), commit)
    if why:
        raise SystemExit(f"P1 tool checks refused: {why} ({record or TCHECK_RECORD})")


def append_tcheck_record(out: Path, commit: str, page_sha: str, tc: dict, decision: str, record: Path = None) -> None:
    record = record or TCHECK_RECORD
    entries = _read_record(record)
    entries.append({"out": str(out.resolve()), "code_commit": commit, "page_sha256": page_sha, "decision": decision,
                    "pass": bool(tc["pass"]), "T0_pass": bool(tc["T0"]["pass"]), "T1_pass": bool(tc["T1"]["pass"]),
                    "T3_pass": bool(tc["T3_pass"]), "T4_pass": bool(tc["T4"]["pass"]),
                    "TV_T0_binds": bool(tc["TV_T0"]["pass"]), "vsl_enters": bool(tc["vsl_enters"]),
                    "time": time.strftime("%Y-%m-%d %H:%M:%S %z")})
    record.parent.mkdir(parents=True, exist_ok=True)
    tmp = record.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(entries, indent=1))
    tmp.replace(record)


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
        raise SystemExit("P1 touches the tool-check, tuning and evaluation seeds once: pass --confirm-run-once")
    if dirty:
        raise SystemExit("the work tree is dirty: commit first")


def smoke_report(out: Path, pool, seeds: dict) -> dict:
    runs = [json.loads(p.read_text()) for p in (out / "runs").glob("*.json")]
    walls = np.array([r["wall_s"] for r in runs], float)
    n_runs = sum(v["runs"] for v in pool.stage_wall.values())
    wall = sum(v["wall_s"] for v in pool.stage_wall.values())
    thr = n_runs / wall if wall else float("nan")
    rc = run_counts()
    med = float(np.median(walls))
    return {"n_runs": len(runs), "wall_s_per_run": {"median": med, "p90": float(np.percentile(walls, 90)),
                                                    "max": float(walls.max())},
            "wall_s_by_kind": {k: float(np.median([r["wall_s"] for r in runs if _kind(r) == k]))
                               for k in sorted({_kind(r) for r in runs})},
            "teleport_runs": int(sum(r["teleports"] > 0 for r in runs)),
            "teleports_total": int(sum(r["teleports"] for r in runs)),
            "invalid_runs": int(sum(not r["valid"] for r in runs)), "health": dict(Counter(r["health"] for r in runs)),
            "throughput_runs_per_s": thr, "workers": pool.workers, "full_run_counts": rc,
            "full_wall_estimate_32w_linear_h": rc["total"] * med / 32 / 3600.0,
            "full_wall_estimate_32w_at_d2_rate_h": rc["total"] / 9.0 / 3600.0}   # D2: 9.0 runs/s at 32 workers


def _kind(r: dict) -> str:
    if r.get("fa"):
        return "false_alarm"
    if r.get("vsl_b") is not None:
        return "vsl"
    if r.get("k"):
        return "replicate"
    if r.get("d") or r.get("c"):
        return "delayed"
    if r.get("post"):
        return "switch"
    p = r["pre"]
    return "NC" if p == "NC" else ("PI" if p.startswith("p") else "AD" if p.startswith("ad") else "fixed")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--cpu-limit", type=float, default=CPU_LIMIT_DEFAULT)
    ap.add_argument("--nice", type=int, default=19)
    ap.add_argument("--smoke", action="store_true", help="smoke seeds 7,400,000-009, G / PI subsets, <= 8 workers")
    ap.add_argument("--confirm-run-once", action="store_true", help="required for the real run")
    ap.add_argument("--resume", action="store_true")
    return ap


def main(argv=None) -> int:
    a = build_parser().parse_args(argv)
    out = Path(a.out)
    commit, dirty = _git("rev-parse", "HEAD"), bool(_git("status", "--porcelain"))
    state0 = tree_state()
    check_launch(a, dirty)
    check_out_dir(out, a.resume)
    if not a.smoke:
        check_sentinel(out, a.resume, commit)
        if not SENTINEL.exists():
            check_tcheck_record(commit)
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
    pool = Pool(out, a.workers, a.cpu_limit, log, commit=commit, verify=verify)
    G_, PI_ = (G_SMOKE, PI_SMOKE) if a.smoke else (fam.G, fam.PI)
    seeds = SMOKE_SEEDS if a.smoke else SEEDS
    page = REPO_ROOT / PAGE
    result = {"study": "P1", "page": PAGE, "page_sha256": hashlib.sha256(page.read_bytes()).hexdigest(),
              "code_commit": commit, "code_dirty": dirty, "args": vars(a), "G": list(G_), "PI": list(PI_),
              "seeds": {k: [v[0], v[-1]] for k, v in seeds.items()}, "qs": QS, "R_set": list(an.R_SET)}
    t0 = time.time()
    tc = stage_tcheck(pool, seeds["tcheck"], G_, force_tv=a.smoke)
    result["tcheck"] = tc
    if not a.smoke and not SENTINEL.exists():
        append_tcheck_record(out, commit, result["page_sha256"], tc, "PASS" if tc["pass"] else tcheck_decision(tc))
    if not tc["pass"] and not a.smoke:
        result["decision"] = tcheck_decision(tc)
    else:
        if not tc["pass"]:
            result["tcheck_decision_if_real"] = tcheck_decision(tc)
        vsl = tc["vsl_enters"] or a.smoke
        tune = stage_tune(pool, seeds["tune"], G_, PI_, vsl)
        result["tune"] = tune
        if not a.smoke:
            write_sentinel(out, commit, result["page_sha256"], vars(a))
            log(f"sentinel {SENTINEL} written: evaluation seeds start now")
        result["eval"] = stage_eval(pool, seeds["eval"], G_, tune["arms"], vsl)
        result["decision"] = {"S1a": result["eval"]["S1"]["S1a_pass"], "S1b": result["eval"]["S1"]["S1b_pass"],
                              "S2": {c: v["statements"]["text"] for c, v in result["eval"]["S2"].items()}}
    result["wall_total_s"] = round(time.time() - t0, 1)
    result["stage_wall"] = pool.stage_wall
    result["guard"] = {"cpu_limit": a.cpu_limit, "pauses": pool.n_pauses, "pkg_temp_max_c": pool.temp_max}
    if a.smoke:
        result["smoke_report"] = smoke_report(out, pool, seeds)
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
