"""Verify the ring AV safety shield leaves the frozen ring baselines unchanged (R3 addendum B)."""
from __future__ import annotations

import json
import time
from pathlib import Path

from vsl_lab.config import REPO_ROOT, RUNS_ROOT
from vsl_lab.ops import ledger
from vsl_lab.ops.scheduler import Job, run_batch

fz = json.loads((REPO_ROOT / "docs/lab/t3_ring_baselines_frozen.json").read_text())
old_root = Path(fz["raw_root"])
root = RUNS_ROOT / "t3" / f"shield_verify_{int(time.time())}"
specs = [(L, s, c) for L in (220, 260) for s in (7130100, 7130101, 7130102) for c in ("fs5", "pi")]
jobs = []
for L, s, c in specs:
    extra = ["--ctrl", "fs", "--U", "5"] if c == "fs5" else ["--ctrl", "pi", "--vcatch", "1.5", "--window", "20"]
    jobs.append(Job(jid=f"sv_{c}_{L}_{s}", argv=["vsl_lab.jobs.ring_run", "--L", str(L), "--seed", str(s), "--tag", "sv",
                                                 "--out-root", str(root)] + extra))
run_batch(jobs, root / "batch", max_workers=10, gate_ok=True)
new = {}
for p in (root / "sv").glob("*/summary.json"):
    o = json.loads(p.read_text())
    new[(int(o["L_target"]), o["seed"], o["ctrl"])] = o["hash"]
old = {}
for p in (old_root / "r2").glob("*/summary.json"):
    o = json.loads(p.read_text())
    key = (int(o["L_target"]), o["seed"], o["ctrl"])
    if key in new and ((o["ctrl"] == "fs" and o["U"] == 5.0) or (o["ctrl"] == "pi" and o["vcatch"] == 1.5 and o["window"] == 20.0)):
        old[key] = o["hash"]
same = {str(k): (new[k] == old.get(k)) for k in new}
ok = all(same.values()) and len(same) == len(specs)
(REPO_ROOT / "docs/lab/t3_shield_verify.json").write_text(json.dumps({"identical": same, "PASS": ok}, indent=1))
ledger.append("T3", "R3", "S", "ring_shield_verify", {"specs": len(specs)}, "7130100-7130102", len(new), {},
              {"PASS": ok, "n_identical": sum(same.values())}, notes=str(root))
print(json.dumps({"PASS": ok, "identical": sum(same.values()), "n": len(same)}))
