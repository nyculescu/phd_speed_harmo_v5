"""R6+ post-result diagnostics (docs/lab/t1_meter_gscan_protocol.md, Addendum H). Labelled post-result; they cannot change
the R6+ FAIL. (a) Is the vanilla DRL's win mostly a good constant metering rate? (b) Does the proven-controller structure
buy robustness out of distribution?

python -m vsl_lab.jobs.t1_meter_r6plus_diag all --gate-ok     # const-tune -> const-test -> ood, then the report
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.envs.bn4_env import RATE_GRID
from vsl_lab.jobs import t1_meter_r6plus as R6P
from vsl_lab.jobs.t1_meter2_h import COND as OOD_COND
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

KINDS = R6P.KINDS
Q = 1600
TUNE_SEEDS = list(range(7112100, 7112200))
OOD_SEEDS = list(range(7112300, 7112400))
IN_DIST = {"none", "slow_v5_d300", "block_d180", "surge_f1.3_d300"}
OUT = REPO_ROOT / "docs/lab/t1_meter_r6plus_diag.json"
RAW = RUNS_ROOT / "t1" / "r6plus_diag"


def _job(jid, ctrl, q, seed, tag, root, ek):
    return Job(jid=jid, argv=["vsl_lab.jobs.bn4_eval", "--ctrl", ctrl, "--inflow", str(q), "--seed", str(seed), "--tag", tag,
                              "--out-root", str(root), "--env-kwargs", json.dumps(ek)])


def _load(root: Path) -> dict:
    d = {}
    for p in root.glob("*__*/*.json"):
        lab, c = p.parent.name.split("__")
        o = json.loads(p.read_text())
        d.setdefault(lab, {}).setdefault(c, {})[o["seed"]] = o["mean_time_in_system_s"]
    return d


def _paired(x: dict, y: dict, rng, level=0.95, n=5000) -> dict:
    ss = sorted(set(x) & set(y))
    diff = np.array([x[s] - y[s] for s in ss])
    b = np.array([np.median(rng.choice(diff, len(diff))) for _ in range(n)])
    lo, hi = 100 * (1 - level) / 2, 100 * (1 + level) / 2
    base = float(np.median([y[s] for s in ss]))
    return {"median_diff_s": float(np.median(diff)), "ci": [float(np.percentile(b, lo)), float(np.percentile(b, hi))],
            "level": level, "rel": float(np.median(diff) / base), "n": len(ss)}


def const_tune(workers, gate_ok) -> dict:
    root = RAW / f"tune_{int(time.time())}"
    jobs = [_job(f"rt_{int(r)}_{k}_s{s}", f"rate:{r:g}", Q, s, f"rate{int(r)}__{k}", root, {"perturb": pk} if pk else {})
            for r in RATE_GRID for k, pk in KINDS.items() for s in TUNE_SEEDS]
    run_batch(jobs, root / "batch", workers, gate_ok=gate_ok)
    d = _load(root)
    J = {lab: float(np.median([np.mean([per[k][s] for k in KINDS]) for s in TUNE_SEEDS
                               if all(s in per.get(k, {}) for k in KINDS)])) for lab, per in d.items()}
    pooled = min(J, key=J.get)
    per_kind = {k: min(d, key=lambda lab: np.median(list(d[lab][k].values()))) for k in KINDS}
    return {"raw": str(root), "median_J_by_rate": J, "pooled_best": pooled, "per_kind_best": per_kind}


def const_test(tune: dict, workers, gate_ok) -> dict:
    r6p = json.loads(R6P.MARKER.read_text())
    root6 = _r6plus_root()
    root = RAW / f"test_{int(time.time())}"
    rate_of = lambda lab: float(lab.replace("rate", ""))
    jobs = []
    for k, pk in KINDS.items():
        ek = {"perturb": pk} if pk else {}
        for lab in {tune["pooled_best"], tune["per_kind_best"][k]}:
            for s in R6P.SEEDS:
                jobs.append(_job(f"rx_{lab}_{k}_s{s}", f"rate:{rate_of(lab):g}", Q, s, f"{lab}__{k}", root, ek))
    run_batch(jobs, root / "batch", workers, gate_ok=gate_ok)
    d = _load(root) | {lab: v for lab, v in _load(root6).items() if lab in ("vanilla", "hybrid", "nc", "evsched", "mpcf", "lookup")}
    pb = tune["pooled_best"]
    J = lambda lab: {s: float(np.mean([d[lab][k][s] for k in KINDS])) for s in R6P.SEEDS if all(s in d[lab].get(k, {}) for k in KINDS)}
    Jo = {s: float(np.mean([d[tune["per_kind_best"][k]][k][s] for k in KINDS])) for s in R6P.SEEDS
          if all(s in d[tune["per_kind_best"][k]].get(k, {}) for k in KINDS)}
    rng = np.random.default_rng(7112199)
    res = {"raw": str(root), "r6plus_raw": str(root6), "pooled_best": pb,
           "median_J": {"const_pooled": float(np.median(list(J(pb).values()))), "const_per_kind_oracle": float(np.median(list(Jo.values()))),
                        **{lab: r6p["median_J"][lab] for lab in ("vanilla", "hybrid", "nc", "evsched", "mpcf", "lookup")}},
           "vanilla_vs_const": _paired(J("vanilla"), J(pb), rng), "hybrid_vs_const": _paired(J("hybrid"), J(pb), rng),
           "const_vs_nc": _paired(J(pb), J("nc"), rng), "vanilla_vs_const_oracle": _paired(J("vanilla"), Jo, rng),
           "per_kind": {k: {"vanilla_vs_const": _paired(d["vanilla"][k], d[pb][k], rng),
                            "hybrid_vs_const": _paired(d["hybrid"][k], d[pb][k], rng)} for k in KINDS}}
    v = res["vanilla_vs_const"]
    res["reading_a"] = ("adaptive learning beyond a constant rate" if v["rel"] <= -0.05 and v["ci"][1] < 0
                        else "mostly a good constant rate")
    h = res["hybrid_vs_const"]
    res["r6_missing_strong_baseline"] = bool(h["median_diff_s"] > 0 and h["ci"][0] > 0)
    return res


def _r6plus_root() -> Path:
    rows = [l for l in (REPO_ROOT / "vsl_lab/runs/ledger.csv").read_text().splitlines() if ",t1_meter_r6plus," in l]
    return Path(rows[-1].rsplit(",", 1)[-1])


def ood(tune: dict, workers, gate_ok) -> dict:
    root = RAW / f"ood_{int(time.time())}"
    pb = tune["pooled_best"]
    hyb = dict(actuator="meter_sched", meter_grid=R6P.GRID, allow_off=False, decision_s=30, obs_stack=1)
    van = dict(actuator="meter_rate", decision_s=30, obs_stack=1)
    conds = {f"{c}@1600": (1600, pk) for c, pk in OOD_COND.items()}
    conds |= {f"{k}@{q}": (q, pk) for q in (1200, 2000) for k, pk in KINDS.items()}
    arms = [("hybrid", f"rl:{R6P.HYBRID}:recurrentppo", hyb), ("vanilla", f"rl:{R6P.VANILLA}:recurrentppo", van),
            ("nc", "nc", {}), ("evsched", "evsched:7:20:1.15", {}), ("mpcf", "mpcf", {}),
            ("const", f"rate:{float(pb.replace('rate', '')):g}", {})]
    jobs = []
    for c, (q, pk) in conds.items():
        base = {"perturb": pk} if pk else {}
        for lab, ctrl, ek in arms:
            for s in OOD_SEEDS:
                jobs.append(_job(f"ood_{lab}_{c}_s{s}", ctrl, q, s, f"{lab}__{c.replace('@', 'AT')}", root, dict(base, **ek)))
    run_batch(jobs, root / "batch", workers, gate_ok=gate_ok)
    d = {lab: {c.replace("AT", "@"): v for c, v in per.items()} for lab, per in _load(root).items()}

    def fam(c: str) -> str:
        name, q = c.split("@")
        if q != "1600":
            return f"inflow_{q}"
        return "in_dist" if name in IN_DIST else f"{name.split('_')[0]}_ood"
    fams = sorted({fam(c) for c in conds})
    Jf = {lab: {f: {s: float(np.mean([d[lab][c][s] for c in conds if fam(c) == f])) for s in OOD_SEEDS
                    if all(s in d[lab].get(c, {}) for c in conds if fam(c) == f)} for f in fams} for lab in d}
    rng = np.random.default_rng(7112399)
    lvl = 1 - 0.05 / (len(fams) * 4)
    res = {"raw": str(root), "families": fams, "median_J": {lab: {f: float(np.median(list(Jf[lab][f].values()))) for f in fams}
                                                              for lab in Jf}, "map": {}}
    for f in fams:
        for ref in ("vanilla", "nc", "evsched", "const"):
            p = _paired(Jf["hybrid"][f], Jf[ref][f], rng)
            pb_ = _paired(Jf["hybrid"][f], Jf[ref][f], rng, level=lvl)
            p["bonferroni_ci"] = pb_["ci"]
            p["regime"] = "hybrid better" if pb_["ci"][1] < 0 else "hybrid worse" if pb_["ci"][0] > 0 else "tie"
            res["map"][f"{f}_vs_{ref}"] = p
    oodf = [f for f in fams if f != "in_dist"]
    deg = {lab: float(np.median([np.mean([Jf[lab][f][s] for f in oodf]) for s in OOD_SEEDS
                                 if all(s in Jf[lab][f] for f in oodf)]) / np.median(list(Jf[lab]["in_dist"].values())))
           for lab in ("hybrid", "vanilla")}
    res["degradation_ratio"] = deg
    win = any(res["map"][f"{f}_vs_vanilla"]["regime"] == "hybrid better" for f in oodf)
    res["reading_b"] = ("robustness advantage of the hybrid" if win and deg["hybrid"] < deg["vanilla"]
                        else "no robustness advantage of the hybrid on BN4")
    return res


def report(out: dict) -> None:
    a, b, t = out["const_test"], out["ood"], out["const_tune"]
    L = ["# R6+ diagnostics (Addendum H; post-result, cannot change the R6+ FAIL)", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · tuning seeds {TUNE_SEEDS[0]}-{TUNE_SEEDS[-1]} · test = R6+ seeds · OOD seeds "
         f"{OOD_SEEDS[0]}-{OOD_SEEDS[-1]} · raw `{RAW}`*", "",
         f"## (a) Constant metering rate: **{a['reading_a']}**", "",
         f"Pooled-best constant rate on tuning seeds: **{t['pooled_best'].replace('rate', '')} veh/h** "
         f"(per-kind oracle: {t['per_kind_best']}).", "",
         "Median J on the R6+ test seeds (s): " + ", ".join(f"{k} {v:.1f}" for k, v in sorted(a["median_J"].items(), key=lambda kv: kv[1])), "",
         "| comparison | Δ (s) [95 % CI] | rel |", "|---|---|---|"]
    for k in ("vanilla_vs_const", "hybrid_vs_const", "const_vs_nc", "vanilla_vs_const_oracle"):
        v = a[k]
        L.append(f"| {k} | {v['median_diff_s']:+.1f} [{v['ci'][0]:+.1f}, {v['ci'][1]:+.1f}] | {v['rel']:+.1%} |")
    L += ["", f"R6's tuned non-learning set missed a strong baseline: **{'yes' if a['r6_missing_strong_baseline'] else 'no'}** "
          "(the pooled-best constant rate beats the hybrid with the CI excluding 0).", "",
          f"## (b) Out-of-distribution: **{b['reading_b']}**", "",
          f"Degradation ratio (median J, OOD families pooled / in-distribution): hybrid {b['degradation_ratio']['hybrid']:.2f}, "
          f"vanilla {b['degradation_ratio']['vanilla']:.2f}.", "",
          "| family | " + " | ".join(sorted(b["median_J"])) + " |", "|---|" + "---|" * len(b["median_J"])]
    for f in b["families"]:
        L.append(f"| {f} | " + " | ".join(f"{b['median_J'][lab][f]:.1f}" for lab in sorted(b["median_J"])) + " |")
    L += ["", "| hybrid vs (family) | Δ (s) [95 % CI] | rel | regime (Bonferroni) |", "|---|---|---|---|"]
    for k, v in b["map"].items():
        L.append(f"| {k} | {v['median_diff_s']:+.1f} [{v['ci'][0]:+.1f}, {v['ci'][1]:+.1f}] | {v['rel']:+.1%} | {v['regime']} |")
    (REPO_ROOT / "docs/lab/t1_meter_r6plus_diag.md").write_text("\n".join(L) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["all"])
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    assert not OUT.exists(), "Addendum H diagnostics already ran (run once)"
    ledger.append("T1", "R6+H", "S", "t1_meter_r6plus_diag_started", {}, f"{TUNE_SEEDS[0]}-{OOD_SEEDS[-1]}", 0, {},
                  {"status": "started"}, notes=str(RAW))
    tune = const_tune(a.workers, a.gate_ok)
    out = {"const_tune": tune, "const_test": const_test(tune, a.workers, a.gate_ok), "ood": ood(tune, a.workers, a.gate_ok)}
    OUT.write_text(json.dumps(out, indent=1))
    report(out)
    ledger.append("T1", "R6+H", "S", "t1_meter_r6plus_diag", {}, f"{TUNE_SEEDS[0]}-{OOD_SEEDS[-1]}", 0, {},
                  {"reading_a": out["const_test"]["reading_a"], "reading_b": out["ood"]["reading_b"],
                   "pooled_best": tune["pooled_best"]}, notes=str(RAW))
    print(json.dumps({"reading_a": out["const_test"]["reading_a"], "reading_b": out["ood"]["reading_b"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
