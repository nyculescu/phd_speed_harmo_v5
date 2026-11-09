"""Plan B shared helpers: conditions, seeds, the run function and resumable batches (planb.md §6)."""
import atexit
import fcntl
import hashlib
import json
import multiprocessing as mp
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
for p in (ROOT, ROOT / "docs/research/round1", ROOT / "docs/research/round2"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import cma2  # noqa: E402
from common1 import OPPONENTS, rule_cfg  # noqa: E402

Q = 5300.0
BLOCK = (7_480_000, 7_480_999)
CELLS = ("SURGE", "TRUCK")
KEYS = ("all_delay", "delay_s", "ttc_net", "collisions", "passed", "alks_full_moving", "finished_pct")
REF_SPEED = 100.0 / 3.6
W_CF = 10.0     # MPC-F's cost weight, as planb_ctrl.W_CF


def seeds(lo: int, hi: int) -> list:
    """An inclusive range inside the approved block (V480)."""
    if not (BLOCK[0] <= lo <= hi <= BLOCK[1]):
        raise SystemExit(f"seeds {lo}-{hi} outside the approved block {BLOCK}")
    return list(range(lo, hi + 1))


def cfg(ctrl: dict, cond: str) -> dict:
    return rule_cfg(ctrl, cond)


def slim(row: dict) -> dict:
    out = {"q": row["q"], "seed": row["seed"], **{k: float(row.get(k) or 0.0) for k in KEYS}}
    if "ctrl_log" in row:
        out["ctrl_log"] = row["ctrl_log"]
    return out


def run_cfg(a: tuple) -> dict:
    t0 = time.time()
    from v5b.fleet import plant_sweep as ps
    return {**slim(ps.run_one(a)), "wall_s": round(time.time() - t0, 1)}


def run_jobs(jobs: list, workers: int):
    failed = []
    ex = ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1)
    try:
        futs = {ex.submit(run_cfg, j): j for j in jobs}
        for fut in as_completed(futs):
            j = futs[fut]
            try:
                m = fut.result()
            except BrokenProcessPool:
                raise
            except Exception as x:
                failed.append(j[0])
                print("FAILED", j[0], j[2], j[3], repr(x)[:300], flush=True)
                continue
            yield (j[0], j[2], j[3]), m
    finally:
        ex.shutdown(wait=True, cancel_futures=True)
    if failed:
        raise RuntimeError(f"{len(failed)} of {len(jobs)} runs failed, first {failed[0]}")


def batch(cfgs: dict, seed_list: list, path: Path, rd: Path, workers: int, runner=run_jobs) -> dict:
    """Run every (name, seed) pair at Q that path lacks; return {(name, seed): row} for the requested pairs."""
    cache = {(r["name"], r["q"], r["seed"]): r for r in cma2.load(path)}
    cma2.fill(cfgs, [(Q, s) for s in seed_list], cache, path, str(rd), workers, runner)
    return {(n, s): cache[(n, Q, s)] for n in cfgs for s in seed_list}


def paired(A: list, B: list, key: str) -> float:
    """The median paired difference A - B in % of B's median (negative = A lower), the round 2 point statistic."""
    d = float(np.median([a[key] - b[key] for a, b in zip(A, B)]))
    return 100.0 * d / max(float(np.median([b[key] for b in B])), 1.0)


def realised_cost(row: dict) -> float:
    """MPC-F's cost over the window: delay vehicle-seconds (1-s samples) + W_CF x close-following vehicle-seconds."""
    return row["delay_s"] + W_CF * row["ttc_net"]


def ref_ctrl(name: str) -> dict:
    return OPPONENTS["ctrl"][name]


def load_json(p) -> dict:
    return json.loads(Path(p).read_text())


JOB = Path("/home/catalin/work/phd/v5b1_runs/round2/test/job_6c49e7e.json")     # round 2's test job (planb.md §3.1)
V3W = ("w0u250", "w1u500", "w2u250", "w3u500", "w4u500")     # V478
CARRIED = ("p333", "z33133", "r4a1", "lr400_13_2", "lr1000_16_2", "lr1000_10_1", "lr400_16_1", "a4400_10_1", "os0_10_10", "os1_15_10",
           "os1_10_0", "copy", "3e", "3ex1", "3ex2")
PLACEBO = {"kind": "brake", "factor": 0.95, "hold": 1.0, "period": 180.0}     # V341's no-wave perturbation, the null of G1


def with_cond(arm_cfg: dict, cond: str, perturb: dict | None = None) -> dict:
    """A stored arm's config with only its perturbation changed: cond's (None for S), or perturb if given."""
    import copy
    from common1 import COND
    c = copy.deepcopy(arm_cfg)
    c.pop("measure", None)
    x = perturb if perturb is not None else COND[cond]
    env = c.setdefault("ctrl", {}).setdefault("env", {})
    env.pop("perturb", None)
    if x:
        env["perturb"] = x
    if not env:
        del c["ctrl"]["env"]
    if not c["ctrl"]:
        del c["ctrl"]
    return c


