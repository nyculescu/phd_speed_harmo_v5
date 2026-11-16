"""Runs plant_sweep.run_one jobs with the code found under CODE_ROOT, so one job list can run at two commits (C1b, planb.md §7.2).
It imports nothing from Plan B. usage: run_rows.py CODE_ROOT JOBS.json OUT.jsonl WORKERS
JOBS.json: [[name, cfg, q, seed], ...]; each row is written in full, one JSON line, as it finishes. OUT must not exist: rows carry no
commit, so a resume could judge a fixed tree on rows from before the fix (review F6)."""
import json
import multiprocessing as mp
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


def init(root: str) -> None:
    sys.path.insert(0, root)


def one(a):
    from v5b2.fleet.plant_sweep import run_one
    return run_one(a)


def main(argv: list) -> int:
    root, jobs, out, workers = argv[0], json.loads(Path(argv[1]).read_text()), Path(argv[2]), int(argv[3])
    if out.exists():
        raise SystemExit(f"{out} exists; write to a new file")
    if not 1 <= workers <= 100:
        raise SystemExit("workers must be 1-100 (planb.md decision 7)")
    rd = str(out.parent / f"rd_{out.stem}")
    todo = [(n, c, q, s, rd) for n, c, q, s in jobs]
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), initializer=init, initargs=(root,), max_tasks_per_child=1) as ex, out.open("a") as w:
        futs = [ex.submit(one, j) for j in todo]
        for f in as_completed(futs):
            w.write(json.dumps(f.result()) + "\n")
            w.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
