"""Track 1 / T0b (preventive actuator authority), pre-registered in docs/lab/t1_bn4_plant_checks_protocol.md."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.eval.stats import paired_median_diff
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

SEEDS = list(range(7110030, 7110050))
CELLS = [1600, 2000]
ARMS = ["nc", "cap:5", "cap:10", "meter:20:8"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    root = RUNS_ROOT / "t1" / f"t0b_{int(time.time())}"
    jobs = [Job(jid=f"t0b_{c.replace(':', '_')}_q{q}_s{s}",
                argv=["vsl_lab.jobs.bn4_eval", "--ctrl", c, "--inflow", str(q), "--seed", str(s), "--tag", "t0b",
                      "--out-root", str(root)]) for q in CELLS for s in SEEDS for c in ARMS]
    rep = run_batch(jobs, root / "batch", max_workers=a.workers, gate_ok=a.gate_ok)
    R = [json.loads(p.read_text()) for p in (root / "t0b").glob("*.json")]
    by = {}
    for o in R:
        by.setdefault((o["ctrl"], int(o["inflow"])), {})[o["seed"]] = o
    health = {}
    for o in R:
        health[o["health"]] = health.get(o["health"], 0) + 1
    cells, fam_pass = {}, {"cap": False, "meter": False}
    for q in CELLS:
        base = by.get(("nc", q), {})
        for arm in ARMS[1:]:
            d = by.get((arm, q), {})
            ss = sorted(set(base) & set(d))
            x = [base[s]["outflow_ctrl_vph"] for s in ss]
            y = [d[s]["outflow_ctrl_vph"] for s in ss]
            pm = paired_median_diff(x, y, seed=7110049)
            ref = float(np.median(x))
            rel = pm["median_diff"] / ref
            tt = paired_median_diff([base[s]["mean_time_in_system_s"] for s in ss],
                                    [d[s]["mean_time_in_system_s"] for s in ss], seed=7110049)
            ok = abs(rel) >= 0.05 and pm["excludes_0"]
            fam = "cap" if arm.startswith("cap") else "meter"
            fam_pass[fam] = fam_pass[fam] or ok
            cells[f"q{q}_{arm}"] = {"nc_median_outflow": ref, "arm_median_outflow": float(np.median(y)),
                                   "outflow_paired": pm, "rel": round(rel, 4), "binds": ok,
                                   "time_in_system_paired_s": tt, "n": len(ss)}
    out = {"n_runs": len(R), "health": health, "cells": cells, "PASS": fam_pass}
    (root / "t0b_analysis.json").write_text(json.dumps(out, indent=1))
    L = ["", "## T0b (preventive actuator authority): results", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · {len(R)} runs · health {health} · raw `{root}`*", "",
         f"**AV cap family: {'PASS' if fam_pass['cap'] else 'FAIL'} · meter: {'PASS' if fam_pass['meter'] else 'FAIL'}**", "",
         "| cell | nc median outflow | arm median outflow | Δ outflow [95 % CI] | rel. | Δ time in system (s) [95 % CI] |",
         "|---|---|---|---|---|---|"]
    for k, c in cells.items():
        pm, tt = c["outflow_paired"], c["time_in_system_paired_s"]
        L.append(f"| {k} | {c['nc_median_outflow']:.0f} | {c['arm_median_outflow']:.0f} | {pm['median_diff']:+.0f} "
                 f"[{pm['ci_lo']:+.0f}, {pm['ci_hi']:+.0f}] | {c['rel']:+.1%} | {tt['median_diff']:+.1f} "
                 f"[{tt['ci_lo']:+.1f}, {tt['ci_hi']:+.1f}] |")
    rp = REPO_ROOT / "docs" / "lab" / "t1_bn4_plant_checks.md"
    rp.write_text(rp.read_text() + "\n".join(L) + "\n")
    ledger.append("T1", "R1", "S", "t0b_preventive", {"arms": ARMS, "cells": CELLS}, "7110030-7110049", len(R),
                  health, {"PASS": fam_pass, "cells": {k: {"rel": v["rel"], "binds": v["binds"]} for k, v in cells.items()}},
                  notes=str(root))
    print(json.dumps({"PASS": fam_pass, "health": health,
                      "cells": {k: (v["rel"], v["binds"]) for k, v in cells.items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