def stored_arms(job: Path = JOB) -> dict:
    """name -> config for v3w's learners and the 15 carried rules, as round 2's test ran them (X1 copies; 3ex2 from X2)."""
    arms = json.loads(job.read_text())["arms"]
    out = {n: arms[f"X1|{n}"] for n in V3W + CARRIED + ("nc",) if f"X1|{n}" in arms}
    out["3ex2"] = arms["X2|3ex2"]
    missing = set(V3W + CARRIED + ("nc",)) - set(out)
    if missing:
        raise SystemExit(f"arms missing from {job}: {sorted(missing)}")
    return out


MAX_WORKERS = 100     # planb.md decision 7, for the whole machine
RESERVE = Path.home() / ".planb_workers.json"


def git(*args) -> tuple:
    r = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return r.returncode, r.stdout


def code_state() -> dict:
    """The code a stage runs: HEAD, whether tracked files are clean, whether HEAD is detached, and a hash of the tracked diff."""
    rc, head = git("rev-parse", "HEAD")
    _, dirty = git("status", "--porcelain", "--untracked-files=no")
    det, _ = git("symbolic-ref", "-q", "HEAD")
    _, diff = git("diff", "HEAD")
    return {"commit": head.strip() if rc == 0 else None, "clean": rc == 0 and not dirty.strip(), "detached": det != 0,
            "diff_sha256": hashlib.sha256(diff.encode()).hexdigest()}


def sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def guard(out: Path, inputs: dict, cfgs: dict, strict: bool) -> dict:
    """meta.json beside a stage's rows: its inputs, a hash of every job config and the code. Resuming with other inputs, jobs or code
    is refused, so stored rows can never stand for another controller or commit (review F6, F7, F24). strict (every real run): the
    tracked tree must be clean and HEAD detached (planb.md §9, frozen run worktree)."""
    cs = code_state()
    if strict and not (cs["clean"] and cs["detached"]):
        raise SystemExit(f"run from a clean, detached worktree at the run commit (found clean={cs['clean']}, detached={cs['detached']})")
    meta = {"inputs": json.loads(json.dumps(inputs)), "jobs_sha256": sha(cfgs), "code": cs}
    out.mkdir(parents=True, exist_ok=True)
    mf = out / "meta.json"
    if mf.exists():
        old = json.loads(mf.read_text())
        if old != meta:
            diff = [k for k in ("inputs", "jobs_sha256") if old.get(k) != meta[k]] + [f"code.{k}" for k in cs if old.get("code", {}).get(k) != cs[k]]
            raise SystemExit(f"{out}: inputs, jobs or code differ from meta.json ({', '.join(diff)}); use a new folder")
    else:
        cma2.write_json(mf, meta)
    return meta


def check_workers(n: int) -> int:
    if not 1 <= n <= MAX_WORKERS:
        raise SystemExit(f"workers must be 1-{MAX_WORKERS} (planb.md decision 7)")
    return n


def reserve(n: int, path: Path = RESERVE) -> None:
    """Hold n of the machine's MAX_WORKERS until this process exits; refuse if live holders already use too many."""
    check_workers(n)
    path.touch(exist_ok=True)
    with path.open("r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            held = json.loads(f.read() or "{}")
        except json.JSONDecodeError:
            held = {}
        held = {p: w for p, w in held.items() if _alive(int(p))}
        if sum(held.values()) + n > MAX_WORKERS:
            raise SystemExit(f"{sum(held.values())} workers already held on this machine by {sorted(held)}; {n} more exceed {MAX_WORKERS}")
        held[str(os.getpid())] = n
        f.seek(0)
        f.truncate()
        f.write(json.dumps(held))
    atexit.register(_release, path)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _release(path: Path) -> None:
    with path.open("r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        held = json.loads(f.read() or "{}")
        held.pop(str(os.getpid()), None)
        f.seek(0)
        f.truncate()
        f.write(json.dumps(held))


def arm_ctrl(name: str) -> dict:
    """A stored arm's controller dict without its environment options, as plan6 runs it."""
    return {k: v for k, v in stored_arms()[name].get("ctrl", {}).items() if k != "env"}


PLANT_PATHS = ("v5b", "docs/research/conf3/common.py", "docs/research/conf3/plant_c3.json", "docs/research/round1/common1.py")


def conds_arg(text: str) -> list:
    """--conds: S, then the cells that passed S2, each once, in the protocol's order (freeze compares ordered lists)."""
    conds = text.split(",")
    cells = conds[1:]
    if conds[0] != "S" or not cells or cells != [c for c in CELLS if c in cells]:
        raise SystemExit(f"--conds is S followed by the cells that passed S2, each once, in the order {CELLS}")
    return conds


def same_plant(a: str, b: str) -> bool:
    """Whether two commits hold the same plant and condition code."""
    return a == b or git("diff", "--quiet", a, b, "--", *PLANT_PATHS)[0] == 0
