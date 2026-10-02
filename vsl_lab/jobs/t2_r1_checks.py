"""Track 2 / R1 plant checks on MRG3 per docs/lab/t2_mrg3_r1_protocol.md (cell from docs/lab/t2_mrg3_calibration.json).

python -m vsl_lab.jobs.t2_r1_checks --workers 10 --gate-ok
"""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.eval.stats import paired_median_diff
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

T1_SEEDS = list(range(7120010, 7120040))
T0_SEEDS = list(range(7120040, 7120050))
T1C = ["const:0.6", "const:0.8", "mtfc:32:38:9:0.0015", "mtfc:25:38:9:0.0015", "mtfc:20:38:9:0.0015"]


def job(tag, ctrl, s, m, r, root):
    return Job(jid=f"{tag}_{ctrl.replace(':', '_')}_s{s}",
               argv=["vsl_lab.jobs.mrg3_run", "--ctrl", ctrl, "--seed", str(s), "--main-peak", str(m), "--ramp-peak", str(r),
                     "--tag", tag, "--out-root", str(root)])


def load(root: Path, tag: str) -> dict:
    out = {}
    for p in (root / tag).glob("*/summary.json"):
        o = json.loads(p.read_text())
        out.setdefault(o["ctrl"], {})[o["seed"]] = o
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--batch-root", default=None)
    a = ap.parse_args(argv)
    cal = json.loads((REPO_ROOT / "docs/lab/t2_mrg3_calibration.json").read_text())
    cell = cal["selected_cell"]
    m, r = (int(x) for x in cell.split("/"))
    root = Path(a.batch_root) if a.batch_root else RUNS_ROOT / "t2" / f"r1_{int(time.time())}"
    if not a.analyse_only:
        jobs = [job("t1", "nc", s, m, r, root) for s in T1_SEEDS]
        jobs += [job("t1c", c, s, m, r, root) for c in T1C for s in T1_SEEDS]
        jobs += [job("t0", c, s, m, r, root) for c in ("nc", "const:0.4") for s in T0_SEEDS]
        run_batch(jobs, root / "batch", max_workers=a.workers, gate_ok=a.gate_ok)
        picks = random.Random(7120099).sample(T1_SEEDS, 5)
        run_batch([job("t3", "nc", s, m, r, root) for s in picks], root / "batch_t3", max_workers=a.workers, gate_ok=True)
    nc = load(root, "t1").get("nc", {})
    res = {"cell": cell}
    bd = [o for o in nc.values() if (o.get("capdrop") or {}).get("breakdown")]
    ratios = [o["capdrop"]["ratio"] for o in bd if o["capdrop"].get("ratio") == o["capdrop"].get("ratio")]
    tele = sum(o["teleports"] for o in nc.values())
    fails = sum(o["health"]["status"] == "FAIL" for o in nc.values())
    t1_pass = (len(bd) / max(len(nc), 1) >= 0.3 and ratios and np.mean([x <= 0.95 for x in ratios]) >= 2 / 3
               and tele == 0 and fails == 0)
    res["T1"] = {"n": len(nc), "breakdown_share": len(bd) / max(len(nc), 1), "median_ratio": float(np.median(ratios)) if ratios else None,
                 "share_ratio_le_095": float(np.mean([x <= 0.95 for x in ratios])) if ratios else None,
                 "teleports": tele, "fail": fails, "PASS": bool(t1_pass)}
    t1c = load(root, "t1c")
    cm = {}
    any_ok = False
    for c in T1C:
        d = t1c.get(c, {})
        ss = sorted(set(nc) & set(d))
        if not ss:
            continue
        pm = paired_median_diff([nc[s]["mean_time_in_system_s"] for s in ss], [d[s]["mean_time_in_system_s"] for s in ss],
                                seed=7120039)
        ref = float(np.median([nc[s]["mean_time_in_system_s"] for s in ss]))
        rel = pm["median_diff"] / ref
        ok = rel <= -0.05 and pm["excludes_0"]
        any_ok = any_ok or ok
        ramp = paired_median_diff([nc[s]["time_ramp_s"] for s in ss], [d[s]["time_ramp_s"] for s in ss], seed=7120039)
        cm[c] = {"rel": round(rel, 4), "paired": pm, "ok": ok, "ramp_paired": ramp,
                 "median_min_b": float(np.median([d[s]["min_b"] for s in ss]))}
    res["T1c"] = {"per_ctrl": cm, "PASS": any_ok}
    t0 = load(root, "t0")
    a0, b0 = t0.get("nc", {}), t0.get("const:0.4", {})
    ss = sorted(set(a0) & set(b0))
    # application-area outflow at peak demand: up0a 30 s loop flow per lane from features.csv over [1500, 2700)
    import csv
    def up0a_q(root_tag, o):
        p = root / root_tag / o["run_id"] / "features.csv"
        rows = list(csv.DictReader(open(p)))
        v = [float(rw["up0a_q"]) for rw in rows if 1500.0 <= float(rw["t"]) < 2700.0]
        return float(np.mean(v)) if v else float("nan")
    if ss:
        x = [up0a_q("t0", a0[s]) for s in ss]
        y = [up0a_q("t0", b0[s]) for s in ss]
        pm = paired_median_diff(x, y, seed=7120049)
        rel = pm["median_diff"] / float(np.median(x))
        res["T0"] = {"rel": round(rel, 4), "paired": pm, "PASS": bool(rel <= -0.10 and pm["excludes_0"])}
    t3 = load(root, "t3").get("nc", {})
    if t3:
        same = [t3[s]["hash"] == nc[s]["hash"] for s in t3 if s in nc]
        res["T3"] = {"n": len(same), "PASS": all(same) and len(same) == 5}
    (root / "analysis.json").write_text(json.dumps(res, indent=1, default=str))
    L = ["# Track 2 (MRG3), R1 plant checks: results", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/t2_mrg3_r1_protocol.md` · cell {cell} · raw `{root}`*", "",
         f"## T1 capacity drop: **{'PASS' if res['T1']['PASS'] else 'FAIL'}**", "", f"- {json.dumps(res['T1'])}", "",
         f"## T1c control matters: **{'PASS' if res['T1c']['PASS'] else 'FAIL'}**", "",
         "| controller | rel. Δ door-to-door vs NC | 95 % CI (s) | ramp users Δ (s) | median min b |", "|---|---|---|---|---|"]
    for c, v in cm.items():
        L.append(f"| {c} | {v['rel']:+.1%} | [{v['paired']['ci_lo']:+.1f}, {v['paired']['ci_hi']:+.1f}] | "
                 f"{v['ramp_paired']['median_diff']:+.1f} | {v['median_min_b']} |")
    if "T0" in res:
        L += ["", f"## T0 actuator binds: **{'PASS' if res['T0']['PASS'] else 'FAIL'}** (application-area outflow "
              f"{res['T0']['rel']:+.1%} at b = 0.4)"]
    if "T3" in res:
        L += ["", f"## T3 determinism: **{'PASS' if res['T3']['PASS'] else 'FAIL'}**"]
    (REPO_ROOT / "docs" / "lab" / "t2_mrg3_r1.md").write_text("\n".join(L) + "\n")
    ledger.append("T2", "R1", "S", "mrg3_r1", {"cell": cell}, "7120010-7120049",
                  len(nc) + sum(len(v) for v in t1c.values()) + len(ss) * 2,
                  {"FAIL": fails}, {k: res[k].get("PASS") for k in ("T1", "T1c", "T0", "T3") if k in res}, notes=str(root))
    print(json.dumps({k: res[k].get("PASS") for k in ("T1", "T1c", "T0", "T3") if k in res}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
