"""Plan B S5 and S6 runner (planb.md §7.4, §8.3, §9). Runs s6_jobs.json's arms with the pack on, from a clean, detached worktree;
a resume is allowed only at the same jobs and commit (meta.json). Every row carries its condition, arm, learner id, seed, commit, the
SHA-256 of its controller dict and of every file it loads (v3w checkpoints, the MPC-F model). A crashed run is re-run on the same seed
and commit up to 3 attempts; a seed that crashes on every attempt goes to drops.json, and read6 drops it from every arm of that
condition. Before any run, v3w's checkpoints must equal docs/research/baseline_v4/SHA256SUMS.

usage: run6.py run --jobs DIR/s6_jobs.json --out DIR [--workers N]
       run6.py smoke --jobs DIR/s6_jobs.json --config DIR/read6_config.json --out DIR [--workers N]
  smoke (S5): every arm on 7,480,000-002 once, then each distinct controller again in its first condition, every key equal; every
  row carries the fields above, TRUCK rows log 10 capped trucks; read6 runs end to end on the smoke rows. Pass or fail only."""
import argparse
import hashlib
import json
import multiprocessing as mp
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pb  # noqa: E402

ATTEMPTS = 3
SMOKE = pb.seeds(7_480_000, 7_480_002)
SUMS = pb.ROOT / "docs/research/baseline_v4/SHA256SUMS"
SKIP = {"cfg", "m_st_file"}
FIELDS = ("cell", "arm", "learner", "seed", "commit", "ctrl_sha256", "files")


def file_sha(p: str) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def loaded_files(x) -> list:
    """Paths a controller dict loads: policy checkpoints and the MPC-F model."""
    if isinstance(x, dict):
        out = []
        for k, v in x.items():
            if k in ("pt", "model") and isinstance(v, str):
                out.append(v)
            elif k == "pts" and isinstance(v, list):
                out += [p for p in v if isinstance(p, str)]
            else:
                out += loaded_files(v)
        return out
    if isinstance(x, list):
        return [p for v in x for p in loaded_files(v)]
    return []


def check_checkpoints(arms: dict) -> dict:
    """v3w's checkpoint hashes against baseline_v4 (planb.md §7.4); returns path -> SHA-256."""
    sums = dict(line.split()[::-1] for line in SUMS.read_text().splitlines() if line.strip())
    out = {}
    for name, cfg in arms.items():
        if name.split("|", 1)[1] in pb.V3W:
            for p in loaded_files(cfg.get("ctrl", {})):
                h = file_sha(p)
                if sums.get(Path(p).name) != h:
                    raise SystemExit(f"{name}: {p} has SHA-256 {h}, baseline_v4 lists {sums.get(Path(p).name)}")
                out[p] = h
    return out


def one(a: tuple) -> dict:
    name, cfg, q, seed, rd, commit = a
    from v5b.fleet import plant_sweep as ps
    row = ps.run_one((name, cfg, q, seed, rd))
    cond, arm = name.split("|", 1)
    row.pop("cfg", None)
    row |= {"cell": cond, "arm": arm, "learner": arm if arm in pb.V3W else None, "commit": commit,
            "ctrl_sha256": pb.sha({k: v for k, v in cfg.items() if k != "measure"}), "files": {p: file_sha(p) for p in loaded_files(cfg.get("ctrl", {}))}}
    return row


