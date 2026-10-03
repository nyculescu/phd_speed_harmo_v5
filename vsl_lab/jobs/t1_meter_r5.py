"""R5-M head-to-head (docs/lab/t1_meter_gscan_protocol.md, Addendum D): F-class RecurrentPPO meter scheduling vs the
best non-learning controllers on test seeds 7,110,590-7,110,689 x 4 perturbation kinds at q = 1,600.

python -m vsl_lab.jobs.t1_meter_r5 --runs DIR0 DIR1 DIR2 --gate-ok
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

KINDS = {"none": None, "slow": {"kind": "slow", "dur": 300, "v_mps": 5.0}, "block": {"kind": "block", "dur": 180},
         "surge": {"kind": "surge", "dur": 300, "factor": 1.3}}
SEEDS = list(range(7110590, 7110690))
Q = 1600
GRID = ["40:6", "40:8", "20:12", "5:8"]
COMPS = ["evsched", "mpcf", "pooled", "meter106", "nc", "lookup"]


def boot_ci(diff: np.ndarray, rng, n=10000):
    b = [np.median(rng.choice(diff, len(diff))) for _ in range(n)]
    return float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs=3, required=True, help="F-class run dirs, learner seeds 0, 1, 2")
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--analyse-only", default=None, help="existing root")
    a = ap.parse_args(argv)
    lk = json.loads((REPO_ROOT / "docs/lab/t1_meter_lookup.json").read_text())["lookup"][str(Q)]
    root = Path(a.analyse_only) if a.analyse_only else RUNS_ROOT / "t1" / f"r5m_{int(time.time())}"
    if not a.analyse_only:
        jobs = []
        for k, pk in KINDS.items():
            base = {"perturb": pk} if pk else {}
            rlk = dict(base, actuator="meter_sched", meter_grid=GRID, allow_off=False, decision_s=30, obs_stack=1)
            ctrls = [("nc", "nc", base), ("meter106", "meter:10:6", base), ("pooled", lk["pooled_best"], base),
                     ("lookup", lk["per_kind"][k], base), ("evsched", "evsched:7:20:1.15", base), ("mpcf", "mpcf", base)]
            ctrls += [(f"drl{i}", f"rl:{Path(d) / 'final_model.zip'}:recurrentppo", rlk) for i, d in enumerate(a.runs)]
            for s in SEEDS:
                for lab, c, ek in ctrls:
                    jobs.append(Job(jid=f"r5m_{lab}_{k}_s{s}", argv=["vsl_lab.jobs.bn4_eval", "--ctrl", c, "--inflow", str(Q),
                                                                     "--seed", str(s), "--tag", f"{lab}__{k}", "--out-root",
                                                                     str(root), "--env-kwargs", json.dumps(ek)]))
        run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    d, fails, tele = {}, {}, {}
    for p in root.glob("*__*/*.json"):
        lab, k = p.parent.name.split("__")
        o = json.loads(p.read_text())
        d.setdefault(lab, {}).setdefault(k, {})[o["seed"]] = o["mean_time_in_system_s"]
        fails[lab] = fails.get(lab, 0) + (o.get("health") == "FAIL")
        tele[lab] = tele.get(lab, 0) + ("H-R3" in (o.get("health_codes") or []))
    J = {lab: {s: float(np.mean([per[k][s] for k in KINDS])) for s in SEEDS if all(s in per.get(k, {}) for k in KINDS)}
         for lab, per in d.items()}
    J["drl_pooled"] = {s: float(np.median([J[f"drl{i}"][s] for i in range(3)])) for s in SEEDS
                       if all(s in J.get(f"drl{i}", {}) for i in range(3))}
    rng = np.random.default_rng(7110689)
    res = {"median_J": {lab: float(np.median(list(v.values()))) for lab, v in J.items()}, "fails": fails, "teleports": tele,
           "paired": {}, "per_kind": {}}
    for drl in ("drl_pooled", "drl0", "drl1", "drl2"):
        for ref in COMPS:
            ss = sorted(set(J[drl]) & set(J[ref]))
            diff = np.array([J[drl][s] - J[ref][s] for s in ss])
            lo, hi = boot_ci(diff, rng)
            res["paired"][f"{drl}_vs_{ref}"] = {"median_diff_s": float(np.median(diff)), "ci95": [lo, hi], "n": len(ss),
                                                 "rel": float(np.median(diff) / np.median([J[ref][s] for s in ss])),
                                                 "beats": bool(np.median(diff) < 0 and hi < 0)}
    for k in KINDS:   # per-kind check for the pooled learners vs evsched and mpcf
        pk = {s: float(np.median([d[f"drl{i}"][k][s] for i in range(3)])) for s in SEEDS
              if all(s in d[f"drl{i}"][k] for i in range(3))}
        for ref in ("evsched", "mpcf"):
            ss = sorted(set(pk) & set(d[ref][k]))
            diff = np.array([pk[s] - d[ref][k][s] for s in ss])
            lo, hi = boot_ci(diff, rng, 5000)
            base = float(np.median([d[ref][k][s] for s in ss]))
            res["per_kind"][f"{k}_vs_{ref}"] = {"median_diff_s": float(np.median(diff)), "ci95": [lo, hi],
                                                "rel": float(np.median(diff) / base), "sig_worse_gt5pct": bool(lo > 0 and np.median(diff) / base > 0.05)}
    beats = {ref: res["paired"][f"drl_pooled_vs_{ref}"]["beats"] and
             sum(res["paired"][f"drl{i}_vs_{ref}"]["beats"] for i in range(3)) >= 2 for ref in COMPS}
    no_kind_harm = not any(v["sig_worse_gt5pct"] for v in res["per_kind"].values())
    fail_ok = all(fails.get(f"drl{i}", 0) / (len(SEEDS) * len(KINDS)) <= 0.05 for i in range(3))
    res["beats"] = beats
    res["CLAIM_DRL_improves_best_nonlearning"] = bool(beats["evsched"] and beats["mpcf"] and no_kind_harm and fail_ok)
    (root / "r5m.json").write_text(json.dumps(res, indent=1))
    (REPO_ROOT / "docs/lab/t1_meter_r5.json").write_text(json.dumps(res, indent=1))
    L = ["# R5-M: DRL (RecurrentPPO) scheduling the feedback meter vs tuned non-learning control", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/t1_meter_gscan_protocol.md` Addendum D · test seeds "
         f"{SEEDS[0]}-{SEEDS[-1]} × 4 kinds · q = {Q} · raw `{root}`*", "",
         f"**Pre-registered reading - DRL measurably improves on the best non-learning control (beats evsched AND MPC-F, "
         f"pooled and in ≥ 2 of 3 learner seeds; no kind significantly worse by > 5 %; FAIL share ≤ 5 %): "
         f"{'YES' if res['CLAIM_DRL_improves_best_nonlearning'] else 'NO'}**", "",
         "Median over seeds of J (mean over the 4 kinds of door-to-door time, s): " +
         ", ".join(f"{k} {v:.1f}" for k, v in sorted(res["median_J"].items(), key=lambda kv: kv[1])), "",
         "| DRL vs | pooled Δ (s) [95 % CI] | rel | seed 0 | seed 1 | seed 2 | beats (pooled & ≥ 2/3) |",
         "|---|---|---|---|---|---|---|"]
    for ref in COMPS:
        pp = res["paired"][f"drl_pooled_vs_{ref}"]
        cells = [f"{res['paired'][f'drl{i}_vs_{ref}']['median_diff_s']:+.1f} [{res['paired'][f'drl{i}_vs_{ref}']['ci95'][0]:+.1f}, "
                 f"{res['paired'][f'drl{i}_vs_{ref}']['ci95'][1]:+.1f}]" for i in range(3)]
        L.append(f"| {ref} | {pp['median_diff_s']:+.1f} [{pp['ci95'][0]:+.1f}, {pp['ci95'][1]:+.1f}] | {pp['rel']:+.1%} | "
                 + " | ".join(cells) + f" | {'yes' if beats[ref] else 'no'} |")
    L += ["", "Per kind (pooled learners):", "", "| kind vs | Δ (s) [95 % CI] | rel |", "|---|---|---|"]
    for k, v in res["per_kind"].items():
        L.append(f"| {k} | {v['median_diff_s']:+.1f} [{v['ci95'][0]:+.1f}, {v['ci95'][1]:+.1f}] | {v['rel']:+.1%} |")
    L += ["", f"FAIL runs: {fails}", f"Teleport runs: {tele}"]
    (REPO_ROOT / "docs/lab/t1_meter_r5.md").write_text("\n".join(L) + "\n")
    ledger.append("T1", "R5-M", "S", "t1_meter_r5", {"runs": a.runs}, f"{SEEDS[0]}-{SEEDS[-1]}", 100 * 4 * 9, fails,
                  {"claim": res["CLAIM_DRL_improves_best_nonlearning"], "beats": beats}, notes=str(root))
    print(json.dumps({"claim": res["CLAIM_DRL_improves_best_nonlearning"], "beats": beats, "median_J": res["median_J"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
