"""T1-M H step (docs/lab/t1_meter_gscan_protocol.md, Addendum A). python -m vsl_lab.jobs.t1_meter_h h1|h2 --gate-ok"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

QS = [1600, 2000]
KINDS = {"none": None, "slow": {"kind": "slow", "dur": 300, "v_mps": 5.0}, "block": {"kind": "block", "dur": 180},
         "surge": {"kind": "surge", "dur": 300, "factor": 1.3}}
H1_SEEDS = list(range(7110160, 7110180))
H2_SEEDS = list(range(7110180, 7110200))
GRID = [f"evsched:{v}:{t}:{f}" for v in (5, 7, 9) for t in (10, 20, 40) for f in (1.15, 1.25, 1.35)]
STATE = REPO_ROOT / "docs/lab/t1_meter_h_state.json"


def jobs_for(ctrls_by_cond, seeds, root):
    out = []
    for (q, k), ctrls in ctrls_by_cond.items():
        ek = json.dumps({"perturb": KINDS[k]} if KINDS[k] else {})
        for s in seeds:
            for lab, c in ctrls:
                out.append(Job(jid=f"h_{lab.replace(':', '_')}_{k}_q{q}_s{s}",
                               argv=["vsl_lab.jobs.bn4_eval", "--ctrl", c, "--inflow", str(q), "--seed", str(s),
                                     "--tag", f"{lab.replace(':', '_')}__{k}_q{q}", "--out-root", str(root),
                                     "--env-kwargs", ek]))
    return out


def load(root):
    d = {}
    for p in root.glob("*__*/*.json"):
        lab, cond = p.parent.name.split("__")
        k, q = cond.rsplit("_q", 1)
        o = json.loads(p.read_text())
        d.setdefault((lab, int(q), k), {})[o["seed"]] = o["mean_time_in_system_s"]
    return d


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["h1", "h2"])
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    root = RUNS_ROOT / "t1" / f"meter_{a.what}_{int(time.time())}"
    lk = json.loads((REPO_ROOT / "docs/lab/t1_meter_lookup.json").read_text())["lookup"]
    st = json.loads(STATE.read_text()) if STATE.exists() else {}
    if a.what == "h1":
        conds = {(q, k): [(c, c) for c in GRID] for q in QS for k in KINDS}
        run_batch(jobs_for(conds, H1_SEEDS, root), root / "batch", a.workers, gate_ok=a.gate_ok)
        d = load(root)
        score = {c: float(np.mean([np.median(list(d[(c.replace(':', '_'), q, k)].values())) for q in QS for k in KINDS]))
                 for c in GRID if all((c.replace(':', '_'), q, k) in d for q in QS for k in KINDS)}
        best = min(score, key=score.get)
        st["evsched"] = best
        st["h1_scores"] = dict(sorted(score.items(), key=lambda kv: kv[1])[:10])
        STATE.write_text(json.dumps(st, indent=1))
        ledger.append("T1", "M-H1", "S", "t1_meter_h1", {"grid": len(GRID)}, "7110160-7110179", len(GRID) * 160, {},
                      {"evsched": best}, notes=str(root))
        print(json.dumps({"evsched": best, "score": score[best]}))
        return 0
    ev = st["evsched"]
    conds = {}
    for q in QS:
        for k in KINDS:
            conds[(q, k)] = [("nc", "nc"), ("meter106", "meter:10:6"), ("pooled", lk[str(q)]["pooled_best"]),
                             ("lookup", lk[str(q)]["per_kind"][k]), ("evsched", ev)]
    run_batch(jobs_for(conds, H2_SEEDS, root), root / "batch", a.workers, gate_ok=a.gate_ok)
    d = load(root)
    res = {}
    rng = np.random.default_rng(7110199)
    for q in QS:
        def J(lab):
            return {s: float(np.mean([d[(lab, q, k)][s] for k in KINDS])) for s in H2_SEEDS
                    if all(s in d.get((lab, q, k), {}) for k in KINDS)}
        Js = {lab: J(lab) for lab in ("nc", "meter106", "pooled", "lookup", "evsched")}
        nl = min(("pooled", "evsched"), key=lambda lab: np.median(list(Js[lab].values())))
        ss = sorted(set(Js[nl]) & set(Js["lookup"]))
        diff = np.array([Js[nl][s] - Js["lookup"][s] for s in ss])
        boots = [np.median(rng.choice(diff, len(diff))) for _ in range(10000)]
        H = float(np.median(diff) / np.median([Js[nl][s] for s in ss]))
        res[str(q)] = {"median_J": {lab: float(np.median(list(v.values()))) for lab, v in Js.items()}, "best_nonlearning": nl,
                       "H": H, "diff_median_s": float(np.median(diff)),
                       "diff_ci95_s": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
                       "DRL_target": bool(H >= 0.10 and np.percentile(boots, 2.5) > 0), "n": len(ss)}
    out = {"evsched": ev, "per_q": res, "targets": [q for q, v in res.items() if v["DRL_target"]], "raw": str(root)}
    (REPO_ROOT / "docs/lab/t1_meter_h.json").write_text(json.dumps(out, indent=1))
    L = ["# T1-M H step (gate seeds 7,110,180-7,110,199): results", "", f"*{time.strftime('%Y-%m-%d %H:%M')} · raw `{root}` · "
         f"evsched tuned on H1: `{ev}`*", "", f"**DRL target (H ≥ 10 % and CI lower bound > 0): {out['targets'] or 'none'}**", "",
         "| q | nc | meter:10:6 | pooled fixed | evsched | lookup I (oracle) | best non-learning | H | Δ (s) [95 % CI] |",
         "|---|---|---|---|---|---|---|---|---|"]
    for q, v in res.items():
        m = v["median_J"]
        L.append(f"| {q} | {m['nc']:.1f} | {m['meter106']:.1f} | {m['pooled']:.1f} | {m['evsched']:.1f} | {m['lookup']:.1f} | "
                 f"{v['best_nonlearning']} | {v['H']:.1%} | {v['diff_median_s']:+.1f} [{v['diff_ci95_s'][0]:+.1f}, {v['diff_ci95_s'][1]:+.1f}] |")
    L += ["", "J = per-seed mean over the 4 kinds (none, slow, block, surge) of door-to-door time (s); table shows medians over seeds."]
    (REPO_ROOT / "docs/lab/t1_meter_h.md").write_text("\n".join(L) + "\n")
    ledger.append("T1", "M-H2", "S", "t1_meter_h2", {"evsched": ev}, "7110180-7110199", 8 * 20 * 5, {},
                  {"targets": out["targets"], "H": {q: round(v["H"], 4) for q, v in res.items()}}, notes=str(root))
    print(json.dumps({"targets": out["targets"], "H": {q: round(v["H"], 4) for q, v in res.items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
