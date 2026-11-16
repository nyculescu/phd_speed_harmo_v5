"""Plan B (planb.md §3.3, V480): the per-cell CMA-ES searches 3E-C (close-following) and 3E-D (delay) over the per-zone own-state
rule, against p333 in the cell, at 5,300 veh/h. The settings are fixed here, not on the command line, so a search cannot drift
from the protocol. Every search runs 100 generations with no data-dependent stop; at generations 20, 30, ..., 100 the 5 best
distinct configurations since the last check (loss minus the generation median) and the current CMA mean are re-run on the 40
check seeds, and the incumbent is the admissible configuration with the lowest check loss so far. The plateau label compares the
incumbent's check loss at 60 and at 100. Run with SUMO_HOME unset and OMP_NUM_THREADS=1.

usage: cmab.py --out DIR --cell SURGE|TRUCK --objective ttc|delay --repick REPICK.json [--workers N]
  The start comes from S3a's repick.json, never from the command line: 3E-C starts at the cell's own-state re-pick, encoded as
  round 2's start (cma2.start): the upstream zone off (th 1 m/s), the other four zones equal to the re-pick (free 3 unless given);
  if S3a picked no admissible own-state rule in the cell, its lowest close-following own-state rule (V482).
  Zone merge1 (-100 to 594.72 m) cannot hold OwnState's x_min of 500 m exactly; disclosed. 3E-D starts at p333 (th 0, free 3).
Files in DIR: meta.json, runs.jsonl, evals.jsonl, best.json (as cma2.py), check_runs.jsonl, checks.jsonl, incumbent.json and,
at the end, pick.json. A file STOP_CEILING in DIR (the budget ceiling, planb.md §9) ends the search at its next check with the
label "stopped at the budget ceiling"."""
import argparse
import hashlib
import json
import multiprocessing as mp
import signal
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
for p in (ROOT, ROOT / "analysis/round1", ROOT / "analysis/round2"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import cma2  # noqa: E402
from common1 import COND, OPPONENTS, rule_cfg  # noqa: E402

sys.path.insert(0, str(HERE))
import pb  # noqa: E402

CELLS = ("SURGE", "TRUCK")
Q = 5300.0
POOL = list(range(7_480_150, 7_480_190))
CHECK = list(range(7_480_190, 7_480_230))
POP, SIGMA, SEEDS_PER_GEN, GENS = 24, 0.25, 16, 100
CHECK_AT = tuple(range(20, GENS + 1, 10))
K_CHECK = 5
CMA_SEED = {"ttc": 20261108, "delay": 20261118}     # plus the cell's index
LOSS = {"ttc": {"cap": 1.0, "w_delay": 10.0, "w_coll": 5.0}, "delay": {"w_coll": 5.0}}
ADMIT_DELAY_PCT = 2.0     # 3E-C: delay at most +2 % over p333 (point) on the check seeds
FULL_TOL = (0.05, 5.0)     # 3E-D: moving full-emergency events at most p333's + max(5 %, 5), summed over the check seeds
PLATEAU = {"ttc": 1.0, "delay": 0.5}     # loss points between the incumbent's check loss at 60 and at 100
PLATEAU_FROM = 60
REF = "p333"
REF_NAME = "ref"
KEYS = cma2.KEYS + ("alks_full_moving",)
P333_ZONES = [{"th": 0.0, "crowd": 0, "level": 0, "free": 3}] * cma2.N_ZONES
LABEL_OK, LABEL_NOT, LABEL_CEIL = "met the plateau criterion", "not converged at 100 generations", "stopped at the budget ceiling"


def slim(row: dict) -> dict:
    return {"q": row["q"], "seed": row["seed"], **{k: float(row.get(k) or 0.0) for k in KEYS}}


def run_cfg(a: tuple) -> dict:
    t0 = time.time()
    from v5b2.freeway import evaluate as ps
    return {**slim(ps.run_one(a)), "wall_s": round(time.time() - t0, 1)}


def run_jobs(jobs: list, workers: int):
    """As cma2.run_jobs, with this file's keys."""
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


def start_vector(spec) -> np.ndarray:
    if spec == "p333":
        return cma2.encode(P333_ZONES)
    if isinstance(spec, dict) and set(spec) <= {"level", "th", "crowd", "free"}:
        z = {"th": float(spec["th"]), "crowd": int(spec.get("crowd", 0)), "level": int(spec["level"]), "free": int(spec.get("free", 3))}
        return cma2.encode([{**z, "th": 1.0}] + [z] * (cma2.N_ZONES - 1))
    raise SystemExit(f"the start must be p333 or an own-state dict, not {spec!r}")


def start_from(repick: dict, cell: str, objective: str):
    """The protocol's start (planb.md §3.3) from S3a's record."""
    if objective == "delay":
        return "p333"
    st = repick.get("own_state_repick", {}).get(cell)
    if st is None:     # V482: the cell's lowest close-following own-state rule, admission ignored; disclosed
        st = repick.get("own_state_fallback", {}).get(cell)
        if st is None:
            raise SystemExit(f"repick.json has neither an own-state re-pick nor its V482 fallback for {cell}")
        print(f"3E-C start in {cell}: no admissible own-state re-pick, V482 fallback {st} (disclosed)", flush=True)
    return st


def delay_objective(runs: list, ref: list, w_coll: float) -> dict:
    """3E-D's loss: the median paired delay change against p333 in % (negative is better), plus w_coll per collision beyond p333's."""
    R = {(r["q"], r["seed"]): r for r in ref}
    B = [R[(r["q"], r["seed"])] for r in runs]
    d = float(np.median([a["all_delay"] - b["all_delay"] for a, b in zip(runs, B)]))
    base = max(float(np.median([b["all_delay"] for b in B])), 1.0)
    extra = max(0.0, sum(a["collisions"] for a in runs) - sum(b["collisions"] for b in B))
    ttc_d = float(np.median([a["ttc_net"] - b["ttc_net"] for a, b in zip(runs, B)]))
    ttc_b = max(float(np.median([b["ttc_net"] for b in B])), 1.0)
    return {"loss": 100.0 * d / base + w_coll * extra, "delay_pct": 100.0 * d / base, "ttc_pct": 100.0 * ttc_d / ttc_b, "coll_extra": extra}


def loss_of(objective: str, runs: list, ref: list) -> dict:
    if objective == "ttc":
        return cma2.objective(runs, ref, **LOSS["ttc"])
    return delay_objective(runs, ref, **LOSS["delay"])


def admissible(objective: str, parts: dict, runs: list, ref: list) -> bool:
    coll_ok = sum(r["collisions"] for r in runs) <= sum(r["collisions"] for r in ref) + 1
    if objective == "ttc":
        return coll_ok and parts["delay_pct"] <= ADMIT_DELAY_PCT
    full, full_ref = sum(r["alks_full_moving"] for r in runs), sum(r["alks_full_moving"] for r in ref)
    return coll_ok and full <= full_ref + max(FULL_TOL[0] * full_ref, FULL_TOL[1])


def label(checks: list) -> str:
    """The plateau label from the stored checks (each holds the incumbent after it)."""
    if checks and checks[-1].get("ceiling"):
        return LABEL_CEIL
    at = {c["gen"]: c["incumbent"] for c in checks}
    a, b = at.get(PLATEAU_FROM), at.get(GENS)
    if not a or not b:
        return LABEL_NOT
    return LABEL_OK if a["check_loss"] - b["check_loss"] < PLATEAU[checks[0]["objective"]] else LABEL_NOT


def code_id(strict: bool = False) -> dict:
    """The search's code: both files' hashes and the tree's state (commit, clean, detached, tracked diff), so an uncommitted plant
    edit changes meta.json. strict (every real search): a clean, detached tree (planb.md §9)."""
    cs = pb.code_state()
    if strict and not (cs["clean"] and cs["detached"]):
        raise SystemExit(f"run from a clean, detached worktree at the run commit (found clean={cs['clean']}, detached={cs['detached']})")
    return {"cmab_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "cma2_sha256": hashlib.sha256(Path(cma2.__file__).read_bytes()).hexdigest(), "commit": cs["commit"], "clean": cs["clean"],
            "detached": cs["detached"], "diff_sha256": cs["diff_sha256"]}


def check(g: int, recs: list, es, last_g: int, cache: dict, out: Path, a, cfg, runner, prior: dict | None, ceiling: bool) -> dict:
    """Re-run the shortlist since the last check and the CMA mean on the check seeds; update the incumbent."""
    since = [r for r in recs if last_g <= r["gen"] < g]
    cands = cma2.shortlist(since, K_CHECK, "norm")
    mean = {"name": f"mean_g{g:03d}", "params": cma2.decode(es.result.xfavorite), "x": [float(v) for v in es.result.xfavorite]}
    if all(json.dumps(mean["params"], sort_keys=True) != json.dumps(r["params"], sort_keys=True) for r in cands):
        cands = cands + [mean]
    pairs = [(Q, s) for s in CHECK]
    cfgs = {REF_NAME: cfg(OPPONENTS["ctrl"][REF])} | {f"c_{r['name']}": cfg(cma2.zone_ctrl(r["params"])) for r in cands}
    cma2.fill(cfgs, pairs, cache, out / "check_runs.jsonl", str(out / "rd_check"), a.workers, runner)
    ref = cma2.rows_of(cache, REF_NAME, pairs)
    rows = []
    for r in cands:
        runs = cma2.rows_of(cache, f"c_{r['name']}", pairs)
        parts = loss_of(a.objective, runs, ref)
        rows.append({"name": r["name"], "params": r["params"], "x": r["x"], "check_loss": parts.pop("loss"), "parts": parts,
                     "admissible": admissible(a.objective, parts, runs, ref)})
    inc = prior
    for r in sorted((r for r in rows if r["admissible"]), key=lambda r: r["check_loss"]):
        if inc is None or r["check_loss"] < inc["check_loss"]:
            inc = {**r, "found_at": g}
        break
    c = {"gen": g, "objective": a.objective, "candidates": rows, "incumbent": inc, "ceiling": ceiling}
    cma2.append(out / "checks.jsonl", c)
    cma2.write_json(out / "incumbent.json", {"gen": g, "incumbent": inc})
    return c


def search(a, runner=run_jobs) -> None:
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    k = CELLS.index(a.cell)
    x0 = start_vector(a.start)
    cfg = lambda ctrl: rule_cfg(ctrl, a.cell)
    meta = {"cell": a.cell, "objective": a.objective, "q": Q, "pool": [POOL[0], POOL[-1]], "check": [CHECK[0], CHECK[-1]], "pop": POP,
            "sigma": SIGMA, "seeds_per_gen": SEEDS_PER_GEN, "gens": GENS, "check_at": list(CHECK_AT), "k_check": K_CHECK,
            "cma_seed": CMA_SEED[a.objective] + k, "loss": LOSS[a.objective], "start": a.start, "x0": [float(v) for v in x0], "ref": REF,
            "ref_cfg": cfg(OPPONENTS["ctrl"][REF]), "cond": COND[a.cell], "edges": list(cma2.EDGES), **code_id(runner is run_jobs)}
    mf = out / "meta.json"
    if mf.exists():
        old = json.loads(mf.read_text())
        if old != meta:
            raise SystemExit("settings or code differ from meta.json: " + ", ".join(x for x in meta if old.get(x) != meta[x]))
    else:
        cma2.write_json(mf, meta)
    cache = {(r["name"], r["q"], r["seed"]): r for r in cma2.load(out / "runs.jsonl")}
    ccache = {(r["name"], r["q"], r["seed"]): r for r in cma2.load(out / "check_runs.jsonl")}
    recs = cma2.load(out / "evals.jsonl")
    checks = cma2.load(out / "checks.jsonl")
    done = {(r["gen"], r["idx"]): r for r in recs}
    checked = {c["gen"]: c for c in checks}
    es = cma2.new_es(POP, SIGMA, meta["cma_seed"], x0)
    ref_cfg = cfg(OPPONENTS["ctrl"][REF])
    inc, last_g, t0 = None, 0, time.time()
    for g in range(GENS):
        xs = es.ask()
        seeds = cma2.window(POOL, SEEDS_PER_GEN, g)
        for i in range(POP):
            if (g, i) in done:
                stored = np.array(done[(g, i)]["x"])
                if stored.shape != xs[i].shape or not np.allclose(stored, xs[i], rtol=0.0, atol=cma2.REPLAY_ATOL):
                    raise SystemExit(f"generation {g} individual {i}: the stored vector differs from CMA-ES's; the search cannot be replayed")
                xs[i] = stored
        todo = [i for i in range(POP) if (g, i) not in done]
        if todo:
            pairs = [(Q, s) for s in seeds]
            names = {i: f"g{g:03d}i{i:02d}" for i in todo}
            cfgs = {REF_NAME: ref_cfg} | {names[i]: cfg(cma2.zone_ctrl(cma2.decode(xs[i]))) for i in todo}
            cma2.fill(cfgs, pairs, cache, out / "runs.jsonl", str(out / "rd"), a.workers, runner)
            ref = cma2.rows_of(cache, REF_NAME, pairs)
            for i in todo:
                runs = cma2.rows_of(cache, names[i], pairs)
                o = loss_of(a.objective, runs, ref)
                r = {"gen": g, "idx": i, "name": names[i], "x": [float(v) for v in xs[i]], "params": cma2.decode(xs[i]), "seeds": seeds,
                     "cell": a.cell, "loss": o.pop("loss"), "parts": o, "runs": runs}
                cma2.append(out / "evals.jsonl", r)
                recs.append(r)
                done[(g, i)] = r
        es.tell(xs, [done[(g, i)]["loss"] for i in range(POP)])
        gen = [done[(g, i)]["loss"] for i in range(POP)]
        print(f"gen {g} best {min(gen):.2f} median {float(np.median(gen)):.2f} sigma {es.sigma:.3f} {time.time() - t0:.0f} s", flush=True)
        n = g + 1
        if n in CHECK_AT:
            ceiling = n < GENS and (out / "STOP_CEILING").exists() and n not in checked     # a search that reached 100 is not a ceiling stop
            c = checked.get(n) or check(n, recs, es, last_g, ccache, out, a, cfg, runner, inc, ceiling)
            checked[n] = c
            inc, last_g = c["incumbent"], n
            if c.get("ceiling"):
                break
    checks = [checked[g] for g in sorted(checked)]
    pick = {"cell": a.cell, "objective": a.objective, "label": label(checks), "generations": max(c["gen"] for c in checks),
            "incumbent": checks[-1]["incumbent"], "code": code_id()}
    cma2.write_json(out / "pick.json", pick)
    print("pick", pick["label"], (pick["incumbent"] or {}).get("name"), flush=True)


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--cell", required=True, choices=CELLS)
    ap.add_argument("--objective", required=True, choices=("ttc", "delay"))
    ap.add_argument("--repick", required=True, help="S3a's repick.json; the start is read from it")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args(argv)
    a.start = start_from(json.loads(Path(a.repick).read_text()), a.cell, a.objective)
    a.out = str(Path(a.out).resolve())
    pb.reserve(a.workers)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    search(a)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
