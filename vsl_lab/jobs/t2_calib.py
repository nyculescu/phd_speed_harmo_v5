"""Track 2 / MRG3 calibration per docs/lab/t2_mrg3_r1_protocol.md (throw-away seeds 7,120,000-7,120,009; disclosed).

NC at main_peak in {4800, 5100, 5400, 5700, 6000} x ramp_peak in {600, 900} x 10 seeds; records breakdown share,
capacity-drop ratio, teleports, health; applies the pre-registered cell-selection rule.
"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

MAIN = [4800, 5100, 5400, 5700, 6000]
RAMP = [600, 900]
SEEDS = list(range(7120000, 7120010))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    root = RUNS_ROOT / "t2" / f"calib_{int(time.time())}"
    jobs = [Job(jid=f"cal_m{m}_r{r}_s{s}", argv=["vsl_lab.jobs.mrg3_run", "--ctrl", "nc", "--seed", str(s),
                                                  "--main-peak", str(m), "--ramp-peak", str(r), "--tag", "calib",
                                                  "--out-root", str(root)])
            for m in MAIN for r in RAMP for s in SEEDS]
    rep = run_batch(jobs, root / "batch", max_workers=a.workers, gate_ok=a.gate_ok)
    rows = [json.loads(p.read_text()) for p in (root / "calib").glob("*/summary.json")]
    cells = {}
    for o in rows:
        k = (int(o["main_peak"]), int(o["ramp_peak"]))
        c = cells.setdefault(k, {"n": 0, "breakdown": 0, "ratios": [], "teleports": 0, "fail": 0, "time": []})
        c["n"] += 1
        cd = o.get("capdrop") or {}
        if cd.get("breakdown"):
            c["breakdown"] += 1
            if cd.get("ratio") == cd.get("ratio"):
                c["ratios"].append(cd["ratio"])
        c["teleports"] += o["teleports"]
        c["fail"] += o["health"]["status"] == "FAIL"
        c["time"].append(o["mean_time_in_system_s"])
    table = {f"{m}/{r}": {"n": c["n"], "breakdown_share": c["breakdown"] / max(c["n"], 1),
                          "median_ratio": float(np.median(c["ratios"])) if c["ratios"] else None,
                          "share_ratio_le_095": float(np.mean([x <= 0.95 for x in c["ratios"]])) if c["ratios"] else None,
                          "teleports": c["teleports"], "fail": c["fail"], "median_time_s": float(np.median(c["time"]))}
             for (m, r), c in sorted(cells.items())}
    ok = {k: v for k, v in table.items() if v["teleports"] == 0 and v["fail"] == 0}
    sel = None
    if ok:
        sel = min(ok, key=lambda k: (abs(ok[k]["breakdown_share"] - 0.5),
                                     sum(int(x) for x in k.split("/"))))
    out = {"table": table, "selected_cell": sel,
           "rule": "closest breakdown share to 0.5 among cells with 0 teleports and 0 FAIL; ties -> lower demand",
           "n_runs": len(rows), "raw": str(root)}
    (REPO_ROOT / "docs" / "lab" / "t2_mrg3_calibration.json").write_text(json.dumps(out, indent=1))
    ledger.append("T2", "R1-calib", "S", "mrg3_calibration", {"main": MAIN, "ramp": RAMP}, "7120000-7120009 (throw-away)",
                  len(rows), {"PASS": rep.n_ok}, {"selected": sel, "table": table}, notes=str(root))
    print(json.dumps({"selected": sel, "table": table}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
