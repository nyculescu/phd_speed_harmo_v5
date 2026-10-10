"""G-1 stage S2: Z9 follow-up, 30 seeds (pre-registration docs/lab/g1_s2_prereg.md).

python -m vsl_lab.jobs.g1_s2 run --gate-ok   # controllers, then timed-oracle windows
python -m vsl_lab.jobs.g1_s2 report          # -> docs/lab/g1_s2.{json,md}
"""
from __future__ import annotations

import argparse
import json
import sys

import numpy as np

from vsl_lab.jobs.g1_s1 import CONSTS, REPO, ROOT, WIN_B, WIN_LEN, WIN_PRE, boot_ci, job, results
from vsl_lab.ops.scheduler import run_batch

CELL, LEVEL = "Z9", 3600
SEEDS = range(7170300, 7170330)
BOOT = 7170399


def H(b: np.ndarray, o: np.ndarray) -> tuple:
    d = (b - o) / b
    return float(np.median(d)), boot_ci(d, seed=BOOT)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["run", "report"])
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    root = ROOT / "s2"
    if a.what == "run":
        ctrls = ["nc", "mtfc"] + [f"const:{b}" for b in CONSTS]
        run_batch([job(root / "w1", CELL, LEVEL, s, k) for s in SEEDS for k in ctrls], root / "w1" / "batch", a.workers,
                  gate_ok=a.gate_ok)
        nc = {x["s"]: x["cd"].get("onset_t") for x in results(root / "w1") if x["ctrl"] == "nc"}
        jobs = [job(root / "w2", CELL, LEVEL, s, f"win:{b}:{t0}:{t0 + L}") for s, on in nc.items() if on is not None
                for b in WIN_B for pre in WIN_PRE for L in WIN_LEN for t0 in [max(0, int(on) - pre)]]
        run_batch(jobs, root / "w2" / "batch", a.workers, gate_ok=a.gate_ok)
        return 0
    X = [x for x in results(root / "w1") + results(root / "w2") if x["T"] is not None]
    per = {}
    for x in X:
        per.setdefault(x["ctrl"], {})[x["s"]] = x["T"]
    seeds = sorted(per["nc"])
    med = {k: float(np.median([d[s] for s in seeds if s in d])) for k, d in per.items() if not k.startswith("win")}
    tuned = min((k for k in med if k.startswith("const")), key=med.get)
    bnl = min(["nc", tuned, "mtfc"], key=med.get)
    o1 = np.array([min(per[k][s] for k in ["nc"] + [f"const:{b}" for b in CONSTS] if s in per[k]) for s in seeds])
    o2 = np.array([min([o1[i]] + [d[s] for k, d in per.items() if k.startswith("win") and s in d])
                   for i, s in enumerate(seeds)])
    b = np.array([per[bnl][s] for s in seeds])
    h, ci = H(b, o2)
    jam = np.array([any(x["s"] == s and x["ctrl"] == "nc" and x["cd"].get("breakdown") for x in X) for s in seeds])
    hj, cij = H(b[jam], o2[jam]) if jam.sum() >= 3 else (None, None)
    rep = {"median_T": med, "tuned_const": tuned, "BNL": bnl, "O1_median": float(np.median(o1)),
           "O2_median": float(np.median(o2)), "H": h, "H_ci": ci, "ratio_of_medians": 1 - float(np.median(o2)) / med[bnl],
           "verdict": "KILL" if h < 0.10 or ci[0] <= 0 else "HEADROOM (oracle)", "n_seeds": len(seeds),
           "n_jam_seeds": int(jam.sum()), "H_jam": hj, "H_jam_ci": cij,
           "teleport_runs": sum(1 for x in X if (x["tele"] or 0) > 0), "n_runs": len(X)}
    (REPO / "docs/lab/g1_s2.json").write_text(json.dumps(rep, indent=1))
    m = rep["median_T"]
    L = ["# G-1 S2: Z9 follow-up (30 seeds)", "", "Pre-registration `g1_s2_prereg.md`. Mean door-to-door time (s), medians.", "",
         f"- nc {m['nc']:.0f} · tuned const {m[tuned]:.0f} ({tuned}) · mtfc {m['mtfc']:.0f} · BNL = {bnl} · "
         f"O1 {rep['O1_median']:.0f} · O2 {rep['O2_median']:.0f}",
         f"- **H = {100*h:.1f} % [{100*ci[0]:.1f}, {100*ci[1]:.1f}] → {rep['verdict']}** "
         f"(ratio of medians, report-only: {100*rep['ratio_of_medians']:.1f} %)",
         f"- Report-only H_jam ({rep['n_jam_seeds']} NC-breakdown seeds): "
         + (f"{100*hj:.1f} % [{100*cij[0]:.1f}, {100*cij[1]:.1f}]" if hj is not None else "n/a"),
         f"- Runs {rep['n_runs']}, runs with teleports {rep['teleport_runs']}"]
    (REPO / "docs/lab/g1_s2.md").write_text("\n".join(L) + "\n")
    print(json.dumps({k: rep[k] for k in ("H", "H_ci", "verdict", "H_jam", "n_jam_seeds")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
