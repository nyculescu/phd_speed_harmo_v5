"""BN4 confirmatory under the conditional bar (docs/lab/t1_meter_gscan_protocol.md, Addendum I; D5.8, D5.9): the frozen
plain-DRL meter (R6+ candidate) vs tuned ALINEA, the tuned constant rate, evsched, MPC-F, the pooled feedback meter, the
R6 hybrid and NC, on fresh seeds x the 4 kinds at q = 1,600. Run ONCE.

python -m vsl_lab.jobs.t1_meter_bn4_confirm all --gate-ok   # ALINEA tuning (+ one edge extension) -> freeze -> test
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.jobs import t1_meter_r6plus as R6P
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

KINDS = R6P.KINDS
Q = 1600
TUNE_SEEDS = list(range(7112200, 7112300))
TEST_SEEDS = list(range(7112400, 7112610))
K_GRID = [20.0, 40.0, 70.0, 120.0, 200.0]
O_GRID = [5.0, 8.0, 11.0, 14.0, 18.0, 22.0, 27.0]
CONST = "rate:1800"                                   # Addendum H pooled-best constant rate
TUNED = REPO_ROOT / "docs/lab/t1_meter_alinea_tuned.json"
OUT = REPO_ROOT / "docs/lab/t1_meter_bn4_confirm.json"
RAW = RUNS_ROOT / "t1" / "bn4_confirm"
NONLEARN = ("alinea", "const", "evsched", "mpcf", "pooled")


def _job(jid, ctrl, seed, tag, root, ek):
    return Job(jid=jid, argv=["vsl_lab.jobs.bn4_eval", "--ctrl", ctrl, "--inflow", str(Q), "--seed", str(seed), "--tag", tag,
                              "--out-root", str(root), "--env-kwargs", json.dumps(ek)])


def _load(root: Path) -> tuple[dict, dict]:
    d, fails = {}, {}
    for p in root.glob("*__*/*.json"):
        lab, k = p.parent.name.split("__")
        o = json.loads(p.read_text())
        d.setdefault(lab, {}).setdefault(k, {})[o["seed"]] = o["mean_time_in_system_s"]
        fails[lab] = fails.get(lab, 0) + (o.get("health") == "FAIL")
    return d, fails


def _pooled_J(per: dict, seeds) -> dict:
    return {s: float(np.mean([per[k][s] for k in KINDS])) for s in seeds if all(s in per.get(k, {}) for k in KINDS)}


def _tune_grid(ks, os_, workers, gate_ok, root) -> dict:
    jobs = [_job(f"al_{k:g}_{o:g}_{kd}_s{s}", f"alinea:{k:g}:{o:g}", s, f"al{k:g}-{o:g}__{kd}", root,
                 {"perturb": pk} if pk else {}) for k in ks for o in os_ for kd, pk in KINDS.items() for s in TUNE_SEEDS]
    run_batch(jobs, root / "batch", workers, gate_ok=gate_ok)
    d, _ = _load(root)
    return {lab: float(np.median(list(_pooled_J(per, TUNE_SEEDS).values()))) for lab, per in d.items()}


def tune(workers, gate_ok) -> dict:
    assert not TUNED.exists(), "ALINEA already tuned (frozen)"
    root = RAW / f"tune_{int(time.time())}"
    med = _tune_grid(K_GRID, O_GRID, workers, gate_ok, root)
    best = min(med, key=med.get)
    k, o = (float(x) for x in best.replace("al", "").split("-"))
    ext = None
    edges = {"K": (K_GRID, k), "o": (O_GRID, o)}
    new_k, new_o = [k], [o]
    for name, (g, v) in edges.items():   # Addendum I: one extension by two steps if the best lies on the grid edge
        step = g[-1] - g[-2] if v == g[-1] else g[1] - g[0] if v == g[0] else None
        if step is not None:
            more = [v + step, v + 2 * step] if v == g[-1] else [max(v - step, 1.0), max(v - 2 * step, 0.5)]
            if name == "K":
                new_k = [k] + more
            else:
                new_o = [o] + more
    if new_k != [k] or new_o != [o]:
        ext = {"K": new_k, "o": new_o}
        med2 = _tune_grid(new_k, new_o, workers, gate_ok, RAW / f"tune_ext_{int(time.time())}")
        med |= med2
        best = min(med, key=med.get)
        k, o = (float(x) for x in best.replace("al", "").split("-"))
    rec = {"protocol": "Addendum I", "seeds": [TUNE_SEEDS[0], TUNE_SEEDS[-1]], "grid": {"K": K_GRID, "o": O_GRID},
           "extension": ext, "median_J": med, "best": {"K": k, "o": o, "ctrl": f"alinea:{k:g}:{o:g}", "median_J": med[best]},
           "raw": str(root)}
    TUNED.write_text(json.dumps(rec, indent=1))
    ledger.append("T1", "R6+I", "S", "t1_meter_alinea_tune", {"grid": rec["grid"], "extension": ext},
                  f"{TUNE_SEEDS[0]}-{TUNE_SEEDS[-1]}", len(med) * len(TUNE_SEEDS) * len(KINDS), {}, rec["best"], notes=str(root))
    return rec


def _paired(x, y, rng, level=0.95, n=10000) -> dict:
    ss = sorted(set(x) & set(y))
    diff = np.array([x[s] - y[s] for s in ss])
    b = np.array([np.median(rng.choice(diff, len(diff))) for _ in range(n)])
    lo, hi = 100 * (1 - level) / 2, 100 * (1 + level) / 2
    base = float(np.median([y[s] for s in ss]))
    return {"median_diff_s": float(np.median(diff)), "ci": [float(np.percentile(b, lo)), float(np.percentile(b, hi))],
            "level": level, "rel": float(np.median(diff) / base), "n": len(ss)}


def confirm(workers, gate_ok) -> dict:
    assert not OUT.exists(), "the BN4 confirmatory already ran (run once)"
    rec = json.loads(R6P.VANILLA_REC.read_text())
    assert R6P.sha(R6P.VANILLA) == rec["sha256"] and R6P.sha(R6P.HYBRID) == R6P.HYBRID_SHA
    al = json.loads(TUNED.read_text())["best"]["ctrl"]
    lk = json.loads((REPO_ROOT / "docs/lab/t1_meter_lookup.json").read_text())["lookup"][str(Q)]
    root = RAW / f"test_{int(time.time())}"
    jobs = []
    for k, pk in KINDS.items():
        base = {"perturb": pk} if pk else {}
        hyb = dict(base, actuator="meter_sched", meter_grid=R6P.GRID, allow_off=False, decision_s=30, obs_stack=1)
        van = dict(base, actuator="meter_rate", decision_s=30, obs_stack=1)
        arms = [("candidate", f"rl:{R6P.VANILLA}:recurrentppo", van), ("hybrid", f"rl:{R6P.HYBRID}:recurrentppo", hyb),
                ("alinea", al, base), ("const", CONST, base), ("evsched", "evsched:7:20:1.15", base),
                ("mpcf", "mpcf", base), ("pooled", lk["pooled_best"], base), ("nc", "nc", base)]
        for s in TEST_SEEDS:
            for lab, c, ek in arms:
                jobs.append(_job(f"bc_{lab}_{k}_s{s}", c, s, f"{lab}__{k}", root, ek))
    ledger.append("T1", "R6+I", "C", "t1_meter_bn4_confirm_started", {"candidate": rec["sha256"], "alinea": al},
                  f"{TEST_SEEDS[0]}-{TEST_SEEDS[-1]}", len(jobs), {}, {"status": "started"}, notes=str(root))
    run_batch(jobs, root / "batch", workers, gate_ok=gate_ok)
    d, fails = _load(root)
    J = {lab: _pooled_J(per, TEST_SEEDS) for lab, per in d.items()}
    rng = np.random.default_rng(7112609)
    lvl = 1 - 0.05 / len(KINDS)
    res = {"candidate_sha256": rec["sha256"], "alinea": al, "seeds": [TEST_SEEDS[0], TEST_SEEDS[-1]],
           "median_J": {lab: float(np.median(list(v.values()))) for lab, v in J.items()},
           "pooled": {ref: _paired(J["candidate"], J[ref], rng) for ref in d if ref != "candidate"},
           "regimes": {}, "fails": fails}
    for k in KINDS:
        med = {lab: float(np.median(list(d[lab][k].values()))) for lab in NONLEARN}
        b = min(med, key=med.get)
        pb = _paired(d["candidate"][k], d[b][k], rng, level=lvl, n=5000)
        res["regimes"][k] = {"B": b, "median_J_nonlearning": med, "candidate_vs_B": pb,
                             "beats_B": bool(pb["ci"][1] < 0), "worse_gt5": bool(pb["rel"] > 0.05 and pb["ci"][0] > 0),
                             "map": {ref: _paired(d["candidate"][k], d[ref][k], rng, n=5000) for ref in d if ref != "candidate"},
                             "hybrid_map": {ref: _paired(d["hybrid"][k], d[ref][k], rng, n=5000) for ref in d if ref not in ("hybrid",)}}
    nc = res["pooled"]["nc"]
    fail_share = fails.get("candidate", 0) / (len(TEST_SEEDS) * len(KINDS))
    res["conditions"] = {"1_vs_nc": bool(nc["rel"] <= -0.10 and nc["ci"][1] < 0),
                         "2_beats_best_in_a_regime": any(r["beats_B"] for r in res["regimes"].values()),
                         "3_never_worse_gt5": not any(r["worse_gt5"] for r in res["regimes"].values()),
                         "4_fail_share": fail_share <= 0.05}
    res["fail_share_candidate"] = fail_share
    res["PASS"] = all(res["conditions"].values())
    OUT.write_text(json.dumps(res, indent=1))
    _report(res, root)
    ledger.append("T1", "R6+I", "C", "t1_meter_bn4_confirm", {"candidate": rec["sha256"], "alinea": al},
                  f"{TEST_SEEDS[0]}-{TEST_SEEDS[-1]}", len(jobs), fails, {"PASS": res["PASS"], "conditions": res["conditions"]},
                  notes=str(root))
    return res


def _report(res: dict, root: Path) -> None:
    L = ["# BN4 confirmatory under the conditional bar (Addendum I; D5.8)", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · seeds {res['seeds'][0]}-{res['seeds'][1]} (210) × 4 kinds · q = {Q} · candidate "
         f"(plain-DRL meter) {res['candidate_sha256'][:12]}… · ALINEA {res['alinea']} · raw `{root}`*", "",
         f"**Conditional bar: {'PASS' if res['PASS'] else 'FAIL'}** · " +
         " · ".join(f"{k}: {'yes' if v else 'no'}" for k, v in res["conditions"].items()), "",
         "Median J (s): " + ", ".join(f"{k} {v:.1f}" for k, v in sorted(res["median_J"].items(), key=lambda kv: kv[1])), "",
         "| candidate vs (pooled) | Δ (s) [95 % CI] | rel |", "|---|---|---|"]
    for ref, v in res["pooled"].items():
        L.append(f"| {ref} | {v['median_diff_s']:+.1f} [{v['ci'][0]:+.1f}, {v['ci'][1]:+.1f}] | {v['rel']:+.1%} |")
    L += ["", "| regime | best tuned non-learning B | candidate vs B: Δ (s) [Bonferroni CI] | rel | beats B | worse > 5 % |",
          "|---|---|---|---|---|---|"]
    for k, r in res["regimes"].items():
        v = r["candidate_vs_B"]
        L.append(f"| {k} | {r['B']} | {v['median_diff_s']:+.1f} [{v['ci'][0]:+.1f}, {v['ci'][1]:+.1f}] | {v['rel']:+.1%} | "
                 f"{'yes' if r['beats_B'] else 'no'} | {'yes' if r['worse_gt5'] else 'no'} |")
    L += ["", f"Candidate FAIL share {res['fail_share_candidate']:.1%} · FAIL runs {res['fails']}"]
    (REPO_ROOT / "docs/lab/t1_meter_bn4_confirm.md").write_text("\n".join(L) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["all"])
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    t = tune(a.workers, a.gate_ok)
    r = confirm(a.workers, a.gate_ok)
    print(json.dumps({"alinea": t["best"], "PASS": r["PASS"], "conditions": r["conditions"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
