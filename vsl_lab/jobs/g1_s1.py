"""G-1 stage S1 (pre-registration docs/lab/g1_s1_prereg.md): narrow band (S1a) and oracle headroom (S1b).

python -m vsl_lab.jobs.g1_s1 a --gate-ok      # S1a NC refinement (320 runs)
python -m vsl_lab.jobs.g1_s1 b --gate-ok      # S1b controllers + timed oracle at the chosen levels
python -m vsl_lab.jobs.g1_s1 report           # -> docs/lab/g1_s1.{json,md}
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import RUNS_ROOT
from vsl_lab.ops.scheduler import Job, run_batch

REPO = Path(__file__).resolve().parents[2]
ROOT = RUNS_ROOT / "g1"
CELLS = {"M3": ("merge", 300, range(5400, 6601, 200)), "M9": ("merge", 900, range(3600, 4201, 200)),
         "Z3": ("zipmerge", 300, range(4800, 6001, 200)), "Z9": ("zipmerge", 900, range(3000, 4201, 200)),
         "L9": ("lanedrop", 900, range(3000, 4201, 200))}
SEEDS_A = range(7170100, 7170110)
SEEDS_B = range(7170200, 7170210)
CONSTS = [0.5, 0.6, 0.7, 0.8, 0.9]
WIN_B, WIN_PRE, WIN_LEN = [0.6, 0.7, 0.8], [300, 900], [1800, 3600]
BOOT_SEED = 7170299


def job(root, cell, m, s, ctrl):
    g, r, _ = CELLS[cell]
    jid = f"{cell}_m{m}_s{s}_{ctrl.replace(':', '~')}"
    return Job(jid, ["vsl_lab.jobs.mrg3_run", "--ctrl", ctrl, "--seed", str(s), "--main-peak", str(m), "--ramp-peak",
                     str(r), "--plant", "v3", "--driver", "H5", "--geom", g, "--tag", jid, "--out-root", str(root)])


def results(root: Path) -> list:
    out = []
    for f in sorted(root.glob("*/batch/batch_report.json")) + sorted(root.glob("batch/batch_report.json")):
        for j in json.loads(f.read_text())["results"]:
            cell, m, s, ctrl = j["jid"].split("_", 3)
            r = j.get("result") or {}
            out.append({"cell": cell, "m": int(m[1:]), "s": int(s[1:]), "ctrl": ctrl.replace("~", ":"),
                        "T": r.get("mean_time_in_system_s"), "cd": r.get("capdrop") or {}, "tele": r.get("teleports"),
                        "thr": r.get("exit_throughput_vph") or r.get("throughput"), "rc": j.get("rc")})
    return out


def chosen_levels(ra: list) -> dict:
    ch = {}
    for cell in CELLS:
        sh = {}
        for x in ra:
            if x["cell"] == cell:
                sh.setdefault(x["m"], []).append(bool(x["cd"].get("breakdown")))
        share = {m: float(np.mean(v)) for m, v in sorted(sh.items())}
        cand = [m for m in share if 0 < share[m] < 1]
        ch[cell] = {"share": share, "level": min(cand, key=lambda m: (abs(share[m] - 0.5), m)) if cand else None}
    return ch


def boot_ci(d: np.ndarray, seed: int = BOOT_SEED, n: int = 10000) -> list:
    rng = np.random.default_rng(seed)
    meds = np.median(d[rng.integers(0, len(d), (n, len(d)))], axis=1)
    return [float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["a", "b", "report"])
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    ra_root, rb_root = ROOT / "s1a", ROOT / "s1b"
    if a.what == "a":
        ra_root.mkdir(parents=True, exist_ok=True)
        jobs = [job(ra_root, c, m, s, "nc") for c, (_, _, ms) in CELLS.items() for m in ms for s in SEEDS_A]
        run_batch(jobs, ra_root / "batch", a.workers, gate_ok=a.gate_ok)
        return 0
    ch = chosen_levels(results(ra_root))
    if a.what == "b":
        rb_root.mkdir(parents=True, exist_ok=True)
        ctrls = ["nc", "mtfc"] + [f"const:{b}" for b in CONSTS]
        jobs = [job(rb_root / "w1", c, v["level"], s, k) for c, v in ch.items() if v["level"] for s in SEEDS_B for k in ctrls]
        run_batch(jobs, rb_root / "w1" / "batch", a.workers, gate_ok=a.gate_ok)
        nc = {(x["cell"], x["s"]): x["cd"].get("onset_t") for x in results(rb_root / "w1") if x["ctrl"] == "nc"}
        jobs = [job(rb_root / "w2", c, ch[c]["level"], s, f"win:{b}:{t0}:{t0 + L}")
                for (c, s), on in nc.items() if on is not None for b in WIN_B for pre in WIN_PRE for L in WIN_LEN
                for t0 in [max(0, int(on) - pre)]]
        run_batch(jobs, rb_root / "w2" / "batch", a.workers, gate_ok=a.gate_ok)
        return 0
    rb = results(rb_root / "w1") + results(rb_root / "w2")
    rep = {"chosen": ch, "cells": {}}
    for c, v in ch.items():
        if not v["level"]:
            continue
        X = [x for x in rb if x["cell"] == c and x["T"] is not None]
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
        dif = (b - o2) / b
        H, ci = float(np.median(dif)), boot_ci(dif)
        ratios = [x["cd"].get("ratio") for x in results(ra_root) if x["cell"] == c and x["cd"].get("breakdown")]
        rep["cells"][c] = {"level": v["level"], "median_T": med, "tuned_const": tuned, "BNL": bnl,
                           "O1_median": float(np.median(o1)), "O2_median": float(np.median(o2)), "H": H, "H_ci": ci,
                           "verdict": "KILL" if H < 0.10 or ci[0] <= 0 else "HEADROOM (oracle)",
                           "teleport_runs": sum(1 for x in X if (x["tele"] or 0) > 0), "n_runs": len(X),
                           "s1a_discharge_ratio_median": float(np.median(ratios)) if ratios else None}
    (REPO / "docs/lab/g1_s1.json").write_text(json.dumps(rep, indent=1))
    L = ["# G-1 S1: narrow band and oracle headroom (H5)", "", "Pre-registration `g1_s1_prereg.md`. Metric: mean "
         "door-to-door time (s). Oracles cheat on purpose (upper bounds; H biased upwards).", "",
         "| cell | level | nc | tuned const | mtfc (untuned) | BNL | O1 | O2 | H [95 % CI] | verdict | discharge ratio (S1a) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c, r in rep["cells"].items():
        m = r["median_T"]
        L.append(f"| {c} | {r['level']} | {m['nc']:.0f} | {m[r['tuned_const']]:.0f} ({r['tuned_const']}) | {m['mtfc']:.0f} | "
                 f"{r['BNL']} | {r['O1_median']:.0f} | {r['O2_median']:.0f} | {100*r['H']:.1f} % "
                 f"[{100*r['H_ci'][0]:.1f}, {100*r['H_ci'][1]:.1f}] | **{r['verdict']}** | "
                 f"{r['s1a_discharge_ratio_median'] and round(r['s1a_discharge_ratio_median'], 3)} |")
    L += ["", "Breakdown share per level (S1a, 10 seeds): " + json.dumps({c: v["share"] for c, v in ch.items()})]
    (REPO / "docs/lab/g1_s1.md").write_text("\n".join(L) + "\n")
    print(json.dumps({c: (r["H"], r["verdict"]) for c, r in rep["cells"].items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
