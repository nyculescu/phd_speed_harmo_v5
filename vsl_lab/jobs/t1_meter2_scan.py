"""Lead 1 stage S (docs/lab/t1_meter2_protocol.md). python -m vsl_lab.jobs.t1_meter2_scan --gate-ok"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

Q = 1600
SEEDS = list(range(7170000, 7170010))
COND = {"none": None}
for v in (3.0, 5.0, 8.0):
    for d in (150, 300, 600):
        COND[f"slow_v{v:g}_d{d}"] = {"kind": "slow", "dur": d, "v_mps": v}
for d in (60, 180, 360):
    COND[f"block_d{d}"] = {"kind": "block", "dur": d}
for f in (1.15, 1.3, 1.5):
    for d in (150, 300, 600):
        COND[f"surge_f{f:g}_d{d}"] = {"kind": "surge", "dur": d, "factor": f}
FIXED = ["nc"] + [f"meter:{k}:{n}" for k in (5, 10, 20, 40) for n in (4, 6, 8, 10, 12)]
CTRLS = FIXED + ["evsched:7:20:1.15"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    root = RUNS_ROOT / "t1" / f"m2scan_{int(time.time())}"
    jobs = [Job(jid=f"m2_{c}_{ctl.replace(':', '_')}_s{s}", argv=["vsl_lab.jobs.bn4_eval", "--ctrl", ctl, "--inflow", str(Q),
                                                                  "--seed", str(s), "--tag", c, "--out-root", str(root),
                                                                  "--env-kwargs", json.dumps({"perturb": pk} if pk else {})])
            for c, pk in COND.items() for s in SEEDS for ctl in CTRLS]
    run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    J, fails = {}, {}
    for c in COND:
        d = {}
        for p in (root / c).glob("*.json"):
            o = json.loads(p.read_text())
            d.setdefault(o["ctrl"], []).append(o["mean_time_in_system_s"])
            fails[c] = fails.get(c, 0) + (o.get("health") == "FAIL")
        J[c] = {k: float(np.median(v)) for k, v in d.items()}

    def fam(conds):
        mean_f = {k: float(np.mean([J[c][k] for c in conds])) for k in FIXED if all(k in J[c] for c in conds)}
        pool = min(mean_f, key=mean_f.get)
        look = float(np.mean([min(J[c][k] for k in mean_f) for c in conds]))
        ev = float(np.mean([J[c]["evsched:7:20:1.15"] for c in conds]))
        nl = min(mean_f[pool], ev)
        return {"pooled_best": pool, "J_pool": mean_f[pool], "J_lookup": look, "J_evsched": ev,
                "G": (mean_f[pool] - look) / mean_f[pool], "H_pre": (nl - look) / nl,
                "per_cond_best": {c: min(mean_f, key=lambda k: J[c][k]) for c in conds}}
    fams = {"all": list(COND), "slow": [c for c in COND if c.startswith("slow") or c == "none"],
            "block": [c for c in COND if c.startswith("block") or c == "none"],
            "surge": [c for c in COND if c.startswith("surge") or c == "none"]}
    res = {f: fam(cs) for f, cs in fams.items()}
    target = bool(res["all"]["G"] >= 0.10 and res["all"]["H_pre"] >= 0.10)
    out = {"families": res, "stage_H": target, "fails": fails, "raw": str(root)}
    (REPO_ROOT / "docs/lab/t1_meter2_scan.json").write_text(json.dumps(out, indent=1))
    L = ["# Lead 1 stage S: headroom scan (varied severity/duration) results", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · raw `{root}` · q = {Q} · seeds {SEEDS[0]}-{SEEDS[-1]}*", "",
         f"**Proceed to stage H (G ≥ 10 % and H_pre ≥ 10 % on all conditions): {'YES' if target else 'NO'}**", "",
         "| family | G | H_pre | pooled best | J pooled | J lookup | J evsched |", "|---|---|---|---|---|---|---|"]
    for f, v in res.items():
        L.append(f"| {f} | {v['G']:.1%} | {v['H_pre']:.1%} | {v['pooled_best']} | {v['J_pool']:.1f} | {v['J_lookup']:.1f} | {v['J_evsched']:.1f} |")
    L += ["", "Per-condition best fixed setting: " + json.dumps(res["all"]["per_cond_best"]), "", f"FAIL runs: {fails}"]
    (REPO_ROOT / "docs/lab/t1_meter2_scan.md").write_text("\n".join(L) + "\n")
    ledger.append("T1", "M2-S", "S", "t1_meter2_scan", {"conds": len(COND), "ctrls": len(CTRLS)}, "7170000-7170009", len(jobs),
                  {}, {"G": round(res["all"]["G"], 4), "H_pre": round(res["all"]["H_pre"], 4), "stage_H": target}, notes=str(root))
    print(json.dumps({"stage_H": target, "G": {f: round(v["G"], 4) for f, v in res.items()},
                      "H_pre": {f: round(v["H_pre"], 4) for f, v in res.items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
