"""Screen D1 runner (docs/research/protocols/screen_D1_detector_faults.md, approved V89, Addendum 2026-10-19).

Stages: tool checks (T0, T1, T3) -> STOP on failure; tuning (FX rate per demand, RF ratio per demand) on seeds
7,400,100-119 (halt before evaluation if a tuned FX rate is at a grid edge, A1); evaluation on 7,400,030-079
(5 arms x 4 faults x 2 demands); decision (Rule 5 against every fallback FX, RF, HL, A2; invalid-seed check, A5)
and the full operating map. Run once (A6): a global sentinel is written before the evaluation stage. One SUMO run per child process (v5b/d1/episode.py), at most --workers at a time, under the CPU
guard (v5b/ops/guard.py) with --cpu-limit. Raw runs and results go to --out under /home/catalin/work/phd/.

Under perfect detection O, FX, RF and NC never use the faulty reading (enforced: their fault type is 'any',
whose read() raises), so their runs are identical across fault types; by default they run once per (q, seed)
and are reused in the four fault cells. --literal runs all 2,000 combinations instead.

  screen:  python -m v5b.d1.run_screen --out /home/catalin/work/phd/v5b1_runs/screen_d1/<tag> --confirm-run-once \
             --workers 16 --cpu-limit 0.70
  smoke:   python -m v5b.d1.run_screen --smoke --out /home/catalin/work/phd/v5b1_runs/d1_smoke_<tag> --workers 4
  V100 bug re-run (v5b/bugrerun.py: same seeds, arms, grid, tuning and rules; only the meter signal changes; new
  --out; its own run-once sentinel D1_BUGRERUN_V100.json instead of D1_EVAL_STARTED.json):
           python -m v5b.d1.run_screen --bug-rerun V100 --meter-signal continuous --confirm-run-once \
             --out /home/catalin/work/phd/v5b1_runs/screen_d1/v100_bugrerun --workers 32 --cpu-limit 0.90
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from collections import deque
from pathlib import Path

import numpy as np

from v5b import bugrerun
from v5b.d1 import netgen_bn4 as net
from v5b.d1 import stats
from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.d1.episode import ARMS
from v5b.d1.faults import ANY, FAULTS, fill_diagnostics, ratio_fit
from v5b.d1.meter_signal import LEGACY
from v5b.ops.guard import ComputeGuard

PAGE = "docs/research/protocols/screen_D1_detector_faults.md"
QS = (1600.0, 2000.0)
SEEDS = {"smoke": tuple(range(7_400_000, 7_400_003)), "tcheck": tuple(range(7_400_010, 7_400_030)),
         "tune": tuple(range(7_400_100, 7_400_120)), "eval": tuple(range(7_400_030, 7_400_080))}
CALIB_ONLY = range(7_400_000, 7_400_010)
# Addendum (2026-10-19) A1: {600, 800} + 1000-2600 in 100 veh/h steps (19 rates), a superset of the build grid.
FX_GRID = (600.0, 800.0) + tuple(float(r) for r in range(1000, 2601, 100))
FALLBACKS = ("FX", "RF", "HL")   # A2; HL = hold the last healthy rate = the NV-dropout runs (identical by construction)
SENTINEL = Path("/home/catalin/work/phd/v5b1_runs/D1_EVAL_STARTED.json")   # A6: run once, across --out dirs
FX_PROBE, RF_PROBE = 1200.0, 1.0      # placeholder values for the T3 determinism runs (before tuning)
T3_SEED, T3_Q = 7_400_010, 2000.0
ALLOWED_ROOT = Path("/home/catalin/work/phd")


def spec(arm, fault, q, seed, q_fx=None, ratio=None, rep=None, kf=20.0, ncrit=8.0) -> dict:
    k = f"{arm}_{fault}_q{int(q)}_s{seed}"
    if arm == "FX":
        k += f"_fx{int(q_fx)}"
    if arm == "RF":
        k += f"_r{ratio:.6f}"
    if rep is not None:
        k += f"_rep{rep}"
    return {"key": k, "arm": arm, "fault": fault, "q": float(q), "seed": int(seed), "q_fx": q_fx, "ratio": ratio,
            "kf": kf, "ncrit": ncrit}


class CpuSampler:
    """System CPU utilisation from /proc/stat between consecutive calls."""

    def __init__(self):
        self.prev = self._read()

    @staticmethod
    def _read():
        with open("/proc/stat") as fh:
            v = [int(x) for x in fh.readline().split()[1:9]]
        return sum(v), v[3] + v[4]

    def util(self) -> float:
        tot, idle = self._read()
        dt, di = tot - self.prev[0], idle - self.prev[1]
        self.prev = (tot, idle)
        return 1.0 - di / dt if dt > 0 else 0.0


def pkg_temp() -> float:
    for h in Path("/sys/class/hwmon").glob("hwmon*"):
        try:
            if (h / "name").read_text().strip() != "coretemp":
                continue
            for lab in h.glob("temp*_label"):
                if lab.read_text().strip().startswith("Package"):
                    return int((h / lab.name.replace("_label", "_input")).read_text()) / 1000.0
        except OSError:
            continue
    return float("nan")


class Pool:
    def __init__(self, out: Path, workers: int, cpu_limit: float, log, commit: str = "", meter_signal: str = LEGACY):
        self.out, self.workers, self.log, self.commit = out, workers, log, commit
        self.meter_signal = meter_signal   # V100: passed to every child run, checked on reuse
        self.guard = ComputeGuard(overrides={"cpu_limit": cpu_limit})
        self.cpu = CpuSampler()
        (out / "runs").mkdir(parents=True, exist_ok=True)
        (out / "sumo").mkdir(parents=True, exist_ok=True)
        self.temp_max = float("nan")
        self.n_pauses = 0

    def _launch(self, s: dict, attempt: int) -> dict:
        rd = self.out / "sumo" / s["key"]
        rd.mkdir(parents=True, exist_ok=True)
        fh = open(rd / f"child_a{attempt}.log", "w")
        cmd = [PYTHON_BIN, "-m", "v5b.d1.episode",
               "--spec", json.dumps({**s, "code_commit": self.commit, "meter_signal": self.meter_signal}),
               "--out", str(self.out / "runs" / f"{s['key']}.json"), "--run-dir", str(rd)]
        p = subprocess.Popen(cmd, cwd=REPO_ROOT, env=clean_sumo_env(), stdout=fh, stderr=subprocess.STDOUT)
        return {"proc": p, "spec": s, "attempt": attempt, "paused": False, "t0": time.time(), "fh": fh}

    def run(self, specs: list, stage: str):
        res, todo, running, failed = {}, deque(), [], []
        for s in specs:
            p = self.out / "runs" / f"{s['key']}.json"
            if p.exists():
                stored = json.loads(p.read_text())
                bad = reuse_mismatch(stored, s, self.commit, self.meter_signal)
                if bad:
                    raise SystemExit(f"{s['key']}: the stored run differs in {bad}; refusing to mix configurations "
                                     "(Addendum A6): start a fresh --out")
                res[s["key"]] = stored
            else:
                todo.append((s, 0))
        n_total, t_start, t_log = len(todo), time.time(), 0.0
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
            while dec.allow_launch and todo and n_new < 2 and \
                    sum(not r["paused"] for r in running) < self.workers:
                s, att = todo.popleft()
                running.append(self._launch(s, att))
                n_new += 1
            if now - t_log >= 60.0:
                t = pkg_temp()
                if t == t and not self.temp_max >= t:
                    self.temp_max = t
                self.log(f"[{stage}] done {len(res)}/{len(specs)} running {len(running)} "
                         f"cpu {util:.2f} pkg {t:.0f} C")
                t_log = now
            time.sleep(0.5)
        self.log(f"[{stage}] finished in {time.time() - t_start:.0f} s, failed {len(failed)}")
        return res, failed


def reuse_mismatch(stored: dict, s: dict, commit: str, meter_signal: str = LEGACY) -> list:
    """Addendum A6: the fields in which a stored run differs from this invocation's spec (empty: reusable).
    A stored run without 'meter_signal' ran the legacy signal (before V100)."""
    want = {k: s[k] for k in ("arm", "fault", "q", "seed", "q_fx", "ratio", "kf", "ncrit")}
    want["code_commit"] = commit
    bad = [k for k, v in want.items() if stored.get(k) != v]
    return bad + (["meter_signal"] if stored.get("meter_signal", LEGACY) != meter_signal else [])


def grid_edge_hits(q_fx: dict, grid) -> list:
    """Addendum A1: demands whose tuned FX rate lies at a grid edge; the screen then halts before evaluation."""
    return sorted(qk for qk, r in q_fx.items() if r in (min(grid), max(grid)))


def _metric(res, keys, m="delay_s"):
    return np.array([res[k][m] for k in keys], float)


def same_run(a: dict, b: dict) -> bool:
    return all(a[k] == b[k] for k in ("hash", "delay_s", "served_ctrl_vph", "ttt_ctrl_vehh", "meter_log"))


def stage_tcheck(pool, kf, ncrit):
    sp = [spec(a, "none", q, s, kf=kf, ncrit=ncrit) for q in QS for s in SEEDS["tcheck"] for a in ("O", "NC")]
    t3 = [("O", "none", {}), ("NC", "none", {}), ("NV", "noisy", {}), ("FX", ANY, {"q_fx": FX_PROBE}),
          ("RF", ANY, {"ratio": RF_PROBE})]
    t3_specs = [[spec(a, f, T3_Q, T3_SEED, rep=rep, kf=kf, ncrit=ncrit, **kw) for rep in (0, 1)] for a, f, kw in t3]
    res, failed = pool.run(sp + [x for pair in t3_specs for x in pair], "tcheck")
    t0 = {}
    for q in QS:
        ok = [s for s in SEEDS["tcheck"] if f"O_none_q{int(q)}_s{s}" in res and f"NC_none_q{int(q)}_s{s}" in res]
        t0[str(int(q))] = stats.t0_check(_metric(res, [f"O_none_q{int(q)}_s{s}" for s in ok]),
                                         _metric(res, [f"NC_none_q{int(q)}_s{s}" for s in ok]))
    t1 = stats.t1_check([r["teleports"] for r in res.values()])
    t3r = {a: (p[0]["key"] in res and p[1]["key"] in res and same_run(res[p[0]["key"]], res[p[1]["key"]]))
           for (a, _, _), p in zip(t3, t3_specs)}
    out = {"T0": t0, "T0_pass": all(v["pass"] for v in t0.values()), "T1": t1, "T3": t3r,
           "T3_pass": all(t3r.values()), "failed_runs": failed,
           "wall_s_median": float(np.median([r["wall_s"] for r in res.values()]))}
    out["pass"] = out["T0_pass"] and t1["pass"] and out["T3_pass"]
    return out


def stage_tune(pool, grid, kf, ncrit):
    sp = [spec("O", ANY, q, s, kf=kf, ncrit=ncrit) for q in QS for s in SEEDS["tune"]]
    sp += [spec("FX", ANY, q, s, q_fx=r, kf=kf, ncrit=ncrit) for q in QS for s in SEEDS["tune"] for r in grid]
    res, failed = pool.run(sp, "tune")
    out = {"ratio": {}, "q_fx": {}, "fx_median_delay_s": {}, "failed_runs": failed}
    for q in QS:
        qk = str(int(q))
        logs = [e for s in SEEDS["tune"] if (k := f"O_{ANY}_q{qk}_s{s}") in res for e in res[k]["meter_log"]]
        n4, n3 = [e[1] for e in logs], [e[2] for e in logs]
        out["ratio"][qk] = ratio_fit(n3, n4)
        out.setdefault("rf_fill", {})[qk] = fill_diagnostics(out["ratio"][qk], n3, n4)   # A3, report only
        med = {}
        for r in grid:
            keys = [k for s in SEEDS["tune"] if (k := f"FX_{ANY}_q{qk}_s{s}_fx{int(r)}") in res]
            med[r] = float(np.median(_metric(res, keys)))
        out["fx_median_delay_s"][qk] = {str(int(r)): v for r, v in med.items()}
        out["q_fx"][qk] = stats.best_rate(med)
    out["grid"] = list(grid)
    out["grid_edge"] = grid_edge_hits(out["q_fx"], grid)
    return out


def eval_specs(q_fx, ratio, literal, kf, ncrit):
    sp = []
    for q in QS:
        qk = str(int(q))
        for s in SEEDS["eval"]:
            kw = {"FX": {"q_fx": q_fx[qk]}, "RF": {"ratio": ratio[qk]}}
            for f in (FAULTS if literal else (ANY,)):
                sp += [spec(a, f, q, s, kf=kf, ncrit=ncrit, **kw.get(a, {})) for a in ARMS if a != "NV"]
            sp += [spec("NV", f, q, s, kf=kf, ncrit=ncrit) for f in FAULTS]
    return sp


def build_cells(res, sp_index, literal):
    """sp_index: (arm, fault, q, seed) -> key. Returns cells and the operating map. HL (A2) is read from the
    NV-dropout runs. A seed enters a cell only if all of its O, FX, RF, NV and HL runs exist."""
    cells, opmap = {}, {}
    cols = ARMS + ("HL",)
    for f in FAULTS:
        for q in QS:
            qk = str(int(q))
            src = {a: (a, f if (literal or a == "NV") else ANY) for a in ARMS}
            src["HL"] = ("NV", "dropout")
            seeds = [s for s in SEEDS["eval"] if all(sp_index[(*src[a], q, s)] in res for a in cols)]
            name = f"{f}_q{qk}"
            if not seeds:
                cells[name] = {"n": 0, "pass": False, "note": "no seed with all runs"}
                opmap[name] = {"n_seeds": 0, "arms": {}}
                continue
            keys = {a: [sp_index[(*src[a], q, s)] for s in seeds] for a in cols}
            dl = {a: _metric(res, keys[a]) for a in cols}
            invalid = [any(not res[keys[a][i]]["valid"] for a in ("O",) + FALLBACKS) for i in range(len(seeds))]
            cells[name] = stats.cell_with_invalid_check(dl["O"], {a: dl[a] for a in FALLBACKS}, invalid)
            rows = {}
            for a in cols:
                rows[a] = {"median_delay_s": float(np.median(dl[a])),
                           "median_served_vph": float(np.median(_metric(res, keys[a], "served_ctrl_vph"))),
                           "median_ttt_ctrl_vehh": float(np.median(_metric(res, keys[a], "ttt_ctrl_vehh"))),
                           "median_ttt_full_vehh": float(np.median(_metric(res, keys[a], "ttt_full_vehh"))),
                           "n_invalid": int(sum(not res[k]["valid"] for k in keys[a])),
                           "n_teleport_runs": int(sum(res[k]["teleports"] > 0 for k in keys[a]))}
                if a != "O":
                    rows[a]["vs_O"] = stats.paired(dl[a], dl["O"])   # rel = (arm - O) / arm
            opmap[name] = {"n_seeds": len(seeds), "arms": rows}
    return cells, opmap


def summary_md(result: dict) -> str:
    L = [f"# Screen D1 result: **{result['decision']}**", "",
         f"Page `{PAGE}` (sha256 {result['page_sha256'][:12]}), code {result['code_commit'][:10]}"
         f"{' (dirty)' if result['code_dirty'] else ''}. Metric: door-to-door delay (s), incl. origin queue.", ""]
    tc = result["tcheck"]
    L += ["## Tool checks", "", "| q | O median | NC median | rel (NC-O)/NC | CI diff (s) | T0 |", "|---|---|---|---|---|---|"]
    for qk, r in tc["T0"].items():
        L.append(f"| {qk} | {r['med_treat']:.1f} | {r['med_base']:.1f} | {100 * r['rel']:.1f} % | "
                 f"[{r['diff_ci'][0]:.1f}, {r['diff_ci'][1]:.1f}] | {'PASS' if r['pass'] else 'FAIL'} |")
    L += ["", f"T1 teleport runs {tc['T1']['n_with_teleports']}/{tc['T1']['n_runs']} "
              f"({'PASS' if tc['T1']['pass'] else 'FAIL'}); T3 {'PASS' if tc['T3_pass'] else 'FAIL'} {tc['T3']}", ""]
    if "tune" in result:
        t = result["tune"]
        L += ["## Tuning", "", f"FX rate per q: {t['q_fx']} (grid {min(t['grid']):.0f}-{max(t['grid']):.0f}, "
              f"{len(t['grid'])} rates; at an edge: {t['grid_edge'] or 'none'}); RF ratio per q: "
              f"{ {k: round(v, 4) for k, v in t['ratio'].items()} }", ""]
        for qk, d in t["rf_fill"].items():
            L.append(f"- RF fill q={qk} (tuning seeds, A3): RMSE {d['rmse']:.2f} vs SD of the true edge-4 count "
                     f"{d['sd_down']:.2f}, corr(edge 3, edge 4) {d['corr']:.2f}: "
                     + ("informative" if d["informative"] else "no better than a constant (RF uninformative on BN4)"))
        L.append("")
    if "eval" in result:
        def hf(c, a):
            p = c["per_fallback"][a]
            return f"{100 * p['HF']:.1f} [{100 * p['HF_ci'][0]:.1f}, {100 * p['HF_ci'][1]:.1f}]"

        L += ["## Headroom HF_f = (f - O) / f, % [95 % CI] (Rule 5; Addendum A2, A5)", "",
              "A cell passes only if HF >= 10 % with CI lower bound > 0 against every fallback (FX, RF, HL), "
              "with and without seeds that have an invalid O/FX/RF/HL run. 'Rule 5 best' = best of FX, RF by median.",
              "", "| cell | n | O | FX | RF | HL | Rule 5 best | binding | inv seeds | pass all | pass valid | pass |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        yn = lambda b: "yes" if b else "no"
        for name, c in result["eval"]["cells"].items():
            if not c["n"]:
                L.append(f"| {name} | 0 | " + " | ".join(["-"] * 9) + " | no |")
                continue
            L.append(f"| {name} | {c['n']} | {c['med_O']:.1f} | {hf(c, 'FX')} | {hf(c, 'RF')} | {hf(c, 'HL')} | "
                     f"{c['best']} {'pass' if c['rule5_pass'] else 'fail'} | {c['binding']} | {c['n_invalid_seeds']} | "
                     f"{yn(c['pass_all_seeds'])} | {yn(c['pass_valid_only'])} | {yn(c['pass'])} |")
        if not result["args"]["literal"]:
            L += ["", "Under perfect detection O, FX, RF and HL do not depend on the fault type: the 4 fault cells of a "
                  "demand share these runs, so the decision has 2 independent cells (one per demand); only NV differs."]
        cols = ARMS + ("HL",)
        L += ["", "## Operating map (median delay s / served veh/h / TTT ctrl veh h; invalid runs; HL = NV-dropout runs)",
              "", "| cell | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
        def cell(r):
            inv = f"; inv {r['n_invalid']}" if r["n_invalid"] else ""
            return f"{r['median_delay_s']:.1f} / {r['median_served_vph']:.0f} / {r['median_ttt_ctrl_vehh']:.1f}{inv}"

        for name, m in result["eval"]["operating_map"].items():
            if m["arms"]:
                L.append(f"| {name} | " + " | ".join(cell(m["arms"][a]) for a in cols) + " |")
    return "\n".join(L) + "\n"


def _git(*args) -> str:
    return subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True).stdout.strip()


def check_out_dir(out: Path, resume: bool) -> None:
    out = out.resolve()
    if not out.is_relative_to(ALLOWED_ROOT) or out.is_relative_to(REPO_ROOT.resolve()):
        raise SystemExit(f"--out must be under {ALLOWED_ROOT} and outside the repo")
    if (out / "result.json").exists():
        raise SystemExit(f"{out} already holds a result: screen D1 runs once")
    if (out / "runs").exists() and any((out / "runs").iterdir()) and not resume:
        raise SystemExit(f"{out}/runs is not empty; pass --resume to reuse finished runs of an interrupted run")


def check_screen_args(a) -> None:
    """Addendum A6: a non-smoke run uses the page's meter law (K_F = 20, n_crit = 8) and the fixed FX grid."""
    if a.kf != 20.0 or a.ncrit != 8.0:
        raise SystemExit("the screen uses K_F = 20 and n_crit = 8 (page, Rule 3); other values only with --smoke")


