"""EXPLORATORY (not a claim): the R6-frozen DRL candidate on the Lead 1 21-condition mix, on the already-used gate seeds
7,170,220-239, compared with the stage-H arms of the same seeds (docs/lab/t1_meter2_h.md). Decides only whether a
pre-registered out-of-distribution test on fresh test seeds is worth proposing.

python -m vsl_lab.jobs.t1_meter2_r6ood --gate-ok
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.jobs.t1_meter2_h import COND, GATE_SEEDS, job, load
from vsl_lab.jobs.t1_meter_r6 import CAND_SHA, CANDIDATE, GRID, sha
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import run_batch


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    assert sha(CANDIDATE) == CAND_SHA
    h = json.loads((REPO_ROOT / "docs/lab/t1_meter2_h.json").read_text())
    root = RUNS_ROOT / "t1" / f"m2r6ood_{int(time.time())}"
    jobs = []
    for c, pk in COND.items():
        base = {"perturb": pk} if pk else {}
        rlk = dict(base, actuator="meter_sched", meter_grid=GRID, allow_off=False, decision_s=30, obs_stack=1)
        for s in GATE_SEEDS:
            jobs.append(job(f"ood_drl_{c}_s{s}", f"rl:{CANDIDATE}:recurrentppo", s, f"drlR6__{c}", root, rlk))
    run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    d = load(Path(h["raw"])) | load(root)
    J = {arm: {s: float(np.mean([per[c][s]["mean_time_in_system_s"] for c in COND]))
               for s in GATE_SEEDS if all(s in per.get(c, {}) for c in COND)} for arm, per in d.items()}
    rng = np.random.default_rng(7170239)

    def paired(x, y, n=10000):
        ss = sorted(set(x) & set(y))
        diff = np.array([x[s] - y[s] for s in ss])
        b = [np.median(rng.choice(diff, len(diff))) for _ in range(n)]
        return {"median_diff_s": float(np.median(diff)), "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))],
                "rel": float(np.median(diff) / np.median([y[s] for s in ss])), "n": len(ss)}
    res = {"drl_vs": {arm: paired(J["drlR6"], J[arm]) for arm in J if arm != "drlR6"},
           "mean_J": {arm: float(np.mean(list(v.values()))) for arm, v in J.items()},
           "fails_drl": sum(o.get("health") == "FAIL" for per in d["drlR6"].values() for o in per.values()), "raw": str(root)}
    fam = {}
    for f in ("none", "slow", "block", "surge"):
        cs = [c for c in COND if c.split("_")[0] == f]
        Jf = {arm: {s: float(np.mean([d[arm][c][s]["mean_time_in_system_s"] for c in cs])) for s in J[arm]}
              for arm in ("drlR6", "mpcf_old", "pooled", "evsched_old")}
        fam[f] = {arm: paired(Jf["drlR6"], Jf[arm], 5000) for arm in ("mpcf_old", "pooled", "evsched_old")}
    res["per_family"] = fam
    (REPO_ROOT / "docs/lab/t1_meter2_r6ood.json").write_text(json.dumps(res, indent=1))
    v = res["drl_vs"]
    ledger.append("T1", "M2-R6OOD", "E", "t1_meter2_r6ood", {"candidate_sha256": CAND_SHA}, f"{GATE_SEEDS[0]}-{GATE_SEEDS[-1]}",
                  len(jobs), {"FAIL": res["fails_drl"]}, {k: round(v[k]["rel"], 4) for k in ("mpcf_old", "pooled", "evsched2", "I")},
                  notes=str(root))
    print(json.dumps({k: [round(x["median_diff_s"], 1), [round(y, 1) for y in x["ci95"]], round(x["rel"], 4)] for k, x in v.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
