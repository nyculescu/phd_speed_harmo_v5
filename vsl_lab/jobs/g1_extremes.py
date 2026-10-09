"""G-1 stage S0: demand extremes on the 3-lane SUMO merge (pre-registration docs/lab/g1_demand_extremes_prereg.md).

python -m vsl_lab.jobs.g1_extremes smoke --gate-ok      # one run on 7,170,000 (timing only)
python -m vsl_lab.jobs.g1_extremes run --gate-ok        # 288 runs
python -m vsl_lab.jobs.g1_extremes report <batch_root>  # -> docs/lab/g1_demand_extremes.{json,md}
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from vsl_lab.config import RUNS_ROOT
from vsl_lab.ops.scheduler import Job, run_batch

REPO = Path(__file__).resolve().parents[2]
GEOMS = ["merge", "lanedrop", "zipmerge"]
DRIVERS = ["H5", "H3"]
MAIN = [3000, 3600, 4200, 4800, 5400, 6000, 6600, 7200]
RAMP = [300, 900, 1500]
SEEDS = [7170010, 7170011]
SMOKE_SEED = 7170000


def job(root: Path, g: str, drv: str, m: int, r: int, s: int) -> Job:
    jid = f"{g}_{drv}_m{m}_r{r}_s{s}"
    return Job(jid, ["vsl_lab.jobs.mrg3_run", "--ctrl", "nc", "--seed", str(s), "--main-peak", str(m), "--ramp-peak",
                     str(r), "--plant", "v3", "--driver", drv, "--geom", g, "--tag", jid, "--out-root", str(root)])


def report(root: Path) -> dict:
    rows = {}
    res = json.loads((root / "batch" / "batch_report.json").read_text())
    for j in res["results"]:
        g, drv, m, r, s = j["jid"].split("_")
        rr = j.get("result") or {}
        cd = rr.get("capdrop") or {}
        key = f"{g}|{drv}|{r[1:]}"
        rows.setdefault(key, {}).setdefault(int(m[1:]), []).append(
            {"breakdown": cd.get("breakdown"), "ratio": cd.get("ratio"), "teleports": rr.get("teleports"),
             "drained": rr.get("drained"), "ok": j.get("rc") == 0})
    out = {}
    for key, by_m in rows.items():
        share = {m: (sum(bool(x["breakdown"]) for x in v) / len(v)) for m, v in sorted(by_m.items())}
        ratios = [x["ratio"] for v in by_m.values() for x in v if x["breakdown"] and x["ratio"] is not None]
        tele = sum(1 for v in by_m.values() for x in v if (x["teleports"] or 0) > 0)
        n = sum(len(v) for v in by_m.values())
        ms = sorted(share)
        mixed = [m for m in ms if 0 < share[m] < 1]
        free = [m for m in ms if share[m] == 0]
        jam = [m for m in ms if share[m] == 1]
        lo = max([m for m in free if not jam or m < min(jam)], default=None)
        hi = min([m for m in jam if not free or m > max(free)], default=None)
        out[key] = {"share": share, "mixed": mixed, "bracket": [lo, hi], "n": n, "runs_with_teleports": tele,
                    "ratio_median": (sorted(ratios)[len(ratios) // 2] if ratios else None), "n_ratio": len(ratios),
                    "failed_runs": sum(1 for v in by_m.values() for x in v if not x["ok"])}
    return out


def write_report(root: Path) -> None:
    out = report(root)
    (REPO / "docs/lab/g1_demand_extremes.json").write_text(json.dumps({"root": str(root), "cells": out}, indent=1))
    L = ["# G-1 S0: demand extremes (3-lane SUMO merge, NC)", "", f"raw `{root}` · pre-registration "
         "`g1_demand_extremes_prereg.md`", "", "Breakdown share per main_peak (veh/h; 2 seeds each). Bracket = "
         "[last all-free, first all-jammed].", "",
         "| layout · driver · ramp | " + " | ".join(str(m) for m in MAIN) + " | bracket | median discharge ratio (n) | runs w/ teleports |",
         "|---" * (len(MAIN) + 4) + "|"]
    for key in sorted(out):
        c = out[key]
        L.append(f"| {key.replace('|', ' · ')} | " + " | ".join(f"{c['share'].get(m, float('nan')):.1f}" for m in MAIN)
                 + f" | {c['bracket']} | {c['ratio_median'] and round(c['ratio_median'], 3)} ({c['n_ratio']}) | "
                 f"{c['runs_with_teleports']}/{c['n']} |")
    (REPO / "docs/lab/g1_demand_extremes.md").write_text("\n".join(L) + "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["smoke", "run", "report"])
    ap.add_argument("root", nargs="?")
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "report":
        write_report(Path(a.root))
        return 0
    root = RUNS_ROOT / "g1" / f"s0_{a.what}_{int(time.time())}"
    root.mkdir(parents=True, exist_ok=True)
    if a.what == "smoke":
        jobs = [job(root, "lanedrop", "H5", 6000, 900, SMOKE_SEED)]
    else:
        jobs = [job(root, g, d, m, r, s) for g in GEOMS for d in DRIVERS for m in MAIN for r in RAMP for s in SEEDS]
    run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    print(json.dumps({"root": str(root), "n_jobs": len(jobs)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
