"""Plan B shared helpers: conditions, seeds, the run function and resumable batches (planb.md §6)."""
import json
import multiprocessing as mp
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
