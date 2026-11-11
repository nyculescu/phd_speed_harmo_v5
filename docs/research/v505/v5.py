"""V505 studies M2 and EV (docs/research/protocols/v505_*.md on v5b1): seed stages, job files and the runner.

Runs reuse Plan B's runner (run6.execute): each run in its own process pool, up to 3 attempts per seed, identity fields on every
row, meta.json refusing a resume at other jobs or code, and a clean, detached tree. Only the seed check differs: every job names its
stage, and its seeds must lie inside that stage's range of v505_common.md §5.

usage: v5.py plan STAGE --out JOBS.json [--a A]      write the job file of an M2 stage
       v5.py run --jobs JOBS.json --out DIR [--workers N]
       v5.py smoke --jobs JOBS.json --out DIR [--workers N]"""
import argparse
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "planb"))
import pb  # noqa: E402
import run6  # noqa: E402

STAGES = {     # v505_common.md §5 (V508); inclusive ranges
    "m2_smoke": (7_488_000, 7_488_009), "m2_trace": (7_488_010, 7_488_019), "m2_pick": (7_488_020, 7_488_079),
    "m2_repeat": (7_488_080, 7_488_099), "m2_ident": (7_480_400, 7_480_402), "m2_verdict": (7_480_400, 7_480_639),
    "ev_smoke": (7_488_200, 7_488_219), "ev_size": (7_488_220, 7_488_239), "ev_gate": (7_488_240, 7_488_279),
    "ev_tune": (7_488_280, 7_488_339), "ev_eval": (7_488_340, 7_488_459), "ev_repeat": (7_488_460, 7_488_499),
    "ev_tune_ext": (7_488_500, 7_488_539), "ev_eval_ext": (7_488_540, 7_488_579),
    "m2_x1": (7_488_600, 7_488_759), "m2_fallback": (7_488_760, 7_488_999)}
S6_JOBS = Path("/home/catalin/work/phd/v5b1_runs/planb_s56_remote/jobs/s6_jobs.json")
M2_RULES = ("nc", "p333", "os0_10_10", "3E-C_TRUCK", "3E-D_TRUCK", "lr1000_16_2")     # M2 §6
M2_X1 = ("nc", "p333", "os0_10_10", "3e")     # 3E-T is the stored arm 3e
LADDER = (2.0, 3.0, 5.0, 10.0)     # M2 §2
TRACE_SEEDS = 2     # M2 §7: 2 seeds x {no control, p333}
RUNS_ROOT = Path("/home/catalin/work/phd/v5b1_runs/v505")


def seeds(stage: str, lo: int | None = None, hi: int | None = None) -> list:
    """The stage's seeds, or a sub-range of them; anything outside the stage's range is refused."""
    a, b = STAGES[stage]
    lo, hi = a if lo is None else lo, b if hi is None else hi
    if not (a <= lo <= hi <= b):
        raise SystemExit(f"seeds {lo}-{hi} outside stage {stage} {a}-{b} (v505_common.md §5)")
    return list(range(lo, hi + 1))


def s6_arms() -> dict:
    return json.loads(S6_JOBS.read_text())["arms"]


def m2_cfg(cfg: dict, a: float | None, measure: Path | None, **extra) -> dict:
    """A stored arm with only the V505 keys added: V-A's level (None = base plant with the M2 counts), the pack's side-file folder."""
    c = copy.deepcopy(cfg)
    c.pop("measure", None)
    if a is None:
        c["m2_counts"] = True
    else:
        c["ramp2_assertive"] = float(a)
    if measure is not None:
        c["measure"] = str(measure)
    return c | extra


def plan(stage: str, out_dir: Path, a: float | None = None) -> dict:
    """The job file of one M2 stage. Arm names are "<cell>|<arm>" for the base plant and "<cell>V<a>|<arm>" for V-A."""
    arms = s6_arms()
    st = out_dir / "st"
    learners = [f"{c}|{w}" for c in ("S", "TRUCK") for w in pb.V3W]
    rules = [f"{c}|{r}" for c in ("S", "TRUCK") for r in M2_RULES]
    if stage == "m2_ident":     # M2 §6: the stored S6 configs unchanged, so rows can be compared with S6's by value
        jobs = {n: {**{k: v for k, v in arms[n].items() if k != "measure"}, "measure": str(st)} for n in rules + learners}
    elif stage == "m2_trace":
        jobs = {f"S|{r}": {**{k: v for k, v in arms[f"S|{r}"].items() if k != "measure"}, "trace_end": True} for r in ("nc", "p333")}
        jobs |= {f"S|{r}~untraced": {k: v for k, v in arms[f"S|{r}"].items() if k != "measure"} for r in ("nc", "p333")}
    elif stage == "m2_pick":
        jobs = {f"S|{r}": m2_cfg(arms[f"S|{r}"], None, st) for r in ("nc", "p333")}
        jobs |= {f"SV{x:g}|{r}": m2_cfg(arms[f"S|{r}"], x, st) for x in LADDER for r in ("nc", "p333")}
    elif stage == "m2_verdict":
        if a is None:
            raise SystemExit("m2_verdict needs --a, the level M2's pick reading chose")
        jobs = {f"{n.split('|')[0]}V{a:g}|{n.split('|')[1]}": m2_cfg(arms[n], a, st) for n in rules + learners}
    elif stage == "m2_x1":
        if a is None:
            raise SystemExit("m2_x1 needs --a")
        x1 = {n: c for n, c in pb.stored_arms().items() if n in M2_X1 or n in pb.V3W}
        x1 = {n: pb.with_cond(c, "X1") for n, c in x1.items()}
        jobs = {f"X1|{n}": m2_cfg(c, None, st) for n, c in x1.items()} | {f"X1V{a:g}|{n}": m2_cfg(c, a, st) for n, c in x1.items()}
    elif stage == "m2_smoke":     # every distinct config of the M2 stages once (S5 practice), on the smoke seeds
        jobs = {}
        for s, x in (("m2_pick", None), ("m2_verdict", LADDER[0]), ("m2_x1", LADDER[0])):
            jobs |= plan(s, out_dir, x)["arms"]
    else:
        raise SystemExit(f"no M2 job for stage {stage}")
    lo, hi = STAGES[stage]
    if stage == "m2_trace":
        hi = lo + TRACE_SEEDS - 1
    if stage == "m2_smoke":
        hi = lo
    return {"stage": stage, "seed_range": [lo, hi], "q": pb.Q, "a": a, "arms": jobs}


