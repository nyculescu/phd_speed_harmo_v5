"""Round 2 D-1: diagnose the MRG3-v2 (IDM) breakdown (teleports, huge door-to-door times). One NC run on the
disclosed throw-away seed 7,120,050 at 5,400/900. Logs teleport reasons, vehicles stopped near the end of the
acceleration lane (merge_0), ramp backlog, and mainline speeds every 60 s. No criteria (diagnosis only).
"""
from __future__ import annotations

import collections
import json
import os
import re
from pathlib import Path

import libsumo as ls

from vsl_lab.config import REPO_ROOT, RUNS_ROOT
from vsl_lab.plants import mrg3 as P
from vsl_lab.sim.runner import SumoSim


def main() -> int:
    seed, mp, rp = 7120050, 5400.0, 900.0
    run_dir = RUNS_ROOT / "t2" / "diag_v2" / f"pid{os.getpid()}"
    run_dir.mkdir(parents=True, exist_ok=True)
    f = P.files()
    dem = P.demand(seed, P.profile(2500.0, mp, 600.0, 1200.0, 3000.0, 3900.0),
                   P.profile(300.0, rp, 600.0, 1200.0, 3000.0, 3900.0), p_noncompliant=0.3, truck_share=0.1, model="idm")
    rou = run_dir / "routes.rou.xml"
    dem.write(rou)
    sim = SumoSim(f["net"], rou, run_dir, dem, additional=[f["add"]], step_length=P.STEP_LENGTH, seed=seed)
    sim.start()
    L0 = f["lanes"]["merge_0"]
    rows = []
    while sim.t < 3900.0 - 1e-9:
        sim.run_until(sim.t + 60.0)
        on_acc = ls.lane.getLastStepVehicleIDs("merge_0")
        stopped_end = sum(1 for v in on_acc if ls.vehicle.getSpeed(v) < 0.5 and ls.vehicle.getLanePosition(v) > L0 - 30)
        rows.append({"t": sim.t, "n_acc_lane": len(on_acc), "stopped_at_acc_end": stopped_end,
                     "ramp_vehicles": ls.edge.getLastStepVehicleNumber("ramp"),
                     "ramp_halting": ls.edge.getLastStepHaltingNumber("ramp"),
                     "pending": len(ls.simulation.getPendingVehicles()),
                     "v_up0b": round(ls.edge.getLastStepMeanSpeed("up0b"), 2),
                     "v_merge_lanes": [round(ls.lane.getLastStepMeanSpeed(f"merge_{i}"), 2) for i in range(4)],
                     "teleports_so_far": sim.tele_start})
    out = sim.close(drained=None)
    reasons = collections.Counter()
    lanes = collections.Counter()
    for line in sim.log_file.read_text(errors="replace").splitlines():
        m = re.search(r"Teleporting vehicle '[^']*'; ([^,]*), lane='([^']*)'", line)
        if m:
            reasons[m.group(1)] += 1
            lanes[m.group(2)] += 1
    res = {"seed": seed, "cell": f"{int(mp)}/{int(rp)}", "teleports": out["teleports"], "teleport_reasons": dict(reasons),
           "teleport_lanes": dict(lanes), "timeline_every_60s": rows[::5], "max_stopped_at_acc_end": max(r["stopped_at_acc_end"] for r in rows),
           "max_ramp_halting": max(r["ramp_halting"] for r in rows), "max_pending": out["max_pending"]}
    (REPO_ROOT / "docs" / "lab" / "t2_mrg3v2_diag.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ("teleports", "teleport_reasons", "teleport_lanes", "max_stopped_at_acc_end",
                                          "max_ramp_halting", "max_pending")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
