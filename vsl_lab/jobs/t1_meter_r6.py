"""R6 confirmatory run (docs/lab/t1_meter_gscan_protocol.md, Addendum F): one frozen DRL candidate vs the pre-registered
comparators on the untouched reserved seeds 7,110,790-7,110,999 x 4 perturbation kinds at q = 1,600. Run ONCE.

python -m vsl_lab.jobs.t1_meter_r6 --gate-ok
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

KINDS = {"none": None, "slow": {"kind": "slow", "dur": 300, "v_mps": 5.0}, "block": {"kind": "block", "dur": 180},
         "surge": {"kind": "surge", "dur": 300, "factor": 1.3}}
SEEDS = list(range(7110790, 7111000))
Q = 1600
GRID = ["40:6", "40:8", "20:12", "5:8"]
CANDIDATE = REPO_ROOT / "docs/lab/frozen/r6_candidate_pm4_s3_best_val.zip"
CAND_SHA = "d855ba4c7cf0be275df20e18131878e4e688443d7de1fc80d2b2fdad01015c15"
MPCF_SHA = "415ea0510523c2816718f0123e6a4a3f56a233a50c38639aa7f1658efc0b8224"
COMPS = ["evsched", "mpcf", "pooled", "meter106", "nc", "lookup"]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    assert sha(CANDIDATE) == CAND_SHA, "frozen candidate changed"
    assert sha(REPO_ROOT / "docs/lab/t1_mpcf_model.pt") == MPCF_SHA, "frozen MPC-F changed"
    marker = REPO_ROOT / "docs/lab/t1_meter_r6.json"
    assert not marker.exists(), "R6 already ran: it is run once"
    lk = json.loads((REPO_ROOT / "docs/lab/t1_meter_lookup.json").read_text())["lookup"][str(Q)]
    root = RUNS_ROOT / "t1" / f"r6m_{int(time.time())}"
    jobs = []
    for k, pk in KINDS.items():
        base = {"perturb": pk} if pk else {}
        rlk = dict(base, actuator="meter_sched", meter_grid=GRID, allow_off=False, decision_s=30, obs_stack=1)
        ctrls = [("nc", "nc", base), ("meter106", "meter:10:6", base), ("pooled", lk["pooled_best"], base),
                 ("lookup", lk["per_kind"][k], base), ("evsched", "evsched:7:20:1.15", base), ("mpcf", "mpcf", base),
                 ("drl", f"rl:{CANDIDATE}:recurrentppo", rlk)]
        for s in SEEDS:
            for lab, c, ek in ctrls:
                jobs.append(Job(jid=f"r6_{lab}_{k}_s{s}", argv=["vsl_lab.jobs.bn4_eval", "--ctrl", c, "--inflow", str(Q), "--seed",
                                                              str(s), "--tag", f"{lab}__{k}", "--out-root", str(root),
                                                              "--env-kwargs", json.dumps(ek)]))
    run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    d, fails = {}, {}
    for p in root.glob("*__*/*.json"):
        lab, k = p.parent.name.split("__")
        o = json.loads(p.read_text())
        d.setdefault(lab, {}).setdefault(k, {})[o["seed"]] = o["mean_time_in_system_s"]
        fails[lab] = fails.get(lab, 0) + (o.get("health") == "FAIL")
    J = {lab: {s: float(np.mean([per[k][s] for k in KINDS])) for s in SEEDS if all(s in per.get(k, {}) for k in KINDS)}
         for lab, per in d.items()}
    rng = np.random.default_rng(7110999)

    def paired(x: dict, y: dict, n=10000):
        ss = sorted(set(x) & set(y))
        diff = np.array([x[s] - y[s] for s in ss])
        b = [np.median(rng.choice(diff, len(diff))) for _ in range(n)]
        base = float(np.median([y[s] for s in ss]))
        return {"median_diff_s": float(np.median(diff)), "ci95": [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))],
                "rel": float(np.median(diff) / base), "n": len(ss)}

    res = {"candidate_sha256": CAND_SHA, "mpcf_sha256": MPCF_SHA, "median_J": {k: float(np.median(list(v.values())))
           for k, v in J.items()}, "paired": {ref: paired(J["drl"], J[ref]) for ref in COMPS}, "per_kind": {}, "fails": fails}
    for k in KINDS:
        for ref in ("evsched", "mpcf"):
            pk = paired(d["drl"][k], d[ref][k], 5000)
            pk["sig_worse_gt5pct"] = bool(pk["ci95"][0] > 0 and pk["rel"] > 0.05)
            res["per_kind"][f"{k}_vs_{ref}"] = pk
    beats = {ref: bool(res["paired"][ref]["median_diff_s"] < 0 and res["paired"][ref]["ci95"][1] < 0) for ref in COMPS}
    fail_share = fails.get("drl", 0) / (len(SEEDS) * len(KINDS))
    res["beats"] = beats
    res["fail_share_drl"] = fail_share
    res["CLAIM"] = bool(beats["evsched"] and beats["mpcf"] and not any(v["sig_worse_gt5pct"] for v in res["per_kind"].values())
                        and fail_share <= 0.05)
    marker.write_text(json.dumps(res, indent=1))
    L = ["# R6 confirmatory: frozen DRL meter scheduler vs tuned non-learning control", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/t1_meter_gscan_protocol.md` Addendum F · reserved seeds "
         f"{SEEDS[0]}-{SEEDS[-1]} (210) × 4 kinds · q = {Q} · candidate sha256 {CAND_SHA[:12]}… · raw `{root}`*", "",
         f"**Pre-registered claim - the frozen DRL controller measurably improves on the best non-learning control (beats the "
         f"event scheduler AND the fitted-model MPC; no kind significantly worse by > 5 %; FAIL share ≤ 5 %): "
         f"{'YES' if res['CLAIM'] else 'NO'}**", "",
         "Median over seeds of J (mean over the 4 kinds of door-to-door time, s): " +
         ", ".join(f"{k} {v:.1f}" for k, v in sorted(res["median_J"].items(), key=lambda kv: kv[1])), "",
         "| DRL vs | median paired Δ (s) | 95 % CI (s) | rel | beats |", "|---|---|---|---|---|"]
    for ref in COMPS:
        v = res["paired"][ref]
        L.append(f"| {ref} | {v['median_diff_s']:+.1f} | [{v['ci95'][0]:+.1f}, {v['ci95'][1]:+.1f}] | {v['rel']:+.1%} | "
                 f"{'yes' if beats[ref] else 'no'} |")
    L += ["", "| kind vs | Δ (s) [95 % CI] | rel |", "|---|---|---|"]
    for k, v in res["per_kind"].items():
        L.append(f"| {k} | {v['median_diff_s']:+.1f} [{v['ci95'][0]:+.1f}, {v['ci95'][1]:+.1f}] | {v['rel']:+.1%} |")
    L += ["", f"FAIL runs: {fails} · DRL FAIL share {fail_share:.1%}"]
    (REPO_ROOT / "docs/lab/t1_meter_r6.md").write_text("\n".join(L) + "\n")
    ledger.append("T1", "R6", "C", "t1_meter_r6", {"candidate": str(CANDIDATE), "sha256": CAND_SHA}, f"{SEEDS[0]}-{SEEDS[-1]}",
                  len(jobs), fails, {"CLAIM": res["CLAIM"], "beats": beats}, notes=str(root))
    print(json.dumps({"CLAIM": res["CLAIM"], "beats": beats, "median_J": res["median_J"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
