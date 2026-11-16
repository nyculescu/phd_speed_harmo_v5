"""ahead's pre-registered KILL (round_2.md, V444): permutation importance of the two look-ahead inputs. Runs inside ahead's own snapshot
(PYTHONPATH and working directory), so it imports nothing from r2/eval; the job file carries the arms and the stored validation rows.
Each traced run must equal its untraced validation row on every stored key (V386).
usage: importance2.py JOB_JSON OUT_JSON WORKERS"""
import json
import multiprocessing as mp
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

SKIP = {"name", "cfg"}
SHUFFLES, SEED = 10, 20261107


def traced(a: tuple):
    """One run with the policy's decision inputs recorded; recording copies the arrays the rule is given and changes nothing."""
    import torch
    from v5b2.freeway import train_per_cav as ct, evaluate as ps
    torch.set_num_threads(1)
    seen = []

    class Rec(ct.Greedy):
        def __call__(self, o):
            ids, lo, _, due = o
            if due.any():
                seen.append(lo[due].copy())
            return super().__call__(o)

    ct.Greedy = Rec
    row = ps.run_one(a)
    return row, (np.concatenate(seen) if seen else np.zeros((0, 0), np.float32))


def changed(path: str, X: np.ndarray, cols: tuple) -> dict:
    import torch
    from v5b2.freeway.train_per_cav import Greedy
    net = Greedy(path).net
    rng = np.random.default_rng(SEED)
    with torch.no_grad():
        base = net.logits(torch.from_numpy(X)).argmax(1).numpy()
        out = {}
        for j in cols:
            s = []
            for _ in range(SHUFFLES):
                Y = X.copy()
                Y[:, j] = Y[rng.permutation(len(Y)), j]
                s.append(float((net.logits(torch.from_numpy(Y)).argmax(1).numpy() != base).mean()))
            out[str(j)] = float(np.mean(s))
    return out


def main(job_f: str, out_f: str, workers: int) -> int:
    job = json.load(open(job_f))
    runs, cols, limit = job["runs"], tuple(job["cols"]), job["limit"]
    args = [(r["name"], r["cfg"], r["q"], r["seed"], job["rd"]) for r in runs]
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn"), max_tasks_per_child=1) as ex:
        res = list(ex.map(traced, args))
    per, bad = {}, []
    for r, (row, X) in zip(runs, res):
        st = r["stored"]
        diff = [k for k in st if k not in SKIP and json.loads(json.dumps(row)).get(k) != st[k]]
        if diff:
            bad.append({"name": r["name"], "seed": r["seed"], "differing": diff[:8]})
            continue
        per.setdefault(str(r["learner"]), []).append({"name": r["name"], "seed": r["seed"], "decisions": int(len(X)), "n_inputs": int(X.shape[1]),
                                                     **changed(r["pt"], X, cols)})
    if bad:
        json.dump({"error": "traced rows differ from the untraced rows", "bad": bad}, open(out_f, "w"), indent=1)
        print("FAIL traced rows differ", bad, flush=True)
        return 1
    learner = {i: {str(j): float(np.mean([x[str(j)] for x in v])) for j in cols} for i, v in per.items()}
    med = {str(j): float(np.median([learner[i][str(j)] for i in learner])) for j in cols}
    killed = all(med[str(j)] < limit for j in cols)
    json.dump({"cols": cols, "limit": limit, "per_run": per, "per_learner": learner, "median": med, "killed": killed}, open(out_f, "w"), indent=1)
    print("ahead importance median", med, "KILLED: look-ahead inputs not used" if killed else "not killed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2], int(sys.argv[3])))
