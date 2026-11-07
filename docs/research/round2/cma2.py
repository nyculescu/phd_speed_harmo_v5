"""Round 2, 3E (protocol docs/research/protocols/round_2_prereg.md) and 3E-X (round_2.md, D4): a resumable CMA-ES search over a per-zone own-state rule on r2m3.
The result is a tuned non-learning opponent, not a candidate. Each generation is scored on a window of the tuning seeds against
os1_15_10, run on the same levels and seeds. Run with SUMO_HOME unset and OMP_NUM_THREADS=1.

usage: cma2.py --out DIR --seeds 7440700-7440739 --levels 5000,5250,5500 [--workers 31 --pop 16 --gens 15 --seeds-per-gen 8 --cond T]
       cma2.py --out DIR --final [K] [--workers 31]     after the search; K defaults to 5
Files in DIR: meta.json (settings and code identity a restart must repeat), runs.jsonl (every run's key metrics; a half-done generation
resumes from it), evals.jsonl (every evaluated configuration with its runs), best.json (rewritten each generation). A restart replays
evals.jsonl through the same deterministic CMA-ES.
--final takes seeds, levels and condition from meta.json, re-evaluates the K best distinct configurations and os1_15_10 on every seed,
and writes final.json with the pick. Its runs go to final_runs.jsonl, so a killed final resumes where it stopped.
Round 2 (round_2.md, D4) adds --ref, --start, --seed-block, --shortlist norm and --admit-cap; their defaults repeat 3E's search. The rule is
built through b_env.ZoneOwnState and plant_sweep's zone_own_state key, so the class is no longer swapped in the worker."""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
for p in (ROOT, ROOT / "docs/research/round1"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
from common1 import OPPONENTS, RULE, TRAINING_SLOWDOWNS, rule_cfg # noqa: E402
from v5b.fleet.b_env import ZONE_EDGES_3E, ZoneOwnState, zone_of_3e as zone_of # noqa: E402,F401

ZONES = ("up", "merge1", "between", "merge2", "down")
EDGES = ZONE_EDGES_3E
FIELDS = ("th", "crowd", "level", "free")
N_ZONES, N_PARAMS = len(ZONES), len(ZONES) * len(FIELDS)
TH_MAX, CROWD_MAX, N_LEVELS = 25.0, 30, 4 # speed threshold in m/s, accelerating-lane count, levels 0-3 = 1.6, 1.2, 1.0, 0.8 s
LIMIT = 100.0 / 3.6
SIGMA0, CMA_SEED = 0.25, 20261106
CAP_PCT, W_DELAY, W_COLL = 2.0, 5.0, 5.0 # delay allowed over the reference in %, loss per % above it, loss per extra collision
KEYS = ("all_delay", "ttc_net", "collisions", "passed", "teleports", "alks_b45_step", "alks_full_events", "finished_pct")
REF_NAME = "ref"
ATTEMPTS = 3
SEED_BLOCK = (7_440_700, 7_440_739) # 3E's approved tuning block; 3E-X passes its own with --seed-block
REPLAY_ATOL = 1e-9
TTC_TAG = "pooled_seconds"


def encode(params: list) -> np.ndarray:
    """Unit-cube vector from per-zone parameters; the integer levels sit at the centre of their bin."""
    u = []
    for p in params:
        u += [p["th"] / TH_MAX, p["crowd"] / CROWD_MAX, (p["level"] + 0.5) / N_LEVELS, (p["free"] + 0.5) / N_LEVELS]
    return np.clip(np.array(u, float), 0.0, 1.0)


def decode(x) -> list:
    """Per-zone parameters from a unit-cube vector: one dict per zone, in ZONES order."""
    u = np.clip(np.asarray(x, float).reshape(N_ZONES, len(FIELDS)), 0.0, 1.0)
    return [{"th": round(float(r[0]) * TH_MAX, 1), "crowd": int(round(float(r[1]) * CROWD_MAX)),
             "level": min(int(r[2] * N_LEVELS), N_LEVELS - 1), "free": min(int(r[3] * N_LEVELS), N_LEVELS - 1)} for r in u]


def start(rule: str = RULE) -> np.ndarray:
    """An own-state rule's parameters in every zone but the upstream one, which starts off (a threshold of 1 m/s)."""
    r = OPPONENTS["ctrl"][rule]["own_state"]
    on = {"th": r["th"], "crowd": r["crowd"], "level": r["level"], "free": r.get("free", 3)}
    return encode([{**on, "th": 1.0}] + [on] * (N_ZONES - 1))


def cfg_for(ctrl: dict, cond: str) -> dict:
    """T is the training slowdowns; the other conditions are confirmatory 3's."""
    return rule_cfg(ctrl, "S", TRAINING_SLOWDOWNS) if cond == "T" else rule_cfg(ctrl, cond)


def slim(row: dict) -> dict:
    return {"q": row["q"], "seed": row["seed"], **{k: float(row.get(k) or 0.0) for k in KEYS}}


def zone_ctrl(zones: list) -> dict:
    return {"zone_own_state": {"zones": zones}}


def run_cfg(a: tuple) -> dict:
    """One run in a fresh process."""
    t0 = time.time()
    from v5b.fleet import plant_sweep as ps
    return {**slim(ps.run_one(a)), "wall_s": round(time.time() - t0, 1)}


def run_jobs(jobs: list, workers: int):
    """Yield ((name, q, seed), metrics) as runs finish, one process per run. A failed run is skipped and raised at the end."""
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


def objective(runs: list, ref: list, cap: float = CAP_PCT, w_delay: float = W_DELAY, w_coll: float = W_COLL) -> dict:
    """Loss to minimise. The TTC term pools the levels in seconds: the sum over levels of the median paired difference, over the sum of
    the reference's medians, in % (negative is better), so a level weighs by its TTC. Plus w_delay per % of delay above cap (per level,
    then averaged), plus w_coll per collision beyond the reference's."""
    R = {(r["q"], r["seed"]): r for r in ref}
    per, extra, d_sum, b_sum = {}, 0.0, 0.0, 0.0
    for q in sorted({r["q"] for r in runs}):
        A = [r for r in runs if r["q"] == q]
        B = [R[(q, r["seed"])] for r in A]
        diff = lambda k: float(np.median([a[k] - b[k] for a, b in zip(A, B)]))
        base = lambda k: max(float(np.median([b[k] for b in B])), 1.0)
        ttc_d, ttc_b = diff("ttc_net"), base("ttc_net")
        per[q] = {"ttc_pct": 100.0 * ttc_d / ttc_b, "ttc_diff_s": ttc_d, "ttc_base_s": ttc_b, "delay_pct": 100.0 * diff("all_delay") / base("all_delay"),
                  "alks_full_events": diff("alks_full_events"), "alks_b45_step": diff("alks_b45_step"), "n": len(A)}
        d_sum, b_sum = d_sum + ttc_d, b_sum + ttc_b
        extra += sum(a["collisions"] for a in A) - sum(b["collisions"] for b in B)
    mean = lambda k: float(np.mean([v[k] for v in per.values()]))
    ttc_pct = 100.0 * d_sum / b_sum
    over = float(np.mean([max(0.0, v["delay_pct"] - cap) for v in per.values()]))
    extra = max(0.0, extra)
    return {"loss": ttc_pct + w_delay * over + w_coll * extra, "ttc_pct": ttc_pct, "delay_pct": mean("delay_pct"), "delay_over": over,
            "coll_extra": extra, "alks_full_events": mean("alks_full_events"), "alks_b45_step": mean("alks_b45_step"),
            "per_level": {str(q): v for q, v in per.items()}}


def window(pool: list, k: int, g: int) -> list:
    """The seeds of generation g: k consecutive tuning seeds, moving on by k each generation and wrapping. k = 0 is all of them."""
    n = len(pool)
    k = min(k, n) if k else n
    return [pool[(g * k + i) % n] for i in range(k)]


def ints(s: str) -> list:
    """'7440700-7440739,7440750' -> a list; a range includes both ends."""
    out = []
    for part in s.split(","):
        lo, _, hi = part.partition("-")
        out += list(range(int(lo), int(hi or lo) + 1))
    return out


def append(path: Path, obj: dict) -> None:
    with path.open("a") as w:
        w.write(json.dumps(obj) + "\n")
        w.flush()
        os.fsync(w.fileno())


def load(path: Path) -> list:
    """The lines of a JSONL file. A last line cut short by a kill is dropped from the file, so the next append starts on a clean line."""
    if not path.exists():
        return []
    data = path.read_bytes()
    if data and not data.endswith(b"\n"):
        data = data[:data.rfind(b"\n") + 1]
        path.write_bytes(data)
        print("dropped a partial last line of", path.name, flush=True)
    return [json.loads(x) for x in data.decode().splitlines()]


def write_json(path: Path, obj: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    os.replace(tmp, path)


def git_commit():
    """HEAD of the repository holding this file, or None when git cannot say."""
    try:
        r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def code_id() -> dict:
    """What a restart must find unchanged: the objective's form, this file's bytes and the commit."""
    return {"ttc": TTC_TAG, "cma2_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "commit": git_commit()}


def check_seeds(pool: list, block: tuple = SEED_BLOCK) -> None:
    lo, hi = block
    bad = [s for s in pool if not lo <= s <= hi]
    if bad:
        raise SystemExit(f"seeds outside the approved block {lo}-{hi}: {bad[:5]}{' ...' if len(bad) > 5 else ''}")


def fill(cfgs: dict, pairs: list, cache: dict, path: Path, rd: str, workers: int, runner) -> None:
    """Run the (configuration, level, seed) triples the cache lacks, appending each finished run to path. A broken pool is retried."""
    jobs = [(n, c, q, s, rd) for n, c in cfgs.items() for q, s in pairs]
    for attempt in range(ATTEMPTS):
        jobs = [j for j in jobs if (j[0], j[2], j[3]) not in cache]
        if not jobs:
            return
        try:
            for (n, q, s), m in runner(jobs, workers):
                cache[(n, q, s)] = {"name": n, **m}
                append(path, cache[(n, q, s)])
        except (RuntimeError, BrokenProcessPool) as x:
            print(f"attempt {attempt + 1} of {ATTEMPTS}: {x}", flush=True)
    missing = [j for j in jobs if (j[0], j[2], j[3]) not in cache]
    if missing:
        raise SystemExit(f"{len(missing)} runs still missing after {ATTEMPTS} attempts; start again to continue")


def rows_of(cache: dict, name: str, pairs: list) -> list:
    return [{k: v for k, v in cache[(name, q, s)].items() if k != "name"} for q, s in pairs]


def new_es(pop: int, sigma: float, seed: int, x0=None):
    import cma
    rng = np.random.default_rng(seed) # private stream: the replay on restart must not depend on other users of numpy's global one
    return cma.CMAEvolutionStrategy(start() if x0 is None else x0, sigma, {"popsize": pop, "bounds": [0, 1], "verbose": -9, "verb_log": 0, "CMA_diagonal": True,
                                                     "randn": lambda *s: rng.standard_normal(s)})


def brief(r: dict) -> dict:
    return {k: r[k] for k in ("gen", "idx", "loss", "parts", "params", "x", "seeds")}


def best_json(recs: list, es, a) -> dict:
    gens = {}
    for r in recs:
        gens.setdefault(r["gen"], []).append(r)
    return {"generations": len(gens), "evaluated": len(recs), "cond": a.cond, "levels": ints(a.levels), "pop": a.pop,
            # best_seen compares losses over different seed windows, so it is optimistic: the pick is made on validation seeds
            "best_seen": brief(min(recs, key=lambda r: r["loss"])),
            "latest_mean": {"params": decode(es.result.xfavorite), "x": [float(v) for v in es.result.xfavorite], "sigma": float(es.sigma)},
            "history": [{"gen": g, "seeds": rs[0]["seeds"], "best": min(r["loss"] for r in rs), "median": float(np.median([r["loss"] for r in rs]))}
                        for g, rs in sorted(gens.items())]}


def search(a, jobs_runner=run_jobs) -> None:
    out = Path(a.out)
    pool, levels = ints(a.seeds), [float(x) for x in a.levels.split(",")]
    check_seeds(pool, block_of(a.seed_block))
    out.mkdir(parents=True, exist_ok=True)
    x0 = start(a.start)
    meta = {"pop": a.pop, "seeds": a.seeds, "seeds_per_gen": a.seeds_per_gen, "levels": a.levels, "cond": a.cond, "sigma": a.sigma, "cma_seed": a.cma_seed,
            "cap": a.cap, "w_delay": a.w_delay, "w_coll": a.w_coll, "start": [float(v) for v in x0], "edges": list(EDGES), **code_id(),
            "ref": a.ref, "start_rule": a.start, "seed_block": a.seed_block, "shortlist": a.shortlist, "admit_cap": a.admit_cap}
    mf = out / "meta.json"
    if mf.exists():
        old = json.loads(mf.read_text())
        if old != meta:
            raise SystemExit("settings differ from meta.json: " + ", ".join(k for k in meta if old.get(k) != meta[k]))
    else:
        write_json(mf, meta)
    cache = {(r["name"], r["q"], r["seed"]): r for r in load(out / "runs.jsonl")}
    recs = load(out / "evals.jsonl")
    done = {(r["gen"], r["idx"]): r for r in recs}
    es = new_es(a.pop, a.sigma, a.cma_seed, x0)
    ref_cfg = cfg_for(OPPONENTS["ctrl"][a.ref], a.cond)
    t0 = time.time()
    for g in range(a.gens):
        xs = es.ask()
        seeds = window(pool, a.seeds_per_gen, g)
        for i in range(a.pop):
            if (g, i) in done:
                stored = np.array(done[(g, i)]["x"])
                if stored.shape != xs[i].shape or not np.allclose(stored, xs[i], rtol=0.0, atol=REPLAY_ATOL):
                    raise SystemExit(f"generation {g} individual {i}: the stored vector differs from the one CMA-ES asks for by more than "
                                     f"{REPLAY_ATOL}; the search cannot be replayed")
                xs[i] = stored # CMA must learn from the vectors that were evaluated
        todo = [i for i in range(a.pop) if (g, i) not in done]
        if todo:
            pairs = [(q, s) for q in levels for s in seeds]
            names = {i: f"g{g:03d}i{i:02d}" for i in todo}
            cfgs = {REF_NAME: ref_cfg} | {names[i]: cfg_for(zone_ctrl(decode(xs[i])), a.cond) for i in todo}
            fill(cfgs, pairs, cache, out / "runs.jsonl", str(out / "rd"), a.workers, jobs_runner)
            ref = rows_of(cache, REF_NAME, pairs)
            for i in todo:
                runs = rows_of(cache, names[i], pairs)
                o = objective(runs, ref, a.cap, a.w_delay, a.w_coll)
                r = {"gen": g, "idx": i, "name": names[i], "x": [float(v) for v in xs[i]], "params": decode(xs[i]), "seeds": seeds, "levels": levels,
                     "cond": a.cond, "loss": o.pop("loss"), "parts": o, "runs": runs}
                append(out / "evals.jsonl", r)
                recs.append(r)
                done[(g, i)] = r
        es.tell(xs, [done[(g, i)]["loss"] for i in range(a.pop)])
        write_json(out / "best.json", best_json(recs, es, a))
        gen = [done[(g, i)]["loss"] for i in range(a.pop)]
        wall = [r["wall_s"] for r in cache.values() if "wall_s" in r]
        print(f"gen {g} seeds {seeds[0]}..{seeds[-1]} ({len(seeds)}) best {min(gen):.2f} median {float(np.median(gen)):.2f} sigma {es.sigma:.3f} "
              f"median run {float(np.median(wall)) if wall else 0.0:.0f} s, {time.time() - t0:.0f} s elapsed", flush=True)


def shortlist(recs: list, k: int, mode: str = "raw") -> list:
    """The k best evaluated configurations by search loss, one per distinct decoded parameter set. Those losses come from different
    seed windows, so they only shortlist. mode "norm" ranks each loss minus its generation's median, because the window moves the median."""
    med = {g: float(np.median([r["loss"] for r in recs if r["gen"] == g])) for g in {r["gen"] for r in recs}}
    key = (lambda r: (r["loss"], r["gen"], r["idx"])) if mode == "raw" else (lambda r: (r["loss"] - med[r["gen"]], r["gen"], r["idx"]))
    seen, out = set(), []
    for r in sorted(recs, key=key):
        key = json.dumps(r["params"], sort_keys=True)
        if key not in seen:
            seen.add(key)
            out.append(r)
        if len(out) == k:
            break
    return out


def convergence(recs: list, n: int = 10) -> dict:
    """Median loss of the last n generations against the n before; with 16 of 40 seeds per generation the windows repeat every 5."""
    G = max(r["gen"] for r in recs) + 1
    last = [r["loss"] for r in recs if G - n <= r["gen"] < G]
    prev = [r["loss"] for r in recs if G - 2 * n <= r["gen"] < G - n]
    return {"generations": G, "last": float(np.median(last)) if last else None, "previous": float(np.median(prev)) if prev else None,
            "still_falling": bool(last and prev and np.median(last) < np.median(prev))}


def block_of(s: str) -> tuple:
    lo, _, hi = s.partition("-")
    return int(lo), int(hi)


def level_stats(runs: list) -> dict:
    return {str(q): {"ttc_net": float(np.median([r["ttc_net"] for r in runs if r["q"] == q])),
                     "all_delay": float(np.median([r["all_delay"] for r in runs if r["q"] == q])),
                     "collisions": float(sum(r["collisions"] for r in runs if r["q"] == q))} for q in sorted({r["q"] for r in runs})}


def final(a, jobs_runner=run_jobs) -> None:
    """Re-evaluate the shortlist and the reference on every tuning seed, then pick the lowest pooled loss among the shortlisted configurations."""
    out = Path(a.out)
    mf = out / "meta.json"
    if not mf.exists():
        raise SystemExit("no meta.json in --out: run the search first")
    meta = json.loads(mf.read_text())
    now = code_id()
    if any(meta.get(k) != v for k, v in now.items()):
        raise SystemExit("code differs from meta.json: " + ", ".join(k for k in now if meta.get(k) != now[k]))
    for k in ("seeds", "levels", "cond"):
        if getattr(a, k, None) is not None and getattr(a, k) != meta[k]:
            raise SystemExit(f"--{k} {getattr(a, k)} differs from meta.json ({meta[k]}); --final takes it from there")
    pool, levels, cond = ints(meta["seeds"]), [float(x) for x in meta["levels"].split(",")], meta["cond"]
    ref_name, mode, admit = meta.get("ref", RULE), meta.get("shortlist", "raw"), meta.get("admit_cap")
    check_seeds(pool, block_of(meta.get("seed_block", f"{SEED_BLOCK[0]}-{SEED_BLOCK[1]}")))
    recs = load(out / "evals.jsonl")
    if not recs:
        raise SystemExit("evals.jsonl is empty: run the search first")
    cands = shortlist(recs, a.final, mode)
    if mode == "norm":     # round 2: the final CMA mean joins the shortlist
        b = json.loads((out / "best.json").read_text())["latest_mean"]
        if all(json.dumps(b["params"], sort_keys=True) != json.dumps(r["params"], sort_keys=True) for r in cands):
            cands.append({"name": "mean", "gen": -1, "idx": -1, "params": b["params"], "x": b["x"], "loss": float("nan")})
    pairs = [(q, s) for q in levels for s in pool]
    cache = {(r["name"], r["q"], r["seed"]): r for r in load(out / "final_runs.jsonl")}
    cfgs = {REF_NAME: cfg_for(OPPONENTS["ctrl"][ref_name], cond)} | {r["name"]: cfg_for(zone_ctrl(r["params"]), cond) for r in cands}
    fill(cfgs, pairs, cache, out / "final_runs.jsonl", str(out / "rd_final"), a.workers, jobs_runner)
    ref = rows_of(cache, REF_NAME, pairs)
    rows = []
    for r in cands:
        o = objective(rows_of(cache, r["name"], pairs), ref, meta["cap"], meta["w_delay"], meta["w_coll"])
        rows.append({"name": r["name"], "gen": r["gen"], "idx": r["idx"], "params": r["params"], "x": r["x"], "search_loss": r["loss"],
                     "loss": o.pop("loss"), **o})
    rows.sort(key=lambda r: (r["loss"], r["gen"], r["idx"]))
    ref_coll = sum(x["collisions"] for x in ref)
    for r in rows:     # round 2: admissible as confirmatory 3's step 1, on all tuning seeds, against the reference
        coll = sum(x["collisions"] for x in rows_of(cache, r["name"], pairs))
        r["admissible"] = admit is None or (max(v["delay_pct"] for v in r["per_level"].values()) <= admit and coll <= ref_coll + 1)
    ok = [r for r in rows if r["admissible"]]
    pick = ({k: ok[0][k] for k in ("name", "gen", "idx", "params", "x", "loss")} | {"beats_reference": ok[0]["loss"] < 0.0}) if ok else None
    write_json(out / "final.json", {"k": a.final, "cond": cond, "levels": levels, "seeds": meta["seeds"], "n_seeds": len(pool), "code": now,
                                    "reference": {"name": ref_name, "ctrl": OPPONENTS["ctrl"][ref_name], "per_level": level_stats(ref)},
                                    "candidates": rows, "pick": pick, "convergence": convergence(recs)})
    for r in rows:
        print(f"{r['name']} search loss {r['search_loss']:.2f} final loss {r['loss']:.2f} ttc {r['ttc_pct']:.2f} % delay {r['delay_pct']:.2f} %", flush=True)
    if pick is None:
        print("no configuration within the cap", flush=True)
    else:
        print("pick", pick["name"], f"loss {pick['loss']:.2f}", "beats the reference" if pick["beats_reference"] else "does not beat the reference", flush=True)


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--pop", type=int, default=16)
    ap.add_argument("--gens", type=int, default=15, help="total generations; a restart continues up to this number")
    ap.add_argument("--seeds", help="the tuning seeds, e.g. 7440700-7440739 or a comma list; required for the search")
    ap.add_argument("--seeds-per-gen", type=int, default=0, help="seeds in each generation's window, taken in turn from --seeds; 0 is all")
    ap.add_argument("--levels", help="demand levels in veh/h, comma separated; required for the search")
    ap.add_argument("--cond", choices=("T", "S", "X1", "X2", "H1", "H2"), help="default T, the training slowdowns")
    ap.add_argument("--sigma", type=float, default=SIGMA0)
    ap.add_argument("--cma-seed", type=int, default=CMA_SEED)
    ap.add_argument("--cap", type=float, default=CAP_PCT, help="delay allowed over the reference, in %%")
    ap.add_argument("--ref", default=RULE, choices=sorted(OPPONENTS["ctrl"]), help="reference rule of the objective (round 2's 3E-X: p333)")
    ap.add_argument("--start", default=RULE, help="own-state rule whose values start zones 1-4")
    ap.add_argument("--seed-block", default=f"{SEED_BLOCK[0]}-{SEED_BLOCK[1]}", help="the approved tuning block, LO-HI")
    ap.add_argument("--shortlist", default="raw", choices=("raw", "norm"))
    ap.add_argument("--admit-cap", type=float, default=None, help="pick only configurations within this delay %% of the reference, collisions +1")
    ap.add_argument("--w-delay", type=float, default=W_DELAY)
    ap.add_argument("--w-coll", type=float, default=W_COLL)
    ap.add_argument("--final", type=int, nargs="?", const=5, metavar="K",
                    help="after the search: re-evaluate the K best distinct configurations (default 5) and the reference on all seeds, write final.json")
    a = ap.parse_args(argv)
    if a.final is not None and a.final < 1:
        ap.error("--final needs K >= 1")
    if a.final is None and not (a.seeds and a.levels):
        ap.error("--seeds and --levels are required for the search")
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143)) # unwinds the pool before the process ends
    if a.final is not None:
        final(a)
    else:
        a.cond = a.cond or "T"
        search(a)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
