"""P1b confirmation C1 (docs/research/protocols/p1b_confirm_c1.md, V114; approved V115): does the type plan IP beat always-on
PI in cell block_q1600? Run once, on fresh seeds, from a frozen worktree. P1b (v5b/p1b/run.py) is unchanged: this
module reuses its episode, meters, runners, pool and analysis helpers.

- plant, incident and meter as P1b (amber meter, runner share s = 0 for the claim): q = 1600 veh/h, the block incident;
- arms frozen from P1b's tuning (commit 93ba655, no re-tuning): IP = N `c1800` before onset, `p20_20_16_e4` from onset
  (stay); PI = `p70_120_8_e4` always on; reference rows N `c1800` throughout and NC;
- seeds 7,400,700-799 (100, no replicates); smoke only on 7,400,000-003;
- statement C1: rel = median(PI - IP) / median(PI) >= 10 % and the lower bound of the two-sided 95 % percentile
  bootstrap CI of median(PI - IP) > 0 (B = 20,000, seed BOOT_SEED_C1), in both views (all seeds; seeds with an invalid
  IP or PI run removed); a seed enters only if its IP and PI runs exist (P1 convention; dropped seeds are counted);
- descriptive rows (95 %, both views, no claims): IP with detection delay d in {30, 60, 120} s vs PI; IP vs PI at
  runner share s in {10 %, 30 %}; per-arm emergency stops, max queue, collisions and the V109 spill share (queue tail
  within 50 m of the entry OR mean depart delay > 5 s);
- run-once sentinel <runs root>/P1B_C1_STARTED.json (written before the first C1 seed); resume only at the same commit;
  the runs root is /home/catalin/work/phd/v5b1_runs or $V5B1_RUNS; --out defaults to <runs root>/p1b_c1/v114.

  run:   (from a detached worktree at the run commit) systemd-run --user --unit p1b-c1 --working-directory=<worktree> \
           env -u SUMO_HOME -u V5B1_RUNS OMP_NUM_THREADS=1 nice -n 19 <venv>/bin/python -m v5b.p1b.confirm_c1 \
           --confirm-run-once --workers 32 --cpu-limit 0.90
  smoke: python -m v5b.p1b.confirm_c1 --smoke --out <scratch dir> --workers 4 --cpu-limit 0.90
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np

from v5b.d1 import netgen_bn4 as net
from v5b.d1.config import REPO_ROOT, RUNS_ROOT
from v5b.d2.run_screen import make_verify, tree_state
from v5b.p1 import family as fam
from v5b.p1 import run as p1run
from v5b.p1 import stats as st
from v5b.p1b import analysis as an
from v5b.p1b import run as rs
from v5b.p1b.analysis import canon_sw, cell_name, fixed, sw
from v5b.p1b.meters import SIGNAL
from v5b.p1b.runners import SHARES

PAGE = "docs/research/protocols/p1b_confirm_c1.md"
P1B_RESULT = "docs/research/results/p1b_result.json"
P1B_COMMIT = "93ba6550fd409ab7992d6166dc976f0bcceb1046"
INC, Q = "block", 1600.0
CELL = cell_name(INC, Q)
N, IP_PLAN, PI = "c1800", "p20_20_16_e4", "p70_120_8_e4"   # frozen from P1b tuning (q = 1600), no re-tuning
SEEDS = tuple(range(7_400_700, 7_400_800))
SMOKE_SEEDS = tuple(range(7_400_000, 7_400_004))
D_ROWS = (30.0, 60.0, 120.0)
B_C1 = 20_000
BOOT_SEED_C1 = 20261020                                      # fixed before data (V114)
LEVEL_C1 = 0.95
REL_MIN = 0.10
SPILL_TAIL_M, SPILL_DEP_S = 50.0, 5.0                       # V109
SENTINEL = RUNS_ROOT / "P1B_C1_STARTED.json"
DEFAULT_OUT = RUNS_ROOT / "p1b_c1" / "v114"
ALLOWED_ROOTS = rs.ALLOWED_ROOTS
SMOKE_WORKERS_MAX = 4


class Pool(rs.Pool):
    KEEP_FIELDS = rs.KEEP + ("depart_delay_s",)              # the V109 spill indicator needs it


# ---------------------------------------------------------------- arms and runs
def ip_spec(s, d=0.0, rs_=0.0) -> dict:
    """IP: N before onset, IP_PLAN from onset (stay); with d > 0 the P1b canonical run (no switch -> the N run)."""
    if d:
        if rs_:
            raise ValueError("C1 has no row with both a detection delay and runners")
        return canon_sw(N, IP_PLAN, INC, Q, s, d=d)
    return sw(N, IP_PLAN, INC, Q, s, rs=rs_)


def arm_spec(arm: str, s) -> dict:
    """Main-run spec of a C1 arm (s = 0, d = 0): IP, PI, N, NC."""
    if arm == "IP":
        return ip_spec(s)
    return fixed({"PI": PI, "N": N, "NC": fam.NC}[arm], INC, Q, s)


ARMS = ("IP", "PI", "N", "NC")


def row_keys(seeds) -> dict:
    """{row: [key per seed]} for every C1 row: the four main arms, IP_d<d>, IP_s<s>, PI_s<s>."""
    k = {x: [arm_spec(x, s)["key"] for s in seeds] for x in ARMS}
    k.update({f"IP_d{d:g}": [ip_spec(s, d=d)["key"] for s in seeds] for d in D_ROWS})
    for r in SHARES:
        k[f"IP_s{r:g}"] = [ip_spec(s, rs_=r)["key"] for s in seeds]
        k[f"PI_s{r:g}"] = [fixed(PI, INC, Q, s, rs=r)["key"] for s in seeds]
    return k


def c1_specs(seeds) -> list:
    sp = [arm_spec(x, s) for s in seeds for x in ARMS]
    sp += [ip_spec(s, d=d) for s in seeds for d in D_ROWS]
    sp += [ip_spec(s, rs_=r) for r in SHARES for s in seeds]
    sp += [fixed(PI, INC, Q, s, rs=r) for r in SHARES for s in seeds]
    return an.uniq(sp)


def frozen_arms_check() -> dict:
    """The frozen arms against P1b's committed result (tune arms at q = 1600, IP for the block incident)."""
    p = REPO_ROOT / P1B_RESULT
    if not p.exists():
        return {"checked": False, "match": None}
    r = json.loads(p.read_text())
    a = r["tune"]["arms"]["1600"]
    got = {"N": a["N"], "IP_block": a["IP"]["block"], "PI": a["PI"], "code_commit": r["code_commit"]}
    want = {"N": N, "IP_block": IP_PLAN, "PI": PI, "code_commit": P1B_COMMIT}
    return {"checked": True, "match": got == want, "p1b": got}