def execute(arms: dict, seeds: list, out: Path, workers: int, guard_inputs: dict) -> dict:
    """Run every (arm, seed) the rows file lacks, at most ATTEMPTS times each; returns the drops {condition: [seeds]}."""
    meta = pb.guard(out, guard_inputs, arms, strict=True)
    commit = meta["code"]["commit"]
    rows_f, att_f = out / "s6_rows.jsonl", out / "attempts.json"
    done = {(r["name"], r["seed"]) for r in pb.cma2.load(rows_f)}
    att = json.loads(att_f.read_text()) if att_f.exists() else {}
    for _ in range(ATTEMPTS):
        todo = [(n, c, pb.Q, s, str(out / "rd"), commit) for n, c in arms.items() for s in seeds
                if (n, s) not in done and att.get(f"{n} {s}", 0) < ATTEMPTS]
        if not todo:
            break
        with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
            futs = {ex.submit(one, j): j for j in todo}
            for f in as_completed(futs):
                n, s = futs[f][0], futs[f][3]
                try:
                    row = f.result()
                except Exception as x:
                    att[f"{n} {s}"] = att.get(f"{n} {s}", 0) + 1
                    pb.cma2.write_json(att_f, att)
                    print("FAILED", n, s, repr(x)[:300], flush=True)
                    continue
                pb.cma2.append(rows_f, row)
                done.add((n, s))
    drops = {}
    for n in arms:
        for s in seeds:
            if (n, s) not in done:
                if att.get(f"{n} {s}", 0) < ATTEMPTS:
                    raise SystemExit(f"{n} {s} neither ran nor failed {ATTEMPTS} times; start again to continue")
                drops.setdefault(n.split("|", 1)[0], set()).add(s)
    drops = {c: sorted(v) for c, v in drops.items()}
    pb.cma2.write_json(out / "drops.json", drops)
    return drops


def smoke(jobs: dict, conf: dict, out: Path, workers: int) -> dict:
    arms = jobs["arms"]
    check_checkpoints(arms)
    first = {}
    for n, c in arms.items():     # each distinct controller once, in the first condition it appears in
        key = pb.sha({k: v for k, v in c.get("ctrl", {}).items() if k != "env"})
        first.setdefault(key, n)
    rep = {n: arms[n] for n in first.values()}
    with_st = lambda A, d: {n: {**c, "measure": str(d / "st")} for n, c in A.items()}
    da, db = execute(with_st(arms, out / "a"), SMOKE, out / "a", workers, {"smoke": True}), execute(with_st(rep, out / "b"), SMOKE, out / "b", workers, {"smoke": True})
    A = {(r["name"], r["seed"]): r for r in pb.cma2.load(out / "a" / "s6_rows.jsonl")}
    Bv = {(r["name"], r["seed"]): r for r in pb.cma2.load(out / "b" / "s6_rows.jsonl")}
    differs = {f"{k[0]} {k[1]}": d for k in Bv if (d := sorted(x for x in (set(A[k]) | set(Bv[k])) - SKIP if json.dumps(A[k].get(x)) != json.dumps(Bv[k].get(x))))}
    missing_fields = sorted({f for r in A.values() for f in FIELDS if f not in r})
    trucks = all(len(r.get("pert_log", [])) == 10 for r in A.values() if r["cell"] == "TRUCK")
    import read6
    try:
        read6.read(read6.load_rows(out / "a" / "s6_rows.jsonl", conf, SMOKE), conf, da, SMOKE)
        reader = None
    except SystemExit as x:
        reader = str(x)[:300]
    res = {"replay_differs": differs, "missing_fields": missing_fields, "truck_logs_10": trucks, "reader_error": reader, "drops": [da, db],
           "pass": not differs and not missing_fields and trucks and reader is None and not da and not db}
    pb.cma2.write_json(out / "s5.json", res)
    return res


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("step", choices=("run", "smoke"))
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--config")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=31)
    a = ap.parse_args(argv)
    jobs = pb.load_json(a.jobs)
    pb.reserve(a.workers)
    if a.step == "smoke":
        res = smoke(jobs, pb.load_json(a.config), Path(a.out), a.workers)
        print("S5", "PASS" if res["pass"] else "FAIL", {k: v for k, v in res.items() if k != "pass" and v})
        return 0 if res["pass"] else 1
    seeds = pb.seeds(*jobs["seed_range"])
    check_checkpoints(jobs["arms"])
    drops = execute(jobs["arms"], seeds, Path(a.out), a.workers, {"seed_range": jobs["seed_range"]})
    print("S6 rows done;", "crash drops:", drops or "none")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
