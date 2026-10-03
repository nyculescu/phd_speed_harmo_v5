"""P-M screening (docs/lab/t1_meter_gscan_protocol.md, Addendum B). python -m vsl_lab.jobs.t1_meter_pm --run-dir DIR --gate-ok"""
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
SEEDS = list(range(7110330, 7110340))
Q = 1600
GRID = ["40:6", "40:8", "20:12", "5:8"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--seeds", default=None)
    ap.add_argument("--tag", default="pm_screen")
    ap.add_argument("--obs-stack", type=int, default=1)
    ap.add_argument("--algo", default="ppo")
    a = ap.parse_args(argv)
    seeds = SEEDS if not a.seeds else list(range(int(a.seeds.split("-")[0]), int(a.seeds.split("-")[1]) + 1))
    run_dir = Path(a.run_dir)
    root = RUNS_ROOT / "t1" / f"{a.tag}_{int(time.time())}"
    lk = json.loads((REPO_ROOT / "docs/lab/t1_meter_lookup.json").read_text())["lookup"][str(Q)]
    jobs = []
    for k, pk in KINDS.items():
        base = {"perturb": pk} if pk else {}
        rlk = dict(base, actuator="meter_sched", meter_grid=GRID, allow_off=False, decision_s=30, obs_stack=a.obs_stack)
        ctrls = [("nc", "nc", base), ("meter106", "meter:10:6", base), ("pooled", lk["pooled_best"], base),
                 ("lookup", lk["per_kind"][k], base), ("evsched", "evsched:7:20:1.15", base)]
        for lab, mp in (("drl_final", run_dir / "final_model.zip"), ("drl_best", run_dir / "best_val_model.zip")):
            if mp.exists():
                ctrls.append((lab, f"rl:{mp}:{a.algo}", rlk))
        for s in seeds:
            for lab, c, ek in ctrls:
                jobs.append(Job(jid=f"pm_{lab}_{k}_s{s}", argv=["vsl_lab.jobs.bn4_eval", "--ctrl", c, "--inflow", str(Q),
                                                              "--seed", str(s), "--tag", f"{lab}__{k}", "--out-root", str(root),
                                                              "--env-kwargs", json.dumps(ek)]))
    run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    d, fails = {}, {}
    for p in root.glob("*__*/*.json"):
        lab, k = p.parent.name.split("__")
        o = json.loads(p.read_text())
        d.setdefault(lab, {}).setdefault(o["seed"], {})[k] = o["mean_time_in_system_s"]
        fails[lab] = fails.get(lab, 0) + (o.get("health") == "FAIL")
    J = {lab: {s: float(np.mean(list(v.values()))) for s, v in per.items() if len(v) == len(KINDS)} for lab, per in d.items()}
    rng = np.random.default_rng(7110339)
    res = {"median_J": {lab: float(np.median(list(v.values()))) for lab, v in J.items()}, "fails": fails, "paired": {}}
    for lab in ("drl_final", "drl_best"):
        if lab not in J:
            continue
        for ref in ("evsched", "pooled", "lookup", "meter106", "nc"):
            ss = sorted(set(J[lab]) & set(J[ref]))
            diff = np.array([J[lab][s] - J[ref][s] for s in ss])
            boots = [np.median(rng.choice(diff, len(diff))) for _ in range(10000)]
            res["paired"][f"{lab}_vs_{ref}"] = {"median_diff_s": float(np.median(diff)),
                                                 "rel": float(np.median(diff) / np.median([J[ref][s] for s in ss])),
                                                 "ci95": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                                                 "n": len(ss)}
        pv = res["paired"][f"{lab}_vs_evsched"]
        res[f"{lab}_PASS"] = bool(pv["rel"] <= -0.05 and pv["ci95"][1] < 0
                                  and fails.get(lab, 0) <= fails.get("evsched", 0))
    (root / "screen.json").write_text(json.dumps(res, indent=1))
    L = [f"## P-M screening ({time.strftime('%Y-%m-%d %H:%M')}) · seeds {seeds[0]}-{seeds[-1]} · q={Q} · run `{run_dir}`", "",
         "Median over seeds of J(s) = mean over the 4 kinds of door-to-door time (s): " +
         ", ".join(f"{k} {v:.1f}" for k, v in sorted(res["median_J"].items(), key=lambda kv: kv[1])), "",
         "| comparison | median paired Δ (s) | rel | 95 % CI (s) |", "|---|---|---|---|"]
    for k, v in res["paired"].items():
        L.append(f"| {k} | {v['median_diff_s']:+.1f} | {v['rel']:+.1%} | [{v['ci95'][0]:+.1f}, {v['ci95'][1]:+.1f}] |")
    L += ["", f"FAIL runs: {fails}", f"**final PASS: {res.get('drl_final_PASS')}** · best PASS: {res.get('drl_best_PASS')}", ""]
    rp = REPO_ROOT / "docs/lab/t1_meter_pm.md"
    rp.write_text((rp.read_text() if rp.exists() else "# T1-M DRL pilots (P-M): screening\n\n") + "\n".join(L) + "\n")
    ledger.append("T1", "M-P", "S", a.tag, {"run_dir": str(run_dir)}, f"{seeds[0]}-{seeds[-1]}", len(jobs), {},
                  {k: v for k, v in res.items() if k.endswith("PASS")}, notes=str(root))
    print(json.dumps({k: v for k, v in res.items() if k.endswith("PASS")} | {"median_J": res["median_J"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
