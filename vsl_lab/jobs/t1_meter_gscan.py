"""T1-M meter headroom scan (docs/lab/t1_meter_gscan_protocol.md). python -m vsl_lab.jobs.t1_meter_gscan --gate-ok"""
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
CTRLS = ["nc"] + [f"meter:{k}:{n}" for k in (5, 10, 20, 40) for n in (4, 6, 8, 10, 12)]
SEEDS = list(range(7110160, 7110180))
FAMS = {"slow": ["none", "slow"], "block": ["none", "block"], "surge": ["none", "surge"], "all": list(KINDS)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--root", default=None)
    ap.add_argument("--analyse-only", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.root) if a.root else RUNS_ROOT / "t1" / f"meter_gscan_{int(time.time())}"
    if not a.analyse_only:
        jobs = []
        for q in QS:
            for k, pk in KINDS.items():
                ek = json.dumps({"perturb": pk} if pk else {})
                jobs += [Job(jid=f"mg_{k}_q{q}_{c.replace(':', '_')}_s{s}",
                             argv=["vsl_lab.jobs.bn4_eval", "--ctrl", c, "--inflow", str(q), "--seed", str(s),
                                   "--tag", f"{k}_q{q}", "--out-root", str(root), "--env-kwargs", ek])
                         for s in SEEDS for c in CTRLS]
        run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    J, tele, fails = {}, {}, {}
    for q in QS:
        for k in KINDS:
            d = {}
            for p in (root / f"{k}_q{q}").glob("*.json"):
                o = json.loads(p.read_text())
                d.setdefault(o["ctrl"], []).append(o)
            J[(q, k)] = {c: float(np.median([o["mean_time_in_system_s"] for o in v])) for c, v in d.items()}
            tele[(q, k)] = sum("H-R3" in (o.get("health_codes") or []) for v in d.values() for o in v)
            fails[(q, k)] = sum(o.get("health") == "FAIL" for v in d.values() for o in v)
    res = {}
    for q in QS:
        for fam, kinds in FAMS.items():
            common = [c for c in CTRLS if all(c in J[(q, k)] for k in kinds)]
            mean_c = {c: float(np.mean([J[(q, k)][c] for k in kinds])) for c in common}
            pool = min(mean_c, key=mean_c.get)
            look = float(np.mean([min(J[(q, k)][c] for c in common) for k in kinds]))
            best = {k: min(common, key=lambda c: J[(q, k)][c]) for k in kinds}
            res[f"q{q}_{fam}"] = {"pooled_best": pool, "J_pool": mean_c[pool], "J_lookup": look, "per_kind_best": best,
                                  "G": (mean_c[pool] - look) / mean_c[pool]}
    targets = [k for k, v in res.items() if v["G"] >= 0.10]
    out = {"families": res, "targets": targets, "teleport_runs": {f"q{q}_{k}": tele[(q, k)] for q, k in tele},
           "fail_runs": {f"q{q}_{k}": fails[(q, k)] for q, k in fails}, "raw": str(root)}
    (REPO_ROOT / "docs/lab/t1_meter_gscan.json").write_text(json.dumps(out, indent=1))
    L = ["# T1-M meter headroom scan: results", "", f"*{time.strftime('%Y-%m-%d %H:%M')} · raw `{root}`*", "",
         f"**Candidate DRL targets (G ≥ 10 %): {targets or 'none'}**", "",
         "| family | G | pooled best | per-condition best | J pooled (s) | J lookup (s) |", "|---|---|---|---|---|---|"]
    for k, v in res.items():
        L.append(f"| {k} | {v['G']:.1%} | {v['pooled_best']} | {v['per_kind_best']} | {v['J_pool']:.1f} | {v['J_lookup']:.1f} |")
    L += ["", f"Teleport runs per condition: {out['teleport_runs']}", f"FAIL runs per condition: {out['fail_runs']}", "",
          "Median door-to-door (s) per condition: nc / best meter:", ""]
    for (q, k), d in J.items():
        b = min(d, key=d.get)
        L.append(f"- q={q} {k}: nc {d.get('nc', float('nan')):.1f} · best {b} {d[b]:.1f} · meter:10:6 {d.get('meter:10:6', float('nan')):.1f}")
    (REPO_ROOT / "docs/lab/t1_meter_gscan.md").write_text("\n".join(L) + "\n")
    ledger.append("T1", "M-gscan", "S", "t1_meter_gscan", {"kinds": list(KINDS), "ctrls": len(CTRLS)}, "7110160-7110179",
                  sum(1 for _ in root.rglob("*.json")), {}, {"targets": targets}, notes=str(root))
    print(json.dumps({"targets": targets, "G": {k: round(v["G"], 4) for k, v in res.items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