def check_sentinel(out: Path, resume: bool, commit: str, sentinel: Path = None) -> None:
    """Addendum A6: once the evaluation stage has started anywhere, refuse every non-smoke invocation except
    --resume of the same --out at the same commit."""
    sentinel = sentinel or SENTINEL
    if not sentinel.exists():
        return
    d = json.loads(sentinel.read_text())
    if not (resume and Path(d["out"]) == out.resolve()):
        raise SystemExit(f"screen D1 evaluation already started ({sentinel}: out {d['out']}, commit "
                         f"{d['code_commit'][:10]}): it runs once; only --resume of that --out is allowed")
    if d["code_commit"] != commit:
        raise SystemExit(f"--resume refused: commit {commit[:10]} differs from {d['code_commit'][:10]} in {sentinel}")


def write_sentinel(out: Path, commit: str, page_sha: str, args: dict, sentinel: Path = None) -> None:
    """Addendum A6: written just before the evaluation stage; kept as-is on a valid --resume."""
    sentinel = sentinel or SENTINEL
    if sentinel.exists():
        return   # check_sentinel already allowed this invocation (same --out, --resume, same commit)
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    with open(sentinel, "x") as fh:
        json.dump({"out": str(out.resolve()), "code_commit": commit, "page_sha256": page_sha, "args": args,
                   "time": time.strftime("%Y-%m-%d %H:%M:%S %z")}, fh, indent=1)


