"""Reference controllers on the R3 validation seeds and conditions (same env windows as the DRL validation).

python -m vsl_lab.jobs.val_refs --track t1 --gate-ok   # NC, best constant cap, tuned meter on BN4 validation specs
python -m vsl_lab.jobs.val_refs --track t3 --gate-ok   # NC, tuned FS, per-L best FS (I), tuned PI on ring validation specs
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from vsl_lab.config import N_MAX_DEFAULT, REPO_ROOT, RUNS_ROOT
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

T1_SPECS = [(q, s) for s in (7110300, 7110301) for q in (1600.0, 2000.0, 2400.0)]
T3_SPECS = [(L, s) for s in (7130300, 7130301, 7130302) for L in (230.0, 260.0)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", choices=["t1", "t3"], required=True)
    ap.add_argument("--workers", type=int, default=N_MAX_DEFAULT)
    ap.add_argument("--gate-ok", action="store_true")
    a = ap.parse_args(argv)
    root = RUNS_ROOT / a.track / f"valrefs_{int(time.time())}"
    jobs = []
    if a.track == "t1":
        fz = json.loads((REPO_ROOT / "docs/lab/t1_bn4_baselines_frozen.json").read_text())
        ctrls = sorted({"nc"} | {fz["tuned"][f]["ctrl"] for f in ("cap", "meter", "avfb") if f in fz["tuned"]})
        for q, s in T1_SPECS:
            for c in ctrls:
                jobs.append(Job(jid=f"vr_{c.replace(':', '_')}_{int(q)}_{s}",
                                argv=["vsl_lab.jobs.bn4_eval", "--ctrl", c, "--inflow", str(q), "--seed", str(s),
                                      "--tag", "valrefs", "--out-root", str(root)]))
    else:
        fz = json.loads((REPO_ROOT / "docs/lab/t3_ring_baselines_frozen.json").read_text())
        fs_u = float(fz["tuned"]["fs"]["ctrl"].split(":")[1])
        pi = fz["tuned"]["pi"]["ctrl"].split(":")
        for L, s in T3_SPECS:
            base = ["vsl_lab.jobs.ring_run", "--L", str(L), "--seed", str(s), "--tag", "valrefs", "--out-root", str(root)]
            jobs.append(Job(jid=f"vr_nc_{int(L)}_{s}", argv=base + ["--ctrl", "nc"]))
            jobs.append(Job(jid=f"vr_fs_{int(L)}_{s}", argv=base + ["--ctrl", "fs", "--U", str(fs_u)]))
            per_l = fz["per_L_best_fs"].get(str(int(L))) or fz["per_L_best_fs"].get(int(L))
            if per_l:
                jobs.append(Job(jid=f"vr_fsI_{int(L)}_{s}", argv=base + ["--ctrl", "fs", "--U", per_l.split(":")[1],
                                                                       "--tag", "valrefs_I"]))
            jobs.append(Job(jid=f"vr_pi_{int(L)}_{s}", argv=base + ["--ctrl", "pi", "--vcatch", pi[1], "--window", pi[2]]))
    rep = run_batch(jobs, root / "batch", max_workers=a.workers, gate_ok=a.gate_ok)
    rows = []
    for p in list(root.rglob("*.json")):
        if p.name in ("batch_report.json",):
            continue
        try:
            o = json.loads(p.read_text())
        except Exception:
            continue
        if "job" in o:
            rows.append(o)
    summ = {}
    if a.track == "t1":
        for o in rows:
            summ.setdefault(o["ctrl"], []).append(o["outflow_ctrl_vph"])
        out = {c: {"mean_val_outflow": float(np.mean(v)), "n": len(v)} for c, v in summ.items()}
    else:
        for o in rows:
            k = "nc" if o["ctrl"] == "nc" else (f"fs:{o['U']:g}" + ("(I)" if "valrefs_I" in o["run_id"] or False else "")
                                                if o["ctrl"] == "fs" else f"pi:{o['vcatch']:g}:{o['window']:g}")
            summ.setdefault(k, []).append(o["mean_speed"])
        out = {c: {"mean_val_speed": float(np.mean(v)), "n": len(v)} for c, v in summ.items()}
    (root / "val_refs.json").write_text(json.dumps(out, indent=1))
    dst = REPO_ROOT / "docs" / "lab" / f"{a.track}_val_refs.json"
    dst.write_text(json.dumps({"specs": T1_SPECS if a.track == "t1" else T3_SPECS, "refs": out, "raw": str(root)}, indent=1))
    ledger.append(a.track.upper(), "R3", "S", "val_refs", {"specs": "pilot validation"}, "validation seeds", len(rows),
                  {"PASS": rep.n_ok}, out, notes=str(root))
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
