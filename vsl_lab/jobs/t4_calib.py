"""T4 CORR2 calibration (docs/lab/t4_corr2_protocol.md). python -m vsl_lab.jobs.t4_calib --gate-ok"""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

QM, QR1, QR2 = [4000, 4500], [300, 600], [1200, 1500, 1800]
SEEDS = [7140001, 7140002, 7140003]


def minutes_below(run_dir: Path, col: str, v_kmh: float = 60.0) -> float:
    rows = list(csv.DictReader(open(run_dir / "features.csv")))
    return 0.5 * sum(1 for r in rows if r.get(col) not in (None, "") and 0 <= float(r[col]) < v_kmh)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    root = RUNS_ROOT / "t4" / f"calib_{int(time.time())}"
    jobs = [Job(jid=f"c_m{m}_r{r1}_{r2}_s{s}", argv=["vsl_lab.jobs.corr_run", "--ctrl", "nc", "--seed", str(s), "--q-main", str(m),
                                                     "--q-r1", str(r1), "--q-r2", str(r2), "--stops", "--tag", "calib",
                                                     "--out-root", str(root)])
            for m in QM for r1 in QR1 for r2 in QR2 for s in SEEDS]
    run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    cells = {}
    for p in (root / "calib").glob("*/summary.json"):
        o = json.loads(p.read_text())
        k = f"{int(o['q_main'])}/{int(o['q_r1'])}/{int(o['q_r2'])}"
        c = cells.setdefault(k, {"block_min": [], "m4_min": [], "tele": 0, "fail": 0, "t_sys": [], "off_users": []})
        c["block_min"].append(minutes_below(p.parent, "m3_v"))
        c["m4_min"].append(minutes_below(p.parent, "m4_v"))
        c["tele"] += o["teleports"]
        c["fail"] += o["health"]["status"] == "FAIL"
        c["t_sys"].append(o["mean_time_in_system_s"])
        dd = o.get("door_to_door") or {}
        c["off_users"].append(next((v.get("mean_s") for kk, v in dd.items() if "off" in kk and isinstance(v, dict)), None))
    table = {k: {"block_min": c["block_min"], "m4_min": c["m4_min"], "teleports": c["tele"], "fail": c["fail"],
                 "median_t_sys": float(np.median(c["t_sys"])), "off_users_s": c["off_users"],
                 "n_block_ge5": sum(x >= 5 for x in c["block_min"])} for k, c in sorted(cells.items())}
    ok = [k for k, v in table.items() if v["teleports"] == 0 and v["fail"] == 0 and v["n_block_ge5"] >= 2]
    sel = min(ok, key=lambda k: sum(int(x) for x in k.split("/"))) if ok else max(
        table, key=lambda k: float(np.median(table[k]["block_min"])))
    out = {"table": table, "selected": sel, "flagged": not bool(ok), "raw": str(root)}
    (REPO_ROOT / "docs/lab/t4_corr2_calibration.json").write_text(json.dumps(out, indent=1, default=str))
    ledger.append("T4", "R1-calib", "S", "corr2_calibration", {"grid": [QM, QR1, QR2]}, "7140001-7140003 (throw-away)",
                  len(jobs), {}, {"selected": sel, "flagged": out["flagged"]}, notes=str(root))
    print(json.dumps({"selected": sel, "flagged": out["flagged"],
                      "block_min": {k: v["block_min"] for k, v in table.items()}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
