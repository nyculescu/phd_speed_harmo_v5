"""Screen D1 runner (docs/research/protocols/screen_D1_detector_faults_draft.md, approved V89).

Stages: tool checks (T0, T1, T3) -> STOP on failure; tuning (FX rate per demand, RF ratio per demand) on seeds
7,400,100-119; evaluation on 7,400,030-079 (5 arms x 4 faults x 2 demands); decision (Rule 5) and the full
operating map. One SUMO run per child process (v5b/d1/episode.py), at most --workers at a time, under the CPU
guard (v5b/ops/guard.py) with --cpu-limit. Raw runs and results go to --out under /home/catalin/work/phd/.

Under perfect detection O, FX, RF and NC never use the faulty reading (enforced: their fault type is 'any',
whose read() raises), so their runs are identical across fault types; by default they run once per (q, seed)
and are reused in the four fault cells. --literal runs all 2,000 combinations instead.

  screen:  python -m v5b.d1.run_screen --out /home/catalin/work/phd/v5b1_runs/d1_<tag> --confirm-run-once \
             --workers 8 --cpu-limit 0.70
  smoke:   python -m v5b.d1.run_screen --smoke --out /home/catalin/work/phd/v5b1_runs/d1_smoke_<tag> --workers 4
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

from v5b.d1 import netgen_bn4 as net
from v5b.d1 import stats
from v5b.d1.config import PYTHON_BIN, REPO_ROOT, clean_sumo_env
from v5b.d1.episode import ARMS
from v5b.d1.faults import ANY, FAULTS, ratio_fit
from v5b.ops.guard import ComputeGuard

PAGE = "docs/research/protocols/screen_D1_detector_faults_draft.md"
QS = (1600.0, 2000.0)
SEEDS = {"smoke": tuple(range(7_400_000, 7_400_003)), "tcheck": tuple(range(7_400_010, 7_400_030)),
         "tune": tuple(range(7_400_100, 7_400_120)), "eval": tuple(range(7_400_030, 7_400_080))}
CALIB_ONLY = range(7_400_000, 7_400_010)
FX_GRID = (600.0, 800.0, 1000.0, 1200.0, 1400.0, 1600.0, 2000.0, 2400.0)
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
    def __init__(self, out: Path, workers: int, cpu_limit: float, log):
        self.out, self.workers, self.log = out, workers, log
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
        cmd = [PYTHON_BIN, "-m", "v5b.d1.episode", "--spec", json.dumps(s),
               "--out", str(self.out / "runs" / f"{s['key']}.json"), "--run-dir", str(rd)]
        p = subprocess.Popen(cmd, cwd=REPO_ROOT, env=clean_sumo_env(), stdout=fh, stderr=subprocess.STDOUT)
        return {"proc": p, "spec": s, "attempt": attempt, "paused": False, "t0": time.time(), "fh": fh}

    def run(self, specs: list, stage: str):
        res, todo, running, failed = {}, deque(), [], []
        for s in specs:
            p = self.out / "runs" / f"{s['key']}.json"
            if p.exists():
                res[s["key"]] = json.loads(p.read_text())
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
        out["ratio"][qk] = ratio_fit([e[2] for e in logs], [e[1] for e in logs])
        med = {}
        for r in grid:
            keys = [k for s in SEEDS["tune"] if (k := f"FX_{ANY}_q{qk}_s{s}_fx{int(r)}") in res]
            med[r] = float(np.median(_metric(res, keys)))
        out["fx_median_delay_s"][qk] = {str(int(r)): v for r, v in med.items()}
        out["q_fx"][qk] = stats.best_rate(med)
        if out["q_fx"][qk] in (min(grid), max(grid)):
            out.setdefault("warnings", []).append(f"q={qk}: tuned FX rate {out['q_fx'][qk]} at the grid edge")
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
    """sp_index: (arm, fault, q, seed) -> key. Returns cells and the operating map."""
    cells, opmap = {}, {}
    for f in FAULTS:
        for q in QS:
            qk = str(int(q))
            fl = {a: (f if (literal or a == "NV") else ANY) for a in ARMS}
            seeds = [s for s in SEEDS["eval"] if all(sp_index[(a, fl[a], q, s)] in res for a in ARMS)]
            keys = {a: [sp_index[(a, fl[a], q, s)] for s in seeds] for a in ARMS}
            dl = {a: _metric(res, keys[a]) for a in ARMS}
            c = stats.headroom_cell(dl["O"], dl["FX"], dl["RF"])
            name = f"{f}_q{qk}"
            cells[name] = c
            rows = {}
            for a in ARMS:
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
        L += ["## Tuning", "", f"FX rate per q: {t['q_fx']}; RF ratio per q: "
              f"{ {k: round(v, 4) for k, v in t['ratio'].items()} }; warnings: {t.get('warnings', [])}", ""]
    if "eval" in result:
        L += ["## Headroom HF = (best of FX, RF - O) / best (Rule 5)", "",
              "| cell | n | best | O | best | HF | 95 % CI | pass |", "|---|---|---|---|---|---|---|---|"]
        for name, c in result["eval"]["cells"].items():
            L.append(f"| {name} | {c['n']} | {c['best']} | {c['med_O']:.1f} | {c['med_best']:.1f} | "
                     f"{100 * c['HF']:.1f} % | [{100 * c['HF_ci'][0]:.1f}, {100 * c['HF_ci'][1]:.1f}] % | "
                     f"{'yes' if c['pass'] else 'no'} |")
        L += ["", "## Operating map (median delay s / served veh/h / TTT ctrl veh h; invalid runs)", "",
              "| cell | " + " | ".join(ARMS) + " |", "|---" * (len(ARMS) + 1) + "|"]
        def cell(r):
            inv = f"; inv {r['n_invalid']}" if r["n_invalid"] else ""
            return f"{r['median_delay_s']:.1f} / {r['median_served_vph']:.0f} / {r['median_ttt_ctrl_vehh']:.1f}{inv}"

        for name, m in result["eval"]["operating_map"].items():
            L.append(f"| {name} | " + " | ".join(cell(m["arms"][a]) for a in ARMS) + " |")
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
    ap.add_argument("--fx-grid", default=",".join(str(int(x)) for x in FX_GRID))
    a = ap.parse_args(argv)
    if not 1 <= a.workers <= 100:
        raise SystemExit("--workers must be in 1..100")
    out = Path(a.out)
    check_out_dir(out, a.resume)
    if not a.smoke and not a.confirm_run_once:
        raise SystemExit("the screen touches the evaluation seeds once: pass --confirm-run-once")
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
    pool = Pool(out, workers, a.cpu_limit, log)
    page = REPO_ROOT / PAGE
    result = {"screen": "D1", "page": PAGE, "page_sha256": hashlib.sha256(page.read_bytes()).hexdigest(),
              "code_commit": _git("rev-parse", "HEAD"), "code_dirty": bool(_git("status", "--porcelain")),
              "args": vars(a), "seeds": {k: [v[0], v[-1]] for k, v in SEEDS.items()}, "qs": QS}
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
        grid = tuple(float(x) for x in a.fx_grid.split(","))
        tune = stage_tune(pool, grid, a.kf, a.ncrit)
        result["tune"] = tune
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
    (out / "summary.md").write_text(summary_md(result))
    tmp = out / "result.json.tmp"
    tmp.write_text(json.dumps(result, indent=1))
    tmp.replace(out / "result.json")
    log(f"decision: {result['decision']} ({out / 'result.json'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