def identity(orig: dict, page_sha: str) -> dict:
    """V100 bug re-run: what must equal between the original result and the current code."""
    return {"seeds": (orig.get("seeds"), {k: [v[0], v[-1]] for k, v in SEEDS.items()}), "qs": (orig.get("qs"), QS),
            "fx_grid": ((orig.get("tune") or {}).get("grid"), FX_GRID), "page_sha256": (orig.get("page_sha256"), page_sha)}


def smoke(pool, out, kf, ncrit, log) -> dict:
    s0, q0 = SEEDS["smoke"][0], 2000.0
    assert all(s in CALIB_ONLY for s in SEEDS["smoke"])
    sp = [spec(a, "none", q, s, kf=kf, ncrit=ncrit) for q in QS for s in SEEDS["smoke"] for a in ("O", "NC")]
    sp += [spec("O", "none", q0, s0, rep=1, kf=kf, ncrit=ncrit),
           spec("FX", ANY, q0, s0, q_fx=FX_PROBE, kf=kf, ncrit=ncrit),
           spec("RF", ANY, q0, s0, ratio=RF_PROBE, kf=kf, ncrit=ncrit)]
    sp += [spec("NV", f, q0, s0, kf=kf, ncrit=ncrit) for f in FAULTS]
    res, failed = pool.run(sp, "smoke")
    o_nc = {}
    for q in QS:
        qk = str(int(q))
        o_nc[qk] = [{"seed": s, "O": res[f"O_none_q{qk}_s{s}"]["delay_s"], "NC": res[f"NC_none_q{qk}_s{s}"]["delay_s"],
                     "O_served": res[f"O_none_q{qk}_s{s}"]["served_ctrl_vph"],
                     "NC_served": res[f"NC_none_q{qk}_s{s}"]["served_ctrl_vph"],
                     "O_q_median": float(np.median([e[4] for e in res[f"O_none_q{qk}_s{s}"]["meter_log"]]))}
                    for s in SEEDS["smoke"]]
    o_logs = {qk: [e for s in SEEDS["smoke"] for e in res[f"O_none_q{qk}_s{s}"]["meter_log"]] for qk in ("1600", "2000")}
    return {"failed": failed, "O_vs_NC": o_nc,
            "determinism_O_rep": same_run(res[f"O_none_q2000_s{s0}"], res[f"O_none_q2000_s{s0}_rep1"]),
            "wall_s": {k: v["wall_s"] for k, v in res.items()},
            "teleports": {k: v["teleports"] for k, v in res.items() if v["teleports"]},
            "health": {k: v["health"] for k, v in res.items()},
            "other_arms_delay_s": {k: v["delay_s"] for k, v in res.items() if not k.startswith(("O_none", "NC_none"))},
            "calib_ratio_smoke": {qk: ratio_fit([e[2] for e in v], [e[1] for e in v]) for qk, v in o_logs.items()}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--cpu-limit", type=float, default=0.90)
    ap.add_argument("--nice", type=int, default=19)
    ap.add_argument("--smoke", action="store_true", help="seeds 7,400,000-002 only, <= 4 workers")
    ap.add_argument("--confirm-run-once", action="store_true", help="required for the screen (evaluation seeds)")
    ap.add_argument("--literal", action="store_true", help="run all 5 x 4 x 2 x 50 combinations")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--kf", type=float, default=20.0)
    ap.add_argument("--ncrit", type=float, default=8.0)
    bugrerun.add_args(ap)
    a = ap.parse_args(argv)
    if not 1 <= a.workers <= 100:
        raise SystemExit("--workers must be in 1..100")
    out = Path(a.out)
    check_out_dir(out, a.resume)
    commit, dirty = _git("rev-parse", "HEAD"), bool(_git("status", "--porcelain"))
    page_sha = hashlib.sha256((REPO_ROOT / PAGE).read_bytes()).hexdigest()
    bug = bugrerun.check(a, "D1", lambda o: identity(o, page_sha))
    if not a.smoke:
        if not a.confirm_run_once:
            raise SystemExit("the screen touches the evaluation seeds once: pass --confirm-run-once")
        check_screen_args(a)
        if dirty:
            raise SystemExit("the work tree is dirty: commit first (Addendum A6)")
        if bug:   # V100: the bug re-run bypasses D1_EVAL_STARTED and is run once through its own sentinel
            check_sentinel(out, a.resume, commit, bugrerun.sentinel_path(a, "D1"))
        else:
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
    workers = min(a.workers, 4) if a.smoke else a.workers
    pool = Pool(out, workers, a.cpu_limit, log, commit=commit, meter_signal=a.meter_signal)
    result = {"screen": "D1", "page": PAGE, "page_sha256": page_sha,
              "code_commit": commit, "code_dirty": dirty, "meter_signal": a.meter_signal,
              "args": vars(a), "seeds": {k: [v[0], v[-1]] for k, v in SEEDS.items()}, "qs": QS}
    if bug:
        result["bug_rerun"] = bug
        if not a.smoke:
            write_sentinel(out, commit, page_sha, vars(a), bugrerun.sentinel_path(a, "D1"))
            log(f"bug re-run {a.bug_rerun}: sentinel {bug['sentinel']} written before the first run")
    t0 = time.time()
    if a.smoke:
        result["smoke"] = smoke(pool, out, a.kf, a.ncrit, log)
        result["wall_total_s"] = round(time.time() - t0, 1)
        (out / "smoke.json").write_text(json.dumps(result, indent=1))
        log(f"smoke done: {out / 'smoke.json'}")
        return 0
    tc = stage_tcheck(pool, a.kf, a.ncrit)
    result["tcheck"] = tc
    if not tc["pass"]:
        result["decision"] = "STOP (tool check)" if not (tc["T0_pass"] and tc["T1"]["pass"]) \
            else "FIX CODE (T3 determinism)"
    else:
        tune = stage_tune(pool, FX_GRID, a.kf, a.ncrit)
        result["tune"] = tune
    if tc["pass"] and tune["grid_edge"]:
        result["decision"] = "HALT (extend FX grid)"   # A1: before any evaluation seed is touched
    elif tc["pass"]:
        if not bug:
            write_sentinel(out, commit, result["page_sha256"], vars(a))
            log(f"sentinel {SENTINEL} written: evaluation seeds start now")
        sp = eval_specs(tune["q_fx"], tune["ratio"], a.literal, a.kf, a.ncrit)
        res, failed = pool.run(sp, "eval")
        idx = {(s["arm"], s["fault"], s["q"], s["seed"]): s["key"] for s in sp}
        cells, opmap = build_cells(res, idx, a.literal)
        result["eval"] = {"cells": cells, "operating_map": opmap, "failed_runs": failed, "n_runs": len(sp),
                          "teleport_runs": int(sum(r["teleports"] > 0 for r in res.values())),
                          "invalid_runs": int(sum(not r["valid"] for r in res.values()))}
        result["decision"] = stats.decide(cells)
    result["wall_total_s"] = round(time.time() - t0, 1)
    result["guard"] = {"cpu_limit": a.cpu_limit, "pauses": pool.n_pauses, "pkg_temp_max_c": pool.temp_max}
    (out / "summary.md").write_text((bugrerun.summary_header(bug) if bug else "") + summary_md(result))
    tmp = out / "result.json.tmp"
    tmp.write_text(json.dumps(result, indent=1))
    tmp.replace(out / "result.json")
    log(f"decision: {result['decision']} ({out / 'result.json'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