# ---------------------------------------------------------------- statement C1 (pure)
def c1_view(pi, ip) -> dict:
    p = st.paired(pi, ip, LEVEL_C1, B=B_C1, seed=BOOT_SEED_C1)
    rel_ok, ci_ok = bool(p["rel"] >= REL_MIN), bool(p["diff_ci"][0] > 0.0)
    return {**p, "rel_ok": rel_ok, "ci_ok": ci_ok, "pass": rel_ok and ci_ok}


def statement_c1(pi, ip, invalid) -> dict:
    """CONFIRMED iff c1_view passes on all seeds and on the seeds without an invalid IP or PI run."""
    pi, ip, inv = np.asarray(pi, float), np.asarray(ip, float), np.asarray(invalid, bool)
    a = c1_view(pi, ip)
    keep = ~inv
    v = c1_view(pi[keep], ip[keep]) if keep.any() else None
    ok = bool(a["pass"] and v is not None and v["pass"])
    return {"all_seeds": a, "valid_only": v, "n_invalid_seeds": int(inv.sum()), "confirmed": ok,
            "text": "CONFIRMED" if ok else "NOT CONFIRMED", "rel_min": REL_MIN, "level": LEVEL_C1, "B": B_C1,
            "boot_seed": BOOT_SEED_C1}


