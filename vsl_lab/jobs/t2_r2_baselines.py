"""Track 2 / R2 per docs/lab/t2_mrg3_r2_protocol.md (runs only if T2 R1 T1 and T0 passed)."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

SEEDS = list(range(7120100, 7120120))
PNC = [0.1, 0.3, 0.5]
CONST = [0.5, 0.6, 0.7, 0.8, 0.9]
RHO = [14, 17, 20, 23, 26, 29, 32]
GAINS = {"paper": (38, 9, 0.0015), "half": (19, 4.5, 0.00075), "double": (76, 18, 0.003)}


def controllers() -> list:
    out = ["nc"] + [f"const:{b}" for b in CONST]
    for rho in RHO:
        for kp, ki, ki2 in GAINS.values():
            out.append(f"mtfc:{rho}:{kp:g}:{ki:g}:{ki2:g}")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--batch-root", default=None)
    ap.add_argument("--plant", default="v1", choices=["v1", "v2", "v3"])
    a = ap.parse_args(argv)
    global SEEDS
    if a.plant == "v3":
        SEEDS = list(range(7120150, 7120170))   # round2_protocol.md D-2 (never used before; disclosed reassignment)
    suffix = "" if a.plant == "v1" else f"_{a.plant}"
    pat = "r1_[0-9]*/analysis.json" if a.plant == "v1" else f"r1_{a.plant}_[0-9]*/analysis.json"
    r1 = json.loads(Path(sorted((RUNS_ROOT / "t2").glob(pat))[-1]).read_text())
    if not (r1.get("T1", {}).get("PASS") and r1.get("T0", {}).get("PASS")):
        print(json.dumps({"skipped": "T2 R1 T1/T0 did not pass", "r1": {k: r1.get(k, {}).get("PASS") for k in ("T1", "T0")}}))
        return 0
    if a.plant == "v3":   # MRG3-v3 = realism variant H0 (docs/lab/t2_realism_protocol.md): R2 only after an H0 PASS
        vp = REPO_ROOT / "docs" / "lab" / "t2_realism_verdict.json"
        verdict = json.loads(vp.read_text()).get("verdict", {}).get("H0") if vp.exists() else None
        if verdict != "PASS":
            print(json.dumps({"skipped": "realism gate: H0 has no PASS", "H0": verdict}))
            ledger.append("T2", "R2", "S", "mrg3v3_r2", {"gate": "realism"}, "-", 0, {}, {"skipped": f"H0 {verdict}"},
                          notes="blocked by docs/lab/t2_realism_protocol.md")
            return 0
    m, r = (int(x) for x in r1["cell"].split("/"))
    root = Path(a.batch_root) if a.batch_root else RUNS_ROOT / "t2" / f"r2{suffix}_{int(time.time())}"
    if not a.analyse_only:
        jobs = [Job(jid=f"r2_{c.replace(':', '_')}_nc{p}_s{s}",
                    argv=["vsl_lab.jobs.mrg3_run", "--ctrl", c, "--seed", str(s), "--main-peak", str(m), "--ramp-peak", str(r),
                          "--p-nc", str(p), "--tag", "r2", "--out-root", str(root), "--plant", a.plant])
                for p in PNC for s in SEEDS for c in controllers()]
        run_batch(jobs, root / "batch", max_workers=a.workers, gate_ok=a.gate_ok)
    rows = [json.loads(p.read_text()) for p in (root / "r2").glob("*/summary.json")]
    by = {}
    for o in rows:
        by.setdefault((o["ctrl"], float(o["p_noncompliant"])), []).append(o)
    table = {}
    for c in controllers():
        row = {}
        for p in PNC:
            d = by.get((c, p), [])
            if d:
                row[p] = {"median_time_s": float(np.median([o["mean_time_in_system_s"] for o in d])),
                          "median_ramp_s": float(np.median([o["time_ramp_s"] for o in d])), "n": len(d)}
        if row:
            row["score"] = float(np.mean([row[p]["median_time_s"] for p in PNC if p in row]))
            table[c] = row
    nc = table.get("nc", {})
    def ramp_ok(c):
        return all(table[c][p]["median_ramp_s"] <= 1.10 * nc[p]["median_ramp_s"] for p in PNC if p in table[c] and p in nc)
    fams = {"const": [c for c in table if c.startswith("const:")], "mtfc": [c for c in table if c.startswith("mtfc:")]}
    tuned = {"nc": {"ctrl": "nc", "score": nc.get("score")}}
    for f, cs in fams.items():
        if not cs:
            continue
        best = min(cs, key=lambda c: table[c]["score"])
        ok = [c for c in cs if ramp_ok(c)]
        best_ok = min(ok, key=lambda c: table[c]["score"]) if ok else None
        tuned[f] = {"ctrl": best_ok or best, "score": table[best_ok or best]["score"], "unconstrained_best": best,
                    "ramp_constraint_ok": bool(best_ok)}
    per_class = {p: min(fams["mtfc"], key=lambda c: table[c].get(p, {}).get("median_time_s", np.inf)) for p in PNC}
    pooled = tuned["mtfc"]["ctrl"]
    cost_pooled = float(np.mean([table[pooled][p]["median_time_s"] for p in PNC]))
    cost_class = float(np.mean([table[per_class[p]][p]["median_time_s"] for p in PNC]))
    G = (cost_pooled - cost_class) / cost_pooled
    out = {"n_runs": len(rows), "health": {h: sum(o["health"]["status"] == h for o in rows) for h in ("PASS", "WARN", "FAIL")},
           "table": table, "tuned": tuned, "per_class_best_mtfc": per_class, "G": G, "T2_PASS": bool(G >= 0.10)}
    (root / "analysis.json").write_text(json.dumps(out, indent=1, default=str))
    (REPO_ROOT / f"docs/lab/t2_mrg3_baselines_frozen{suffix}.json").write_text(json.dumps(
        {"protocol": "docs/lab/t2_mrg3_r2_protocol.md", "cell": r1["cell"], "tuned": tuned, "per_class_best_mtfc": per_class,
         "G": G, "raw_root": str(root), "frozen_at": time.strftime("%Y-%m-%d %H:%M")}, indent=1))
    L = ["# Track 2 (MRG3), R2 tuned baselines and T2 mechanism", "",
         f"*{time.strftime('%Y-%m-%d %H:%M')} · {len(rows)} runs · health {out['health']} · cell {r1['cell']} · raw `{root}`*", "",
         f"**T2 mechanism (hybrid gate): G = {G:.1%} -> {'PASS' if out['T2_PASS'] else 'FAIL (conservative KILL of MTFC set-point scheduling)'}**", "",
         "| controller | p_nc=0.1 | p_nc=0.3 | p_nc=0.5 | score | ramp ok |", "|---|---|---|---|---|---|"]
    for c in sorted(table, key=lambda c: table[c]["score"])[:15]:
        L.append(f"| {c} | " + " | ".join(f"{table[c][p]['median_time_s']:.1f}" if p in table[c] else "-" for p in PNC) +
                 f" | {table[c]['score']:.1f} | {ramp_ok(c)} |")
    L += ["", f"- Tuned: {json.dumps(tuned)}", f"- Per-class best MTFC (I): {per_class}"]
    (REPO_ROOT / f"docs/lab/t2_mrg3_r2{suffix}.md").write_text("\n".join(L) + "\n")
    ledger.append("T2", "R2", "S", "mrg3_baselines_T2", {"protocol": "t2_mrg3_r2_protocol.md"}, "7120100-7120119", len(rows),
                  out["health"], {"tuned": tuned, "G": G, "T2_PASS": out["T2_PASS"]}, notes=str(root))
    print(json.dumps({"tuned": tuned, "G": G, "T2_PASS": out["T2_PASS"]}, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