def same_row(a: dict, b: dict, skip=run6.SKIP | {"commit", "name", "cfg"}) -> list:
    """Keys whose values differ between two rows, compared by value (V499: never by line text)."""
    return sorted(k for k in (set(a) | set(b)) - set(skip) if json.dumps(a.get(k), sort_keys=True) != json.dumps(b.get(k), sort_keys=True))


def smoke(jobs: dict, out: Path, workers: int) -> dict:
    """S5 practice for V505: every arm once, then each distinct config again, every value equal; V-A read back where it is on; the
    traced twin equal to the untraced one apart from its trace."""
    arms = jobs["arms"]
    sd = seeds(jobs["stage"], *jobs["seed_range"])
    run6.check_checkpoints(arms)
    run6.check_files(arms)
    first = {}
    for n, c in arms.items():
        first.setdefault(pb.sha({k: v for k, v in c.items() if k != "measure"}), n)
    rep = {n: arms[n] for n in first.values()}
    inp = {"stage": jobs["stage"], "seed_range": jobs["seed_range"], "smoke": True}
    da, db = run6.execute(arms, sd, out / "a", workers, inp), run6.execute(rep, sd, out / "b", workers, inp)
    A = {(r["name"], r["seed"]): r for r in pb.cma2.load(out / "a" / "s6_rows.jsonl")}
    B = {(r["name"], r["seed"]): r for r in pb.cma2.load(out / "b" / "s6_rows.jsonl")}
    differs = {f"{k[0]} {k[1]}": d for k in B if (d := same_row(A[k], B[k], run6.SKIP | {"commit", "m_st_file"}))}
    va = {f"{n} {s}": {k: r.get(k) for k in ("va_n_0", "va_n_1", "va_n_2", "va_bad_0", "va_bad_1", "va_bad_2")}
          for (n, s), r in A.items() if "ramp2_assertive" in arms[n]}
    va_bad = sorted(k for k, x in va.items() if any(x.get(f"va_bad_{i}") for i in range(3)) or not x.get("va_n_1"))
    counts = sorted(f"{n} {s}" for (n, s), r in A.items() if not any(k.startswith("r2_lc_") for k in r))
    res = {"replay_differs": differs, "va_not_bound": va_bad, "no_r2_counts": counts, "drops": [da, db],
           "pass": not differs and not va_bad and not counts and not da and not db}
    pb.cma2.write_json(out / "smoke.json", res)
    return res


def run(jobs: dict, out: Path, workers: int) -> dict:
    sd = seeds(jobs["stage"], *jobs["seed_range"])
    run6.check_checkpoints(jobs["arms"])
    run6.check_files(jobs["arms"])
    return run6.execute(jobs["arms"], sd, out, workers, {"stage": jobs["stage"], "seed_range": jobs["seed_range"], "a": jobs.get("a")})


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("plan", "run", "smoke"))
    ap.add_argument("stage", nargs="?")
    ap.add_argument("--jobs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--a", type=float)
    ap.add_argument("--workers", type=int, default=31)
    x = ap.parse_args(argv)
    if x.step == "plan":
        out = Path(x.out).resolve()
        j = plan(x.stage, out.parent, x.a)
        pb.cma2.write_json(out, j)
        print(j["stage"], len(j["arms"]), "arms, seeds", j["seed_range"])
        return 0
    pb.reserve(x.workers)
    if x.step == "smoke":
        res = smoke(pb.load_json(x.jobs), Path(x.out).resolve(), x.workers)
        print("smoke", "PASS" if res["pass"] else "FAIL", {k: v for k, v in res.items() if k != "pass" and v})
        return 0 if res["pass"] else 1
    drops = run(pb.load_json(x.jobs), Path(x.out).resolve(), x.workers)
    print("rows done;", "crash drops:", drops or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
