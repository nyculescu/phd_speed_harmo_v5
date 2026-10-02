"""Track 1 / R2: tune BN4 baselines per docs/lab/t1_bn4_r2_baselines_protocol.md and freeze them.

python -m vsl_lab.jobs.t1_r2_baselines --workers 10 --gate-ok
python -m vsl_lab.jobs.t1_r2_baselines --analyse-only --batch-root DIR
"""
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

CELLS = [1200, 1600, 2000, 2400]
SEEDS = list(range(7110100, 7110120))
CAPS = [3, 5, 7, 9, 11, 13, 15, 18]
METER = [(kf, nc) for kf in (10, 20, 40) for nc in (4, 6, 8, 10, 12, 14)]


def controllers() -> list:
    return ["nc"] + [f"cap:{c}" for c in CAPS] + [f"meter:{kf}:{nc}" for kf, nc in METER]


def load(root: Path) -> list:
    out = []
    for p in (root / "r2").glob("*.json"):
        try:
            out.append(json.loads(p.read_text()))
        except Exception:
            pass
    return out


def analyse(root: Path) -> dict:
    R = load(root)
    by = {}
    for o in R:
        by.setdefault((o["ctrl"], int(o["inflow"])), {})[o["seed"]] = o
    health = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for o in R:
        health[o["health"]] = health.get(o["health"], 0) + 1
    table = {}
    for ctrl in controllers():
        row = {}
        for q in CELLS:
            d = by.get((ctrl, q), {})
            if not d:
                continue
            mt = [d[s]["mean_time_in_system_s"] for s in sorted(d)]
            of = [d[s]["outflow_ctrl_vph"] for s in sorted(d)]
            row[q] = {"n": len(d), "median_time_s": float(np.median(mt)), "median_outflow": float(np.median(of)),
                      "drained_all": all(d[s].get("drained") for s in d)}
        if row:
            row["score"] = float(np.mean([row[q]["median_time_s"] for q in CELLS if q in row]))
            table[ctrl] = row
    fams = {"nc": ["nc"], "cap": [c for c in table if c.startswith("cap:")],
            "meter": [c for c in table if c.startswith("meter:")]}
    tuned = {}
    for fam, cs in fams.items():
        if not cs:
            continue
        best = min(cs, key=lambda c: table[c]["score"])
        tuned[fam] = {"ctrl": best, "score": table[best]["score"]}
    per_cell_best = {q: min(table, key=lambda c: table[c].get(q, {}).get("median_time_s", np.inf)) for q in CELLS}
    vs_nc = {}
    for fam, tb in tuned.items():
        if fam == "nc":
            continue
        vs_nc[fam] = {}
        for q in CELLS:
            a = by.get(("nc", q), {})
            b = by.get((tb["ctrl"], q), {})
            ss = sorted(set(a) & set(b))
            if ss:
                vs_nc[fam][q] = paired_median_diff([a[s]["mean_time_in_system_s"] for s in ss],
                                                   [b[s]["mean_time_in_system_s"] for s in ss], seed=7110119)
    return {"n_runs": len(R), "health": health, "table": table, "tuned": tuned, "per_cell_best": per_cell_best,
            "tuned_vs_nc_paired_time": vs_nc}


def write(res: dict, root: Path) -> None:
    frozen = {"protocol": "docs/lab/t1_bn4_r2_baselines_protocol.md", "frozen_at": time.strftime("%Y-%m-%d %H:%M"),
              "tuned": res["tuned"], "per_cell_best": res["per_cell_best"], "raw_root": str(root)}
    (REPO_ROOT / "docs" / "lab" / "t1_bn4_baselines_frozen.json").write_text(json.dumps(frozen, indent=1))
    t = res["table"]
    L = ["# Track 1 (BN4), R2 tuned baselines: results (frozen)", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/t1_bn4_r2_baselines_protocol.md` · "
         f"{res['n_runs']} runs · health {res['health']} · raw `{root}`*", "",
         "Primary: median over 20 tuning seeds of the mean time in system per vehicle (s, door-to-door incl. queue). "
         "Score = mean over the 4 cells.", "",
         "| controller | q=1200 | q=1600 | q=2000 | q=2400 | score | outflow q=2000 (veh/h) |", "|---|---|---|---|---|---|---|"]
    for c in sorted(t, key=lambda c: t[c]["score"]):
        r = t[c]
        cells = " | ".join(f"{r[q]['median_time_s']:.1f}" if q in r else "-" for q in CELLS)
        L.append(f"| {c} | {cells} | {r['score']:.1f} | {r.get(2000, {}).get('median_outflow', float('nan')):.0f} |")
    L += ["", "## Tuned (frozen)", ""]
    for fam, tb in res["tuned"].items():
        L.append(f"- **{fam}**: `{tb['ctrl']}` (score {tb['score']:.1f} s)")
    L += ["", f"- Per-cell best (informed reference for a later hybrid gate): {res['per_cell_best']}", "",
          "## Tuned vs NC (paired, median of paired differences in mean time in system, s; negative = better)", ""]
    for fam, cells in res["tuned_vs_nc_paired_time"].items():
        for q, pm in cells.items():
            L.append(f"- {fam} @ q={q}: {pm['median_diff']:+.1f} s [{pm['ci_lo']:+.1f}, {pm['ci_hi']:+.1f}]")
    (REPO_ROOT / "docs" / "lab" / "t1_bn4_r2_baselines.md").write_text("\n".join(L) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--batch-root", default=None)
    a = ap.parse_args(argv)
    root = Path(a.batch_root) if a.batch_root else RUNS_ROOT / "t1" / f"r2_{int(time.time())}"
    if not a.analyse_only:
        jobs = [Job(jid=f"r2_{c.replace(':', '_')}_q{q}_s{s}",
                    argv=["vsl_lab.jobs.bn4_eval", "--ctrl", c, "--inflow", str(q), "--seed", str(s), "--tag", "r2",
                          "--out-root", str(root)])
                for q in CELLS for s in SEEDS for c in controllers()]
        rep = run_batch(jobs, root / "batch", max_workers=a.workers, gate_ok=a.gate_ok)
        print(json.dumps({k: v for k, v in rep.__dict__.items() if k != "results"}), flush=True)
    res = analyse(root)
    (root / "r2_analysis.json").write_text(json.dumps(res, indent=1, default=str))
    write(res, root)
    ledger.append("T1", "R2", "S", "bn4_baselines", {"protocol": "t1_bn4_r2_baselines_protocol.md",
                                                    "controllers": controllers(), "cells": CELLS},
                  "7110100-7110119", res["n_runs"], res["health"],
                  {"tuned": res["tuned"], "per_cell_best": res["per_cell_best"]}, notes=str(root))
    print(json.dumps({"tuned": res["tuned"], "health": res["health"]}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
