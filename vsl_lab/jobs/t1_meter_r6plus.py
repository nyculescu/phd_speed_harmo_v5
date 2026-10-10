"""R6+ (docs/lab/t1_meter_gscan_protocol.md, Addendum G; decision D5.3): the frozen R6 hybrid (RecurrentPPO scheduling the
validated feedback meter) against a FAIR VANILLA DRL (the same RecurrentPPO setting the metering rate directly, no
feedback law) and no control, on fresh seeds x the 4 perturbation kinds at q = 1,600. Bar (D5.1): the hybrid beats the
vanilla DRL and no control by >= 10 % each (median paired difference / comparator median, 95 % CI upper bound < 0).
The tuned non-learning arms and the lookup oracle are reported per kind (the operating map), never the bar.

python -m vsl_lab.jobs.t1_meter_r6plus freeze --runs DIR DIR DIR   # pick the vanilla candidate on validation only
python -m vsl_lab.jobs.t1_meter_r6plus eval --gate-ok               # run ONCE on the approved seed block
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT

KINDS = {"none": None, "slow": {"kind": "slow", "dur": 300, "v_mps": 5.0}, "block": {"kind": "block", "dur": 180},
         "surge": {"kind": "surge", "dur": 300, "factor": 1.3}}
SEEDS = list(range(7112700, 7112910))          # Addendum G: 210 fresh seeds (block 7,112,000-999, author approval)
Q = 1600
GRID = ["40:6", "40:8", "20:12", "5:8"]
HYBRID = REPO_ROOT / "docs/lab/frozen/r6_candidate_pm4_s3_best_val.zip"
HYBRID_SHA = "d855ba4c7cf0be275df20e18131878e4e688443d7de1fc80d2b2fdad01015c15"
MPCF_SHA = "415ea0510523c2816718f0123e6a4a3f56a233a50c38639aa7f1658efc0b8224"
VANILLA = REPO_ROOT / "docs/lab/frozen/r6plus_vanilla_candidate.zip"
VANILLA_REC = REPO_ROOT / "docs/lab/t1_meter_r6plus_candidate.json"
MARKER = REPO_ROOT / "docs/lab/t1_meter_r6plus.json"
BAR = -0.10                                     # rel = median paired diff / comparator median J
BAR_REFS = ("vanilla", "nc")
MAP_REFS = ("vanilla", "nc", "evsched", "mpcf")  # per-kind operating map
REPORT_REFS = ("vanilla", "nc", "evsched", "mpcf", "pooled", "meter106", "lookup")
N_MAP = len(KINDS) * len(MAP_REFS)              # Bonferroni family for the per-kind flags


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freeze(runs: list[str]) -> dict:
    """Addendum G rule (as Addendum F): among the learners' best-validation checkpoints, the lowest validation score
    (validation metric tts_system_ctrl_vehh = -best_val_return); validation seeds only."""
    assert not VANILLA.exists() and not VANILLA_REC.exists(), "vanilla candidate already frozen"
    rows = []
    for r in runs:
        d = Path(r)
        res = json.loads((d / "summary.json").read_text()) if (d / "summary.json").exists() else None
        cfg = json.loads((d / "config.json").read_text())
        assert json.loads(cfg["env_kwargs"])["actuator"] == "meter_rate", f"{d}: not a meter_rate run"
        bv = res.get("best_val_return") if res else None
        rows.append({"run_dir": str(d), "seed": cfg["seed"], "best_val_return": bv,
                     "val_score": None if bv is None else -bv, "updates_done": res.get("updates_done") if res else None})
    ok = [x for x in rows if x["val_score"] is not None and (Path(x["run_dir"]) / "best_val_model.zip").exists()]
    best = min(ok, key=lambda x: x["val_score"])
    VANILLA.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(best["run_dir"]) / "best_val_model.zip", VANILLA)
    rec = {"protocol": "docs/lab/t1_meter_gscan_protocol.md Addendum G", "rule": "lowest validation score",
           "learners": rows, "chosen": best, "file": str(VANILLA.relative_to(REPO_ROOT)), "sha256": sha(VANILLA)}
    VANILLA_REC.write_text(json.dumps(rec, indent=1))
    return rec


def _paired(x: dict, y: dict, rng, n: int = 10000, level: float = 0.95) -> dict:
    ss = sorted(set(x) & set(y))
    diff = np.array([x[s] - y[s] for s in ss])
    b = np.array([np.median(rng.choice(diff, len(diff))) for _ in range(n)])
    base = float(np.median([y[s] for s in ss]))
    lo, hi = 100 * (1 - level) / 2, 100 * (1 + level) / 2
    return {"median_diff_s": float(np.median(diff)), "ci": [float(np.percentile(b, lo)), float(np.percentile(b, hi))],
            "level": level, "rel": float(np.median(diff) / base), "comparator_median_J": base, "n": len(ss)}


def evaluate(workers: int, gate_ok: bool) -> dict:
    from vsl_lab.ops import ledger
    from vsl_lab.ops.scheduler import Job, run_batch
    assert sha(HYBRID) == HYBRID_SHA, "frozen hybrid changed"
    assert sha(REPO_ROOT / "docs/lab/t1_mpcf_model.pt") == MPCF_SHA, "frozen MPC-F changed"
    rec = json.loads(VANILLA_REC.read_text())
    assert sha(VANILLA) == rec["sha256"], "frozen vanilla candidate changed"
    assert not MARKER.exists(), "R6+ already ran: it is run once"
    lk = json.loads((REPO_ROOT / "docs/lab/t1_meter_lookup.json").read_text())["lookup"][str(Q)]
    root = RUNS_ROOT / "t1" / f"r6plus_{int(time.time())}"
    jobs = []
    for k, pk in KINDS.items():
        base = {"perturb": pk} if pk else {}
        hyb = dict(base, actuator="meter_sched", meter_grid=GRID, allow_off=False, decision_s=30, obs_stack=1)
        van = dict(base, actuator="meter_rate", decision_s=30, obs_stack=1)
        ctrls = [("nc", "nc", base), ("meter106", "meter:10:6", base), ("pooled", lk["pooled_best"], base),
                 ("lookup", lk["per_kind"][k], base), ("evsched", "evsched:7:20:1.15", base), ("mpcf", "mpcf", base),
                 ("hybrid", f"rl:{HYBRID}:recurrentppo", hyb), ("vanilla", f"rl:{VANILLA}:recurrentppo", van)]
        for s in SEEDS:
            for lab, c, ek in ctrls:
                jobs.append(Job(jid=f"r6p_{lab}_{k}_s{s}", argv=["vsl_lab.jobs.bn4_eval", "--ctrl", c, "--inflow", str(Q),
                                                                "--seed", str(s), "--tag", f"{lab}__{k}", "--out-root",
                                                                str(root), "--env-kwargs", json.dumps(ek)]))
    ledger.append("T1", "R6+", "C", "t1_meter_r6plus_started", {"hybrid": HYBRID_SHA, "vanilla": rec["sha256"]},
                  f"{SEEDS[0]}-{SEEDS[-1]}", len(jobs), {}, {"status": "started"}, notes=str(root))
    run_batch(jobs, root / "batch", workers, gate_ok=gate_ok)
    d, fails = {}, {}
    for p in root.glob("*__*/*.json"):
        lab, k = p.parent.name.split("__")
        o = json.loads(p.read_text())
        d.setdefault(lab, {}).setdefault(k, {})[o["seed"]] = o["mean_time_in_system_s"]
        fails[lab] = fails.get(lab, 0) + (o.get("health") == "FAIL")
    J = {lab: {s: float(np.mean([per[k][s] for k in KINDS])) for s in SEEDS if all(s in per.get(k, {}) for k in KINDS)}
         for lab, per in d.items()}
    rng = np.random.default_rng(7112999)
    res = {"hybrid_sha256": HYBRID_SHA, "vanilla_sha256": rec["sha256"], "mpcf_sha256": MPCF_SHA, "seeds": [SEEDS[0], SEEDS[-1]],
           "median_J": {k: float(np.median(list(v.values()))) for k, v in J.items()},
           "p90_J": {k: float(np.percentile(list(v.values()), 90)) for k, v in J.items()},
           "paired": {ref: _paired(J["hybrid"], J[ref], rng) for ref in REPORT_REFS},
           "vanilla_vs_nc": _paired(J["vanilla"], J["nc"], rng),
           "per_kind": {}, "fails": fails}
    lvl = 1 - 0.05 / N_MAP
    for k in KINDS:
        for ref in MAP_REFS:
            pk = _paired(d["hybrid"][k], d[ref][k], rng, 5000)
            pk_b = _paired(d["hybrid"][k], d[ref][k], rng, 5000, level=lvl)
            pk["bonferroni_ci"] = pk_b["ci"]
            pk["regime"] = ("hybrid better" if pk_b["ci"][1] < 0 else "hybrid worse" if pk_b["ci"][0] > 0 else "tie")
            res["per_kind"][f"{k}_vs_{ref}"] = pk
    res["share_seeds_hybrid_worse_than_nc"] = float(np.mean([J["hybrid"][s] > J["nc"][s] for s in J["hybrid"] if s in J["nc"]]))
    res["bar"] = {ref: bool(res["paired"][ref]["rel"] <= BAR and res["paired"][ref]["ci"][1] < 0) for ref in BAR_REFS}
    res["fail_share"] = {lab: fails.get(lab, 0) / (len(SEEDS) * len(KINDS)) for lab in ("hybrid", "vanilla")}
    res["PASS"] = bool(all(res["bar"].values()) and res["fail_share"]["hybrid"] <= 0.05)
    MARKER.write_text(json.dumps(res, indent=1))
    _report(res, root)
    ledger.append("T1", "R6+", "C", "t1_meter_r6plus", {"hybrid": HYBRID_SHA, "vanilla": rec["sha256"]},
                  f"{SEEDS[0]}-{SEEDS[-1]}", len(jobs), fails, {"PASS": res["PASS"], "bar": res["bar"]}, notes=str(root))
    return res


def _report(res: dict, root: Path) -> None:
    L = ["# R6+: the R6 hybrid vs a fair vanilla DRL and no control (bar D5.1), with the operating map", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/t1_meter_gscan_protocol.md` Addendum G · seeds "
         f"{res['seeds'][0]}-{res['seeds'][1]} (210) × 4 kinds · q = {Q} · hybrid {res['hybrid_sha256'][:12]}… · vanilla "
         f"{res['vanilla_sha256'][:12]}… · raw `{root}`*", "",
         f"**Pre-registered bar: the hybrid beats the vanilla DRL and no control by ≥ 10 % each (CI upper bound < 0), "
         f"hybrid FAIL share ≤ 5 %: {'PASS' if res['PASS'] else 'FAIL'}** (vanilla: {'yes' if res['bar']['vanilla'] else 'no'}"
         f", no control: {'yes' if res['bar']['nc'] else 'no'})", "",
         "Median J (mean over the 4 kinds of door-to-door time, s): " +
         ", ".join(f"{k} {v:.1f}" for k, v in sorted(res["median_J"].items(), key=lambda kv: kv[1])), "",
         "| hybrid vs | median paired Δ (s) | 95 % CI (s) | rel | role |", "|---|---|---|---|---|"]
    for ref, v in res["paired"].items():
        L.append(f"| {ref} | {v['median_diff_s']:+.1f} | [{v['ci'][0]:+.1f}, {v['ci'][1]:+.1f}] | {v['rel']:+.1%} | "
                 f"{'bar' if ref in BAR_REFS else 'reported'} |")
    v = res["vanilla_vs_nc"]
    L += ["", f"Vanilla DRL vs no control: {v['median_diff_s']:+.1f} s [{v['ci'][0]:+.1f}, {v['ci'][1]:+.1f}] ({v['rel']:+.1%}).",
          "", f"**Operating map** (per kind; regime from the Bonferroni CI over {N_MAP} comparisons):", "",
          "| kind vs | Δ (s) [95 % CI] | rel | regime |", "|---|---|---|---|"]
    for k, v in res["per_kind"].items():
        L.append(f"| {k} | {v['median_diff_s']:+.1f} [{v['ci'][0]:+.1f}, {v['ci'][1]:+.1f}] | {v['rel']:+.1%} | {v['regime']} |")
    L += ["", "**Robustness (report-only):** 90th-percentile J: " +
          ", ".join(f"{k} {v:.1f}" for k, v in sorted(res["p90_J"].items(), key=lambda kv: kv[1])) +
          f" · seeds where the hybrid is worse than no control: {res['share_seeds_hybrid_worse_than_nc']:.1%} · FAIL runs "
          f"{res['fails']}"]
    (REPO_ROOT / "docs/lab/t1_meter_r6plus.md").write_text("\n".join(L) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["freeze", "eval"])
    ap.add_argument("--runs", nargs="*", default=[])
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "freeze":
        print(json.dumps(freeze(a.runs)["chosen"]))
    else:
        r = evaluate(a.workers, a.gate_ok)
        print(json.dumps({"PASS": r["PASS"], "bar": r["bar"], "median_J": r["median_J"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
