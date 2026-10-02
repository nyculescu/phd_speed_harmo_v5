"""Track 1 / R5 head-to-head per docs/lab/t1_bn4_r5_protocol.md.

python -m vsl_lab.jobs.t1_r5_eval --models PATH[:algo] [PATH[:algo] ...] --tag r5_<candidate> --gate-ok
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

SEEDS = list(range(7110500, 7110530))
CELLS = [1200, 1600, 2000, 2400]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True, help="model.zip[:algo] per learner seed")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--env-kwargs", default="{}")
    ap.add_argument("--seeds", default=None, help="a-b inclusive test seeds (default 7110500-7110529)")
    ap.add_argument("--frozen", default="docs/lab/t1_bn4_baselines_frozen.json")
    ap.add_argument("--plant-kwargs", default="{}", help="env kwargs for EVERY controller (e.g. av_share 0.25, B-R5)")
    a = ap.parse_args(argv)
    global SEEDS
    if a.seeds:
        SEEDS = list(range(int(a.seeds.split("-")[0]), int(a.seeds.split("-")[1]) + 1))
    fz = json.loads((REPO_ROOT / a.frozen).read_text())
    comps = ["nc"] + [fz["tuned"][f]["ctrl"] for f in ("cap", "avfb", "meter") if f in fz["tuned"]]
    drl = [f"rl:{m}" if ":" in m else f"rl:{m}:ppo" for m in a.models]
    root = RUNS_ROOT / "t1" / f"{a.tag}_{int(time.time())}"
    jobs = []
    for q in CELLS:
        for s in SEEDS:
            for i, c in enumerate(comps + drl):
                lab = c if not c.startswith("rl:") else f"drl{i - len(comps)}"
                jobs.append(Job(jid=f"r5_{lab.replace(':', '_')}_q{q}_s{s}",
                                argv=["vsl_lab.jobs.bn4_eval", "--ctrl", c, "--inflow", str(q), "--seed", str(s),
                                      "--tag", lab.replace(":", "_"), "--out-root", str(root),
                                      "--env-kwargs", json.dumps(json.loads(a.plant_kwargs)
                                                                 | (json.loads(a.env_kwargs) if c.startswith("rl:") else {}))]))
    rep = run_batch(jobs, root / "batch", max_workers=a.workers, gate_ok=a.gate_ok)
    data = {}
    for p in root.glob("*/*.json"):
        if p.parent.name == "batch":
            continue
        o = json.loads(p.read_text())
        data.setdefault(p.parent.name, {})[(int(o["inflow"]), o["seed"])] = o
    drl_labels = sorted(k for k in data if k.startswith("drl"))
    out = {"cells": {}, "health": {}}
    for k, d in data.items():
        out["health"][k] = {h: sum(1 for o in d.values() if o["health"] == h) for h in ("PASS", "WARN", "FAIL")}
    for q in CELLS:
        cell = {}
        for comp in comps:
            ck = comp.replace(":", "_")
            base = data.get(ck, {})
            res = {}
            for dl in drl_labels + ["drl_pooled"]:
                if dl == "drl_pooled":
                    x, y = [], []
                    for s in SEEDS:
                        vals = [data[d][(q, s)]["mean_time_in_system_s"] for d in drl_labels if (q, s) in data[d]]
                        if vals and (q, s) in base:
                            y.append(float(np.median(vals)))
                            x.append(base[(q, s)]["mean_time_in_system_s"])
                else:
                    ss = [s for s in SEEDS if (q, s) in base and (q, s) in data[dl]]
                    x = [base[(q, s)]["mean_time_in_system_s"] for s in ss]
                    y = [data[dl][(q, s)]["mean_time_in_system_s"] for s in ss]
                if x:
                    pm = paired_median_diff(x, y, seed=7110529)
                    pm["rel"] = pm["median_diff"] / float(np.median(x))
                    res[dl] = pm
            cell[comp] = res
        out["cells"][q] = cell
    (root / "r5_analysis.json").write_text(json.dumps(out, indent=1, default=str))
    L = [f"# T1 R5 head-to-head: {a.tag}", "", f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol "
         f"`docs/lab/t1_bn4_r5_protocol.md` · test seeds {SEEDS[0]}-{SEEDS[-1]} · raw `{root}`*", "",
         "Median of paired differences in door-to-door time (DRL − comparator, s; negative = DRL better) [95 % CI].", ""]
    for q in CELLS:
        L += [f"## q = {q} veh/h", "", "| comparator | " + " | ".join(drl_labels + ["drl_pooled"]) + " |",
              "|---|" + "---|" * (len(drl_labels) + 1)]
        for comp in comps:
            r = out["cells"][q][comp]
            L.append(f"| {comp} | " + " | ".join(
                f"{r[d]['median_diff']:+.1f} [{r[d]['ci_lo']:+.1f}, {r[d]['ci_hi']:+.1f}] ({r[d]['rel']:+.1%})" if d in r else "-"
                for d in drl_labels + ["drl_pooled"]) + " |")
        L.append("")
    L += ["## Health", "", json.dumps(out["health"])]
    (REPO_ROOT / "docs" / "lab" / f"{a.tag}.md").write_text("\n".join(L) + "\n")
    ledger.append("T1", "R5", "S", a.tag, {"models": a.models, "comps": comps, "plant_kwargs": a.plant_kwargs}, f"{SEEDS[0]}-{SEEDS[-1]}", rep.n_jobs,
                  {k: sum(v[k] for v in out["health"].values()) for k in ("PASS", "WARN", "FAIL")},
                  {str(q): {c: {d: round(v["rel"], 4) for d, v in r.items()} for c, r in cell.items()}
                   for q, cell in out["cells"].items()}, notes=str(root))
    print(json.dumps({"report": f"docs/lab/{a.tag}.md"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
