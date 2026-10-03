"""T4 corridor headroom scan (docs/lab/t4_corr2_protocol.md, Addendum B). python -m vsl_lab.jobs.t4_gscan --gate-ok"""
from __future__ import annotations

import argparse
import json
import time

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

CONDS = {"A": (5000, 300, 2000), "B": (5000, 300, 2500), "C": (5500, 300, 2000), "D": (5000, 600, 2000)}
CTRLS = ["nc"] + [f"alinea:{o}:{k}" for o in (8, 10, 12, 14) for k in (40, 70)]
SEEDS = list(range(7140010, 7140020))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    root = RUNS_ROOT / "t4" / f"gscan_{int(time.time())}"
    jobs = [Job(jid=f"g_{c}_{ctl.replace(':', '_')}_s{s}",
                argv=["vsl_lab.jobs.corr_run", "--ctrl", ctl, "--seed", str(s), "--q-main", str(m), "--q-r1", str(r1),
                      "--q-r2", str(r2), "--stops", "--tag", f"g_{c}", "--out-root", str(root)])
            for c, (m, r1, r2) in CONDS.items() for s in SEEDS for ctl in CTRLS]
    run_batch(jobs, root / "batch", a.workers, gate_ok=a.gate_ok)
    J, tele = {}, {}
    for c in CONDS:
        d = {}
        for p in (root / f"g_{c}").glob("*/summary.json"):
            o = json.loads(p.read_text())
            d.setdefault(o["ctrl"], []).append(o)
            tele[c] = tele.get(c, 0) + o["teleports"]
        J[c] = {k: float(np.median([o["mean_time_in_system_s"] for o in v])) for k, v in d.items()}
    common = [k for k in CTRLS if all(k in J[c] for c in CONDS)]
    mean_c = {k: float(np.mean([J[c][k] for c in CONDS])) for k in common}
    pool = min(mean_c, key=mean_c.get)
    look = float(np.mean([min(J[c][k] for k in common) for c in CONDS]))
    G = (mean_c[pool] - look) / mean_c[pool]
    out = {"J": J, "pooled_best": pool, "J_pool": mean_c[pool], "J_lookup": look, "G": G,
           "per_cond_best": {c: min(common, key=lambda k: J[c][k]) for c in CONDS}, "teleports": tele,
           "DRL_target": bool(G >= 0.10), "raw": str(root)}
    (REPO_ROOT / "docs/lab/t4_gscan.json").write_text(json.dumps(out, indent=1))
    L = ["# T4 corridor headroom scan: results", "", f"*{time.strftime('%Y-%m-%d %H:%M')} · raw `{root}`*", "",
         f"**G = {G:.1%} → {'candidate DRL target' if out['DRL_target'] else 'KILL (G < 10 %)'}** · pooled best `{pool}` · "
         f"per-condition best {out['per_cond_best']}", "", "| controller | " + " | ".join(CONDS) + " |", "|---|" + "---|" * len(CONDS)]
    for k in CTRLS:
        L.append(f"| {k} | " + " | ".join(f"{J[c].get(k, float('nan')):.1f}" for c in CONDS) + " |")
    L += ["", f"Teleports per condition: {tele}"]
    (REPO_ROOT / "docs/lab/t4_gscan.md").write_text("\n".join(L) + "\n")
    ledger.append("T4", "gscan", "S", "t4_gscan", {"conds": CONDS, "ctrls": CTRLS}, "7140010-7140019", len(jobs), {},
                  {"G": round(G, 4), "target": out["DRL_target"]}, notes=str(root))
    print(json.dumps({"G": round(G, 4), "pooled": pool, "per_cond_best": out["per_cond_best"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
