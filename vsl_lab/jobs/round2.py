"""Round 2 batches per docs/lab/round2_protocol.md.

python -m vsl_lab.jobs.round2 a_t0 --gate-ok    # posted VSL binds?
python -m vsl_lab.jobs.round2 a_r2 --gate-ok    # tune constant VSL / MTFC-BN4 (+ meter reference)
python -m vsl_lab.jobs.round2 b_r2 --gate-ok    # 25 % AVs: tune NC / caps / avfb (+ meter reference)
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
MTFC_RHO = [20, 30, 40, 50, 60, 70]
MTFC_GAINS = [(38, 9, 0.0015), (76, 18, 0.003)]


def ctrls_a() -> list:
    out = ["nc"] + [f"vsl:{b}:0.9" for b in (0.3, 0.4, 0.5, 0.6, 0.8)]
    out += [f"mtfcb:{r}:{kp}:{ki}:{ki2}" for r in MTFC_RHO for kp, ki, ki2 in MTFC_GAINS]
    return out + ["meter:10:6"]


def ctrls_b() -> list:
    out = ["nc", "cap:9", "cap:13", "cap:18"]
    out += [f"avfb:{k:g}:{n}" for k in (0.5, 1.0, 2.0) for n in (4, 6, 8, 10)]
    return out + ["meter:10:6"]


def jobs_for(tag, ctrls, cells, seeds, root, env_kwargs):
    return [Job(jid=f"{tag}_{c.replace(':', '_')}_q{q}_s{s}",
                argv=["vsl_lab.jobs.bn4_eval", "--ctrl", c, "--inflow", str(q), "--seed", str(s), "--tag", tag,
                      "--out-root", str(root), "--env-kwargs", json.dumps(env_kwargs)])
            for q in cells for s in seeds for c in ctrls]


def load(root: Path, tag: str) -> dict:
    by = {}
    for p in (root / tag).glob("*.json"):
        o = json.loads(p.read_text())
        by.setdefault((o["ctrl"], int(o["inflow"])), {})[o["seed"]] = o
    return by


def tune(by: dict, ctrls: list, cells: list) -> dict:
    table = {}
    for c in ctrls:
        row = {q: float(np.median([o["mean_time_in_system_s"] for o in by.get((c, q), {}).values()]))
               for q in cells if by.get((c, q))}
        if len(row) == len(cells):
            row["score"] = float(np.mean([row[q] for q in cells]))
            table[c] = row
    fams = {}
    for c in table:
        fams.setdefault(c.split(":")[0], []).append(c)
    tuned = {f: {"ctrl": min(cs, key=lambda c: table[c]["score"]), "score": min(table[c]["score"] for c in cs)}
             for f, cs in fams.items()}
    return {"table": table, "tuned": tuned}


def health(by: dict) -> dict:
    h = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for d in by.values():
        for o in d.values():
            h[o["health"]] = h.get(o["health"], 0) + 1
    return h


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["a_t0", "a_r2", "b_r2"])
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    root = RUNS_ROOT / "t1" / f"round2_{a.what}_{int(time.time())}"
    if a.what == "a_t0":
        seeds = list(range(7110050, 7110060))
        cells = [1600, 2000]
        ctrls = ["nc", "vsl:0.4:0.9"]
        run_batch(jobs_for("a_t0", ctrls, cells, seeds, root, {}), root / "batch", a.workers, gate_ok=a.gate_ok)
        by = load(root, "a_t0")
        res = {}
        ok = False
        for q in cells:
            base, arm = by.get(("nc", q), {}), by.get(("vsl:0.4:0.9", q), {})
            ss = sorted(set(base) & set(arm))
            pm = paired_median_diff([base[s]["outflow_ctrl_vph"] for s in ss], [arm[s]["outflow_ctrl_vph"] for s in ss],
                                    seed=7110059)
            rel = pm["median_diff"] / float(np.median([base[s]["outflow_ctrl_vph"] for s in ss]))
            tt = paired_median_diff([base[s]["mean_time_in_system_s"] for s in ss],
                                    [arm[s]["mean_time_in_system_s"] for s in ss], seed=7110059)
            res[q] = {"outflow_rel": round(rel, 4), "outflow_paired": pm, "time_paired": tt,
                      "binds": abs(rel) >= 0.05 and pm["excludes_0"]}
            ok = ok or res[q]["binds"]
        out = {"PASS": ok, "cells": res, "health": health(by)}
    else:
        if a.what == "a_r2":
            seeds, ctrls, envk = list(range(7110120, 7110140)), ctrls_a(), {}
        else:
            seeds, ctrls, envk = list(range(7110140, 7110160)), ctrls_b(), {"av_share": 0.25}
        run_batch(jobs_for(a.what, ctrls, CELLS, seeds, root, envk), root / "batch", a.workers, gate_ok=a.gate_ok)
        by = load(root, a.what)
        t = tune(by, ctrls, CELLS)
        out = {"health": health(by), **t}
        name = {"a_r2": "t1_bn4vsl_baselines_frozen.json", "b_r2": "t1_bn4av25_baselines_frozen.json"}[a.what]
        (REPO_ROOT / "docs" / "lab" / name).write_text(json.dumps(
            {"protocol": "docs/lab/round2_protocol.md", "frozen_at": time.strftime("%Y-%m-%d %H:%M"),
             "tuned": t["tuned"], "env_kwargs": envk, "raw_root": str(root)}, indent=1))
    (root / "analysis.json").write_text(json.dumps(out, indent=1, default=str))
    L = [f"# Round 2 {a.what}: results", "", f"*{time.strftime('%Y-%m-%d %H:%M')} · protocol `docs/lab/round2_protocol.md` · "
         f"raw `{root}` · health {out['health']}*", ""]
    if a.what == "a_t0":
        L.append(f"**Posted VSL binds: {'PASS' if out['PASS'] else 'FAIL'}**")
        for q, r in out["cells"].items():
            L.append(f"- q={q}: outflow {r['outflow_rel']:+.1%} [{r['outflow_paired']['ci_lo']:+.0f}, {r['outflow_paired']['ci_hi']:+.0f}] veh/h; "
                     f"door-to-door {r['time_paired']['median_diff']:+.1f} s [{r['time_paired']['ci_lo']:+.1f}, {r['time_paired']['ci_hi']:+.1f}]")
    else:
        L += ["| controller | q=1200 | q=1600 | q=2000 | q=2400 | score |", "|---|---|---|---|---|---|"]
        for c in sorted(out["table"], key=lambda c: out["table"][c]["score"])[:14]:
            r = out["table"][c]
            L.append(f"| {c} | " + " | ".join(f"{r[q]:.1f}" for q in CELLS) + f" | {r['score']:.1f} |")
        L += ["", f"Tuned (frozen): {json.dumps(out['tuned'])}"]
    (REPO_ROOT / "docs" / "lab" / f"round2_{a.what}.md").write_text("\n".join(L) + "\n")
    ledger.append("T1", "R2" if a.what != "a_t0" else "R1", "S", f"round2_{a.what}", {"protocol": "round2_protocol.md"},
                  "see protocol", sum(len(d) for d in load(root, a.what).values()), out["health"],
                  {k: out[k] for k in ("PASS", "tuned") if k in out}, notes=str(root))
    print(json.dumps({k: out[k] for k in ("PASS", "tuned", "health") if k in out}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
