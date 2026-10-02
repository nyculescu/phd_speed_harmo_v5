"""R0.4 thermal calibration: find N_max = largest worker count with steady package temp <= 87 C
and no thermal pauses, on sustained BN4 simulation load. Results are not used for anything else.

Run: python -m vsl_lab.ops.calibrate_thermal --gate-ok
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from vsl_lab.config import RUNS_ROOT
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch
from vsl_lab.ops.thermal import package_temp_c

STEADY_MAX_C = 87.0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--levels", type=int, nargs="+", default=[8, 16, 24, 32, 48])
    ap.add_argument("--window-s", type=float, default=150.0)
    ap.add_argument("--cooldown-s", type=float, default=45.0)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    root = RUNS_ROOT / "ops" / f"thermal_cal_{int(time.time())}"
    seeds = list(range(7110000, 7110010))  # track-1 throw-away calibration seeds (heat only)
    rows, n_max = [], None
    for n in a.levels:
        def factory(k, n=n):
            s = seeds[k % len(seeds)]
            return Job(jid=f"n{n}_k{k}", argv=["vsl_lab.jobs.bn4_nc", "--inflow", "2000", "--seed", str(s),
                                                "--t-demand", "6000", "--t-max", "9000", "--window", "5000", "6000",
                                                "--tag", f"thermal_cal_n{n}", "--out-root", str(root)])
        rep = run_batch([], root / f"n{n}", max_workers=n, gate_ok=a.gate_ok, time_budget_s=a.window_s,
                        job_factory=factory)
        import csv
        with open(root / f"n{n}" / "thermal.csv") as f:
            th = list(csv.DictReader(f))
        tail = [float(r["temp_c"]) for r in th if float(r["wall_s"]) >= a.window_s - 60.0 and r["temp_c"] != "nan"]
        steady = round(sum(tail) / max(len(tail), 1), 1)
        sim_s = sum((r["result"] or {}).get("sim_per_wall", 0) * (r["wall"] or 0) for r in rep.results)
        row = {"n": n, "steady_c": steady, "max_c": rep.max_temp_c, "pauses": rep.n_pauses,
               "jobs": rep.n_jobs, "failed": rep.n_failed_proc, "sim_s_per_wall_s": round(sim_s / rep.wall_s, 0)}
        rows.append(row)
        print(json.dumps(row), flush=True)
        if steady <= STEADY_MAX_C and rep.n_pauses == 0:
            n_max = n
        else:
            break
        t_cool = time.time()
        while time.time() - t_cool < a.cooldown_s and package_temp_c() > 70:
            time.sleep(2)
    out = {"levels": rows, "n_max": n_max, "rule": f"steady (last 60 s) <= {STEADY_MAX_C} C and 0 pauses",
           "plant": "BN4 NC, inflow 2000, 0.5 s step"}
    (root / "thermal_calibration.json").write_text(json.dumps(out, indent=1))
    ledger.append("ops", "R0.4", "S", "thermal_calibration", {"levels": a.levels, "window_s": a.window_s},
                  "7110000-7110009 (heat only)", sum(r["jobs"] for r in rows),
                  {"PASS": sum(r["jobs"] - r["failed"] for r in rows), "FAIL": sum(r["failed"] for r in rows)},
                  {"n_max": n_max, "levels": rows}, notes=str(root))
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
