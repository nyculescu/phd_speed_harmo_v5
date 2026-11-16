"""Per-seed rows for run 4b: policies and fixed zone arms, with and without the 0.5-s delay, on the validation seeds."""
import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from v5b.fleet import b_train as bt

R = Path("/home/catalin/work/phd/v5b1_runs/b_train/run4b")
OUT = R / "perseed"


def job(a):
    name, asl, q, seed, model = a
    kw = {**bt.CFG[6]["env"], **({"alks_asl": asl} if asl else {})}
    row = bt._eval_one((model, 0.5, q, seed, str(OUT / "rd"), kw, True))
    row.update(name=name, asl=asl)
    return row


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    seeds = bt.CFG[6]["seeds"][:20]
    arms = [(f"L{i}", str(R / f"L{i}_final")) for i in range(3)]
    arms += [("".join(map(str, t)), t) for t in ((0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3))]
    jobs = [(n, asl, q, s, m) for n, m in arms for asl in (None, 0.5) for q in bt.CFG[6]["levels"] for s in seeds]
    print(len(jobs), "jobs", flush=True)
    with ProcessPoolExecutor(27, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex, open(OUT / "rows.jsonl", "w") as f:
        for i, fut in enumerate(as_completed([ex.submit(job, j) for j in jobs])):
            f.write(json.dumps(fut.result()) + "\n")
            f.flush()
    print("done", flush=True)