# ---------------------------------------------------------------- analysis (pure)
def spill_v109(r: dict) -> bool:
    return bool(r["max_queue_m"] >= r["avail_m"] - SPILL_TAIL_M or r["depart_delay_s"] > SPILL_DEP_S)


def c1_row(res, keys) -> dict:
    """P1b's arm row (delay, served, TTT, emergency stops, queues, collisions) with the V109 spill share."""
    r = an.arm_row(res, keys)
    r["spill_share_b4_7m"] = r.pop("spill_share")
    r["spill_share"] = float(np.mean([spill_v109(res[k]) for k in keys])) if keys else None
    r["median_depart_delay_s"] = float(np.median([res[k]["depart_delay_s"] for k in keys]))
    return r


def _paired_rows(res, K: dict, ok_idx: list, pairs) -> dict:
    out = {}
    for ref, trt in pairs:
        if not ok_idx:
            out[f"{ref}_vs_{trt}"] = {"n_seeds": 0, "n_dropped_seeds": len(K[ref])}
            continue
        kr, kt = [K[ref][i] for i in ok_idx], [K[trt][i] for i in ok_idx]
        out[f"{ref}_vs_{trt}"] = {**an._two(an._arr(res, kr), an._arr(res, kt), an._inv(res, kr) | an._inv(res, kt),
                                            st.LEVEL_95), "n_dropped_seeds": len(K[ref]) - len(ok_idx)}
    return out


def analyse(res: dict, seeds) -> dict:
    K = row_keys(seeds)
    have = lambda rows: [i for i in range(len(seeds)) if all(K[x][i] in res for x in rows)]
    ok = have(("IP", "PI"))
    out = {"cell": CELL, "n_seeds": len(ok), "n_dropped_seeds": len(seeds) - len(ok),
           "arms": {"IP": f"{N} -> {IP_PLAN} at onset (stay)", "PI": f"{PI} always on", "N": f"{N} throughout",
                    "NC": "no control"}}
    if ok:
        kp, ki = [K["PI"][i] for i in ok], [K["IP"][i] for i in ok]
        out["C1"] = statement_c1(an._arr(res, kp), an._arr(res, ki), an._inv(res, kp) | an._inv(res, ki))
    else:
        out["C1"] = {"confirmed": False, "text": "NOT CONFIRMED", "note": "no seed with both IP and PI runs"}
    desc = {}
    desc.update(_paired_rows(res, K, have(ARMS), [(r, t) for r in ("N", "NC") for t in ("IP", "PI")]))
    for d in D_ROWS:
        x = f"IP_d{d:g}"
        i = have(("PI", "IP", x))
        desc.update(_paired_rows(res, K, i, [("PI", x), ("IP", x)]))
        desc[f"PI_vs_{x}"]["n_no_switch"] = int(sum(K[x][j] == sw(N, N, INC, Q, seeds[j])["key"] for j in i))
    for r in SHARES:
        xi, xp = f"IP_s{r:g}", f"PI_s{r:g}"
        desc.update(_paired_rows(res, K, have(("IP", "PI", xi, xp)), [(xp, xi), ("IP", xi), ("PI", xp)]))
    out["descriptive"] = desc
    out["rows"] = {x: c1_row(res, [k for k in ks if k in res]) for x, ks in K.items() if any(k in res for k in ks)}
    return out


# ---------------------------------------------------------------- report
def _p(x):
    return "-" if x is None else f"{100 * x:.1f}"


def _stat(v: dict) -> str:
    return (f"{_p(v['rel'])} % [{_p(v['rel_ci'][0])}, {_p(v['rel_ci'][1])}]; diff {v['diff']:.2f} s "
            f"[{v['diff_ci'][0]:.2f}, {v['diff_ci'][1]:.2f}], n {v['n']}")


def summary_md(result: dict) -> str:
    c = result["c1"]
    s = c["C1"]
    L = [f"# P1b confirmation C1 ({c['cell']})", "",
         f"Code {result['code_commit'][:10]}, page sha256 {result['page_sha256'][:12]}, seeds {result['seeds']}, "
         f"smoke: {result['smoke']}. Seeds used {c['n_seeds']}, dropped {c['n_dropped_seeds']}.", "",
         f"## Statement C1: **{s['text']}**", ""]
    if "all_seeds" in s:
        L += [f"rel = median(PI - IP) / median(PI) >= {_p(REL_MIN)} % and 95 % CI lower bound of median(PI - IP) > 0 "
              f"(B = {B_C1}, bootstrap seed {BOOT_SEED_C1}).", "", "| view | rel % [95 % CI] ; diff s/veh [95 % CI] | "
              "rel ok | CI ok | pass |", "|---|---|---|---|---|"]
        for v in ("all_seeds", "valid_only"):
            x = s[v]
            L.append(f"| {v} | no seed left | | | False |" if x is None else
                     f"| {v} | {_stat(x)} | {x['rel_ok']} | {x['ci_ok']} | {x['pass']} |")
        L += ["", f"Seeds with an invalid IP or PI run: {s['n_invalid_seeds']}."]
    else:
        L.append(s.get("note", ""))
    L += ["", "## Descriptive rows (95 %, report only; rel % = median(ref - t) / median(ref))", "",
          "| ref vs t | all seeds | valid only (n invalid) |", "|---|---|---|"]
    for k, v in c["descriptive"].items():
        if not v.get("n_seeds", 1):
            L.append(f"| {k} | no seeds | |")
            continue
        va = v["valid_only"]
        L.append(f"| {k} | {_stat(v['all_seeds'])} | {'-' if va is None else _stat(va)} ({v['n_invalid_seeds']}) |")
    L += ["", "## Arm rows (medians over seeds; spill = V109: tail within 50 m of the entry or mean depart delay > 5 s)",
          "", "| row | n | delay s | served veh/h | TTT ctrl veh h | depart delay s | emergency stops (all / EB at meter) | "
          "max queue m med / max (avail) | spill share | collisions | invalid |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for x, r in c["rows"].items():
        L.append(f"| {x} | {r['n']} | {r['median_delay_s']:.2f} | {r['median_served_vph']:.0f} | "
                 f"{r['median_ttt_ctrl_vehh']:.1f} | {r['median_depart_delay_s']:.2f} | {r['emergency_stops_total']} / "
                 f"{r['emergency_meter_total']} | {r['median_max_queue_m']:.0f} / {r['max_max_queue_m']:.0f} "
                 f"({r['avail_m']:.0f}) | {r['spill_share']:.2f} | {r['collisions_total']} | {r['n_invalid']} |")
    L += ["", f"Runs {result['n_runs']}, failed {len(result['failed_runs'])}, wall {result.get('wall_total_s')} s, "
          f"guard {result.get('guard')}.", ""]
    return "\n".join(L)


# ---------------------------------------------------------------- run-once and launch rules
def check_out_dir(out: Path, resume: bool) -> None:
    out = out.resolve()
    if not any(out.is_relative_to(r.resolve()) for r in ALLOWED_ROOTS) or out.is_relative_to(REPO_ROOT.resolve()):
        raise SystemExit(f"--out must be under {[str(r) for r in ALLOWED_ROOTS]} and outside the repo")
    if (out / "result.json").exists():
        raise SystemExit(f"{out} already holds a result: C1 runs once")
    if (out / "runs").exists() and any((out / "runs").iterdir()) and not resume:
        raise SystemExit(f"{out}/runs is not empty; pass --resume to reuse finished runs of an interrupted run")


def check_launch(a, dirty: bool) -> None:
    if not 1 <= a.workers <= 100:
        raise SystemExit("--workers must be in 1..100")
    if not 0.0 < a.cpu_limit <= 0.90:
        raise SystemExit("--cpu-limit must be in (0, 0.90] (author rule: CPU <= 90 %)")
    if a.smoke:
        if a.workers > SMOKE_WORKERS_MAX:
            raise SystemExit(f"--smoke uses at most {SMOKE_WORKERS_MAX} workers")
        if not all(s in rs.CALIB_ONLY for s in SMOKE_SEEDS):
            raise SystemExit("smoke seeds must be calibration seeds 7,400,000-009")
        return
    if not a.confirm_run_once:
        raise SystemExit("C1 touches the confirmatory seeds 7,400,700-799 once: pass --confirm-run-once")
    if dirty:
        raise SystemExit("the work tree is dirty: commit first")


def check_sentinel(out: Path, resume: bool, commit: str, sentinel: Path = None) -> None:
    p1run.check_sentinel(out, resume, commit, sentinel=sentinel or SENTINEL)


def write_sentinel(out: Path, commit: str, page_sha: str, args: dict, sentinel: Path = None) -> None:
    p1run.write_sentinel(out, commit, page_sha, args, sentinel=sentinel or SENTINEL)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help=f"default {DEFAULT_OUT} (runs root: $V5B1_RUNS)")
    ap.add_argument("--workers", type=int, default=SMOKE_WORKERS_MAX)
    ap.add_argument("--cpu-limit", type=float, default=rs.CPU_LIMIT_DEFAULT)
    ap.add_argument("--nice", type=int, default=19)
    ap.add_argument("--smoke", action="store_true", help="smoke seeds 7,400,000-003, <= 4 workers, explicit --out")
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
    commit, dirty = p1run._git("rev-parse", "HEAD"), bool(p1run._git("status", "--porcelain"))
    state0 = tree_state()
    check_launch(a, dirty)
    check_out_dir(out, a.resume)
    arms_ok = frozen_arms_check()
    if not a.smoke:
        if not arms_ok["match"]:
            raise SystemExit(f"the frozen arms do not match {P1B_RESULT}: {arms_ok}")
        check_sentinel(out, a.resume, commit)
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
    seeds = SMOKE_SEEDS if a.smoke else SEEDS
    page_sha = hashlib.sha256((REPO_ROOT / PAGE).read_bytes()).hexdigest()
    result = {"study": "P1b-C1", "page": PAGE, "page_sha256": page_sha, "code_commit": commit, "code_dirty": dirty,
              "args": vars(a), "smoke": a.smoke, "seeds": [seeds[0], seeds[-1]], "cell": CELL,
              "frozen_arms": {"N": N, "IP": IP_PLAN, "PI": PI, "p1b_commit": P1B_COMMIT, "check": arms_ok},
              "d_rows": list(D_ROWS), "runner_shares": list(SHARES),
              "spill_v109": {"tail_m": SPILL_TAIL_M, "depart_delay_s": SPILL_DEP_S}}
    if not a.smoke:
        write_sentinel(out, commit, page_sha, vars(a))
        log(f"sentinel {SENTINEL} written: C1 seeds start now")
    t0 = time.time()
    specs = c1_specs(seeds)
    res, failed = pool.run(specs, "c1")
    result["c1"] = analyse(res, seeds)
    result.update({"n_runs": len(specs), "failed_runs": failed,
                   "teleport_runs": int(sum(r["teleports"] > 0 for r in res.values())),
                   "invalid_runs": int(sum(not r["valid"] for r in res.values())),
                   "collision_runs": int(sum(r["collisions"] > 0 for r in res.values())),
                   "wall_total_s": round(time.time() - t0, 1), "stage_wall": pool.stage_wall,
                   "guard": {"cpu_limit": a.cpu_limit, "pauses": pool.n_pauses, "pkg_temp_max_c": pool.temp_max}})
    result["decision"] = result["c1"]["C1"]["text"]
    verify("before result.json")
    (out / "summary.md").write_text(summary_md(result))
    tmp = out / "result.json.tmp"
    tmp.write_text(json.dumps(result, indent=1, default=str))
    tmp.replace(out / "result.json")
    log(f"done: C1 {result['decision']} ({out / 'result.json'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
